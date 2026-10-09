from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec
from embodiment.physics3d.physical_projection import project_body_physical_input
from embodiment.physics3d.physical_transition import PhysicalStepCorrelation


def _spec() -> ArticulatedBodySpec:
    joint = JointSpec("hinge", (0.0, 1.0, 0.0), -1.0, 1.0, 4.0, 0.1, 2.0)
    return ArticulatedBodySpec(
        body_kind="test-body",
        state_schema_version=1,
        spawn_height=0.5,
        base_link_name="base",
        joint_specs=(joint,),
        joint_topology=(JointTopology("hinge", "base", "foot", (0.0, 0.0, 0.2)),),
        segments={
            "base": SegmentSpec(1.0, (0.2, 0.2, 0.1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
            "foot": SegmentSpec(0.5, (0.1, 0.1, 0.4), (0, 0, 0.2), (0.2, 0.3, 0.4, 1)),
        },
        contact_link_names=("foot",),
        structural_neighbour_names=(("base", "foot"),),
    )


def _pose() -> BodyPoseSample:
    return BodyPoseSample(
        body_id="body.7",
        reference_frame="physics3d.world",
        body_frame="body.root",
        position_m=(1.0, 2.0, 3.0),
        orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
        sample_kind="physics_step",
        sample_value=3,
    )


def _correlation() -> PhysicalStepCorrelation:
    return PhysicalStepCorrelation(
        world_id="world.1",
        causal_tick=2,
        physical_step_id="step.3",
        body_id="body.7",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.4",
        environment_revision="environment.5",
        solver_config_revision="solver.6",
    )


def test_projection_snapshots_pose_morphology_and_contact_links() -> None:
    projected = project_body_physical_input(_spec(), _pose(), correlation=_correlation())

    assert projected.body_id == "body.7"
    assert projected.correlation == _correlation()
    assert projected.body_kind == "test-body"
    assert projected.reference_frame == "physics3d.world"
    assert projected.body_frame == "body.root"
    assert projected.position_m == (1.0, 2.0, 3.0)
    assert projected.orientation_xyzw == (0.0, 0.0, 0.0, 1.0)
    assert projected.contact_link_names == ("foot",)
    assert '<mass value="1"/>' in projected.articulated_description
    assert '<mass value="0.5"/>' in projected.articulated_description
    assert '<geometry><box size="0.1 0.1 0.4"/></geometry>' in projected.articulated_description


def test_projection_is_immutable_and_does_not_mutate_owner_inputs() -> None:
    spec = _spec()
    pose = _pose()
    spec_before = dict(spec.segments)
    projected = project_body_physical_input(spec, pose, correlation=_correlation())

    with pytest.raises(FrozenInstanceError):
        projected.body_id = "body.other"  # type: ignore[misc]

    assert spec.segments == spec_before
    assert pose.position_m == (1.0, 2.0, 3.0)


def test_projection_captures_description_instead_of_live_mutable_spec_mapping() -> None:
    spec = _spec()
    projected = project_body_physical_input(spec, _pose(), correlation=_correlation())
    original = projected.articulated_description

    spec.segments.clear()

    assert projected.articulated_description == original
