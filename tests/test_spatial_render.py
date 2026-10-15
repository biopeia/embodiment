from __future__ import annotations

from dataclasses import replace

import pytest

from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec
from embodiment.physics3d.spatial_render import (
    CONTRACT_REVISION,
    RenderMorphologyProjection,
    RenderSegment,
    _render_digest,
)


def _spec() -> ArticulatedBodySpec:
    return ArticulatedBodySpec(
        body_kind="test-body",
        state_schema_version=1,
        spawn_height=0.5,
        base_link_name="body.base",
        joint_specs=(JointSpec("joint.hinge", (0.0, 0.0, 1.0), -1.0, 1.0, 2.0, 0.1, 3.0),),
        joint_topology=(
            JointTopology("joint.hinge", "body.base", "body.arm", (0.0, 0.0, 0.2)),
        ),
        segments={
            "body.base": SegmentSpec(1.0, (0.2, 0.1, 0.1), (0.0, 0.0, 0.0), (0.1, 0.2, 0.3, 1.0)),
            "body.arm": SegmentSpec(0.5, (0.1, 0.1, 0.4), (0.0, 0.0, 0.2), (0.3, 0.2, 0.1, 1.0)),
        },
        contact_link_names=("body.arm",),
        structural_neighbour_names=(("body.base", "body.arm"),),
    )


def _active(spec: ArticulatedBodySpec | None = None) -> ActiveArticulatedMorphology:
    return ActiveArticulatedMorphology.from_spec(
        body_id="body.test",
        embodiment_episode_id="episode.test",
        morphology_revision="morphology-r1",
        spec=spec or _spec(),
    )


def _projection(spec: ArticulatedBodySpec | None = None) -> RenderMorphologyProjection:
    return RenderMorphologyProjection.from_active_morphology(
        _active(spec), geometry_revision="render-r1"
    )


def test_static_projection_contains_only_approved_render_fields() -> None:
    projection = _projection()
    payload = projection.to_payload()

    assert payload["contract_revision"] == CONTRACT_REVISION
    assert payload["body_id"] == "body.test"
    assert payload["embodiment_episode_id"] == "episode.test"
    assert payload["morphology_revision"] == "morphology-r1"
    assert payload["geometry_revision"] == "render-r1"
    assert [item["segment_id"] for item in payload["segments"]] == ["body.arm", "body.base"]
    assert payload["segments"][1]["shape"] == "box"
    assert payload["segments"][1]["dimensions_m"] == [0.2, 0.1, 0.1]
    assert payload["segments"][1]["visual_origin_in_link_m"] == [0.0, 0.0, 0.0]
    assert payload["joints"] == [
        {
            "joint_id": "joint.hinge",
            "parent_link_id": "body.base",
            "child_link_id": "body.arm",
            "joint_type": "revolute",
            "joint_origin_in_parent_m": [0.0, 0.0, 0.2],
            "axis_in_joint_frame": [0.0, 0.0, 1.0],
        }
    ]
    serialized = projection.canonical_bytes().decode("utf-8")
    for excluded in ("mass", "color", "torque", "velocity", "contact", "receptor", "effector"):
        assert excluded not in serialized
    assert len(projection.canonical_bytes()) <= 256 * 1024


def test_static_projection_digest_changes_only_for_render_subset() -> None:
    original = _projection()
    source = _spec()
    segments = dict(source.segments)
    segments["body.base"] = replace(segments["body.base"], mass=7.0, color=(1.0, 0.0, 1.0, 1.0))
    non_render_change = _projection(replace(source, segments=segments))
    segments["body.base"] = replace(segments["body.base"], size=(0.3, 0.1, 0.1))
    render_change = _projection(replace(source, segments=segments))

    assert non_render_change.render_geometry_sha256 == original.render_geometry_sha256
    assert render_change.render_geometry_sha256 != original.render_geometry_sha256


def test_payload_roundtrip_is_deterministic_and_closed() -> None:
    projection = _projection()
    restored = RenderMorphologyProjection.from_payload(projection.to_payload())

    assert restored == projection
    assert restored.canonical_bytes() == projection.canonical_bytes()
    payload = projection.to_payload()
    payload["unexpected"] = "reject"
    with pytest.raises(ValueError, match="descriptor fields"):
        RenderMorphologyProjection.from_payload(payload)


def test_payload_rejects_digest_tampering() -> None:
    payload = _projection().to_payload()
    payload["render_geometry_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not match"):
        RenderMorphologyProjection.from_payload(payload)

@pytest.mark.parametrize(
    "dimensions",
    [(-1.0, 1.0, 1.0), (0.0, 1.0, 1.0), (float("nan"), 1.0, 1.0), (float("inf"), 1.0, 1.0)],
)
def test_segment_rejects_invalid_dimensions(dimensions) -> None:
    with pytest.raises(ValueError):
        RenderSegment("body.part", dimensions, (0.0, 0.0, 0.0))


def test_projection_rejects_non_unit_source_joint_axis_without_rewriting_it() -> None:
    source = _spec()
    invalid = replace(source, joint_specs=(replace(source.joint_specs[0], axis=(0.0, 0.0, 2.0)),))

    with pytest.raises(ValueError, match="already be normalized"):
        _projection(invalid)


def test_projection_rejects_undeclared_topology_references() -> None:
    source = _spec()
    invalid = replace(
        source,
        joint_topology=(JointTopology("joint.hinge", "missing", "body.arm", (0.0, 0.0, 0.0)),),
    )

    with pytest.raises(ValueError, match="undeclared morphology link"):
        _projection(invalid)


def test_projection_allows_topology_link_without_authored_geometry() -> None:
    source = _spec()
    segments = dict(source.segments)
    del segments["body.arm"]
    projection = _projection(replace(source, segments=segments))

    assert [item.segment_id for item in projection.segments] == ["body.base"]
    assert projection.joints[0].child_link_id == "body.arm"


def test_candidate_digest_vector_matches_rfc8785_bytes() -> None:
    # This is the contract's illustrative descriptor vector. It is not evidence
    # of production morphology publication or World-cut association.
    segment = RenderSegment("body.root", (0.2, 0.1, 0.1), (0.0, 0.0, 0.0))
    content = {
        "contract_revision": CONTRACT_REVISION,
        "schema_version": 1,
        "coordinate_system": "right_handed_z_up",
        "length_unit": "m",
        "segments": [segment.to_payload()],
        "joints": [],
    }
    expected = "62a6a5dc9be0d29cabfbd1d5c55079988dd7e6f85b6f14816d15ebae8ef0c234"
    assert _render_digest(content) == expected
    projection = RenderMorphologyProjection.from_payload(
        {
            "contract_revision": CONTRACT_REVISION,
            "schema_version": 1,
            "body_id": "body.test",
            "embodiment_episode_id": "episode.test",
            "morphology_revision": "morphology-r1",
            "geometry_revision": "render-r1",
            "render_geometry_sha256": expected,
            "coordinate_system": "right_handed_z_up",
            "length_unit": "m",
            "segments": [segment.to_payload()],
            "joints": [],
        }
    )
    assert projection.render_geometry_sha256 == expected
