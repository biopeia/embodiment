from __future__ import annotations

from dataclasses import replace
import json

import pytest

from embodiment.physics3d.articulated_spec import (
    ArticulatedBodySpec,
    FixedLinkTopology,
    articulated_body_spec_bytes,
    articulated_body_spec_sha256,
    build_articulated_urdf,
    restore_articulated_body_spec,
)
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec, SurfaceMaterial


def _spec() -> ArticulatedBodySpec:
    joint = JointSpec("hinge", (0.0, 1.0, 0.0), -1.0, 1.0, 4.0, 0.1, 2.0)
    return ArticulatedBodySpec(
        body_kind="test-body",
        state_schema_version=1,
        spawn_height=0.5,
        base_link_name="base",
        joint_specs=(joint,),
        joint_topology=(JointTopology("hinge", "base", "arm", (0.0, 0.0, 0.2)),),
        segments={
            "base": SegmentSpec(1.0, (0.2, 0.2, 0.1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
            "arm": SegmentSpec(0.5, (0.1, 0.1, 0.4), (0, 0, 0.2), (0.2, 0.3, 0.4, 1)),
        },
        contact_link_names=("arm",),
        structural_neighbour_names=(("base", "arm"),),
        fixed_link_topology=(FixedLinkTopology("arm", "foot", (0, 0, -0.1)),),
    )


def test_spec_exposes_opaque_ordinal_channels() -> None:
    spec = _spec()

    assert spec.motor_dof == 1
    assert spec.effector_ids() == ("eff.0", "eff.1")
    assert spec.interoceptive_receptor_ids() == tuple(
        f"rec.{i}" for i in range(spec.physical_receptor_count, spec.total_receptor_count)
    )
    assert all(name.startswith("rec.") for name in spec.receptor_ids())


def test_urdf_generation_is_deterministic_and_contains_morphology() -> None:
    first = build_articulated_urdf(_spec())
    second = build_articulated_urdf(_spec())

    assert first == second
    assert '<robot name="body_test_body">' in first
    assert first.count('type="revolute"') == 1
    assert 'name="foot_fixed" type="fixed"' in first
    assert '<child link="foot"/>' in first
    assert "symbiont_" not in first


def test_urdf_rejects_mismatched_joint_spec_and_topology() -> None:
    spec = _spec()
    invalid = replace(spec, joint_topology=())

    with pytest.raises(ValueError, match="length mismatch"):
        build_articulated_urdf(invalid)


def test_complete_morphology_checkpoint_encoding_is_deterministic_and_roundtrips() -> None:
    spec = _spec()
    encoded = articulated_body_spec_bytes(spec)
    restored = restore_articulated_body_spec(json.loads(encoded))

    assert restored == spec
    assert articulated_body_spec_bytes(restored) == encoded
    assert articulated_body_spec_sha256(restored) == articulated_body_spec_sha256(spec)


@pytest.mark.parametrize(
    "change",
    [
        {"contact_link_names": ("base",)},
        {"fixed_base": True},
        {"spawn_height": 0.75},
        {"state_schema_version": 2},
        {"structural_neighbour_names": (("base", "arm"), ("arm", "foot"))},
        {"body_material": SurfaceMaterial(0.7, 0.02, 0.002, 0.02, 0.03, 0.05)},
    ],
)
def test_full_morphology_fingerprint_covers_non_urdf_body_contracts(change) -> None:
    original = _spec()
    changed = replace(original, **change)

    assert build_articulated_urdf(changed) == build_articulated_urdf(original)
    assert articulated_body_spec_sha256(changed) != articulated_body_spec_sha256(original)


def test_full_morphology_fingerprint_distinguishes_sub_urdf_precision_mass_changes() -> None:
    original = _spec()
    segments = dict(original.segments)
    segments["base"] = replace(segments["base"], mass=1.00000000001)
    changed = replace(original, segments=segments)

    assert build_articulated_urdf(changed) == build_articulated_urdf(original)
    assert articulated_body_spec_sha256(changed) != articulated_body_spec_sha256(original)


def test_spec_restore_rejects_unknown_fields_and_non_finite_values() -> None:
    payload = json.loads(articulated_body_spec_bytes(_spec()))
    payload["unknown"] = "not accepted"
    with pytest.raises(ValueError, match="schema or fields"):
        restore_articulated_body_spec(payload)
    payload = json.loads(articulated_body_spec_bytes(_spec()))
    payload["spawn_height"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        restore_articulated_body_spec(payload)


def test_spec_restore_rejects_segment_identity_collisions_after_normalization() -> None:
    payload = json.loads(articulated_body_spec_bytes(_spec()))
    segment_name, segment = next(iter(payload["segments"].items()))
    payload["segments"][f" {segment_name} "] = segment

    with pytest.raises(ValueError, match="collide after normalization"):
        restore_articulated_body_spec(payload)
