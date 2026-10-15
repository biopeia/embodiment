from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec
from embodiment.physics3d.spatial_render import (
    CONTRACT_REVISION,
    RenderDynamicPoseCandidate,
    RenderLinkPose,
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


def _pose_candidate(**overrides) -> RenderDynamicPoseCandidate:
    projection = _projection()
    context = SimpleNamespace(
        world_id=overrides.pop("source_world_id", "world.test"),
        physical_step_id=overrides.pop("physical_step_id", "step.1"),
        environment_revision=overrides.pop("environment_revision", "environment-r1"),
        solver_config_revision=overrides.pop("solver_config_revision", "solver-r1"),
        source_causal_tick=overrides.pop("source_causal_tick", 0),
        target_causal_tick=overrides.pop("target_causal_tick", 1),
        body_id=overrides.pop("body_id", projection.body_id),
        embodiment_episode_id=overrides.pop("embodiment_episode_id", projection.embodiment_episode_id),
        morphology_revision=overrides.pop("morphology_revision", projection.morphology_revision),
    )
    return projection.validate_dynamic_pose_candidate(
        world_context=context,
        poses=(
            RenderLinkPose("body.arm", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RenderLinkPose("body.base", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ),
        **overrides,
    )


def test_dynamic_pose_candidate_binds_complete_authentic_sample_to_static_identity() -> None:
    static = _projection()
    candidate = _pose_candidate()
    payload = candidate.to_payload()

    assert candidate.body_id == static.body_id
    assert candidate.embodiment_episode_id == static.embodiment_episode_id
    assert candidate.morphology_revision == static.morphology_revision
    assert candidate.geometry_revision == static.geometry_revision
    assert candidate.render_geometry_sha256 == static.render_geometry_sha256
    assert [pose["segment_id"] for pose in payload["poses"]] == ["body.arm", "body.base"]
    assert payload["completeness"] == "complete"
    assert payload["reference_frame"] == "physics3d.world"
    assert payload["coordinate_system"] == "right_handed_z_up"
    assert payload["length_unit"] == "m"
    assert payload["poses"][0] == {
        "segment_id": "body.arm",
        "translation_m": [1.0, 0.0, 0.0],
        "orientation_xyzw": [0.0, 0.0, 0.0, 1.0],
    }
    assert len(candidate.canonical_bytes()) <= 256 * 1024


@pytest.mark.parametrize(
    "poses",
    [
        (),
        (RenderLinkPose("body.arm", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),),
        (
            RenderLinkPose("body.arm", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RenderLinkPose("body.base", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
            RenderLinkPose("extra", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ),
    ],
)
def test_dynamic_pose_candidate_rejects_missing_or_extra_ids(poses) -> None:
    with pytest.raises(ValueError, match="exactly match"):
        _projection().validate_dynamic_pose_candidate(
            world_context=SimpleNamespace(
                world_id="world.test", physical_step_id="step.1",
                environment_revision="environment-r1", solver_config_revision="solver-r1",
                source_causal_tick=0, target_causal_tick=1,
                body_id="body.test", embodiment_episode_id="episode.test",
                morphology_revision="morphology-r1",
            ),
            poses=poses,
        )


def test_dynamic_pose_candidate_rejects_duplicate_ids() -> None:
    pose = RenderLinkPose("body.arm", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="exactly match"):
        _projection().validate_dynamic_pose_candidate(
            world_context=SimpleNamespace(
                world_id="world.test", physical_step_id="step.1",
                environment_revision="environment-r1", solver_config_revision="solver-r1",
                source_causal_tick=0, target_causal_tick=1,
                body_id="body.test", embodiment_episode_id="episode.test",
                morphology_revision="morphology-r1",
            ),
            poses=(pose, pose),
        )


def test_dynamic_pose_candidate_rejects_mismatched_static_identity_or_revision() -> None:
    static = _projection()
    candidate = _pose_candidate()
    for changed in (
        replace(candidate, body_id="body.other"),
        replace(candidate, embodiment_episode_id="episode.other"),
        replace(candidate, morphology_revision="morphology-r2"),
        replace(candidate, geometry_revision="render-r2"),
        replace(candidate, render_geometry_sha256="0" * 64),
    ):
        with pytest.raises(ValueError, match="identity/revision"):
            static.validate_dynamic_pose_candidate_binding(changed)


def test_dynamic_pose_candidate_rejects_non_adjacent_step_context() -> None:
    with pytest.raises(ValueError, match="adjacent"):
        _projection().validate_dynamic_pose_candidate(
            world_context=SimpleNamespace(
                world_id="world.test", physical_step_id="step.1",
                environment_revision="environment-r1", solver_config_revision="solver-r1",
                source_causal_tick=1, target_causal_tick=3,
                body_id="body.test", embodiment_episode_id="episode.test",
                morphology_revision="morphology-r1",
            ),
            poses=(RenderLinkPose("body.arm", (1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
                   RenderLinkPose("body.base", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))),
        )


def test_dynamic_pose_candidate_rejects_world_context_from_other_morphology() -> None:
    with pytest.raises(ValueError, match="World step context identity"):
        _pose_candidate(morphology_revision="morphology-r2")


@pytest.mark.parametrize(
    "translation,orientation",
    [
        ((float("nan"), 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),
        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 2.0)),
    ],
)
def test_render_link_pose_rejects_nonfinite_translation_or_nonunit_quaternion(translation, orientation) -> None:
    with pytest.raises(ValueError):
        RenderLinkPose("body.base", translation, orientation)


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
