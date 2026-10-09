from __future__ import annotations

from dataclasses import replace

import pytest

from embodiment.physics3d.articulated_spec import (
    ArticulatedBodySpec,
    FixedLinkTopology,
    build_articulated_urdf,
)
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec


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
