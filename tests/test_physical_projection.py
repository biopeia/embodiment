from dataclasses import FrozenInstanceError, replace

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.articulated_state import (
    ActiveArticulatedMorphology,
    ArticulatedEmbodimentPhysicalState,
    JointKinematicState,
)
from embodiment.physics3d.mechanics import (
    JointSpec,
    JointTopology,
    SegmentSpec,
    SurfaceMaterial,
)
from embodiment.physics3d.physical_projection import (
    BodyPhysicalInput,
    project_body_physical_input,
)
from embodiment.physics3d.physical_transition import (
    EmbodimentPhysicalState,
    PhysicalStepCorrelation,
)


def _spec() -> ArticulatedBodySpec:
    joint = JointSpec("joint.elbow", (0.0, 1.0, 0.0), -1.0, 1.0, 4.0, 0.1, 2.0)
    return ArticulatedBodySpec(
        body_kind="test-body",
        state_schema_version=1,
        spawn_height=0.5,
        base_link_name="body.root",
        joint_specs=(joint,),
        joint_topology=(JointTopology("joint.elbow", "body.root", "body.arm", (0.0, 0.0, 0.2)),),
        segments={
            "body.root": SegmentSpec(1.0, (0.2, 0.2, 0.1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
            "body.arm": SegmentSpec(0.5, (0.1, 0.1, 0.4), (0, 0, 0.2), (0.2, 0.3, 0.4, 1)),
        },
        contact_link_names=("body.arm",),
        structural_neighbour_names=(("body.root", "body.arm"),),
        body_material=SurfaceMaterial(0.8, 0.02, 0.002, 0.02, 0.03, 0.05),
        fixed_base=True,
    )


def _correlation(**changes: object) -> PhysicalStepCorrelation:
    values: dict[str, object] = {
        "world_id": "world.1",
        "causal_tick": 2,
        "physical_step_id": "step.3",
        "body_id": "body.7",
        "embodiment_episode_id": "episode.2",
        "morphology_revision": "morph.4",
        "environment_revision": "environment.5",
        "solver_config_revision": "solver.6",
    }
    values.update(changes)
    return PhysicalStepCorrelation(**values)  # type: ignore[arg-type]


def _state() -> ArticulatedEmbodimentPhysicalState:
    spec = _spec()
    morphology = ActiveArticulatedMorphology.from_spec(
        body_id="body.7",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.4",
        spec=spec,
    )
    root = EmbodimentPhysicalState(
        world_id="world.1",
        causal_tick=2,
        body_id="body.7",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.4",
        pose=BodyPoseSample(
            body_id="body.7",
            reference_frame="world.frame",
            body_frame="body.root",
            position_m=(1.0, 2.0, 3.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value=2,
        ),
        linear_velocity_m_per_s=(1.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.5),
    )
    return ArticulatedEmbodimentPhysicalState(
        root=root,
        morphology=morphology,
        joints=(JointKinematicState("joint.elbow", 0.25, -0.5),),
    )


def test_projection_snapshots_complete_owner_state_by_stable_joint_identity() -> None:
    state = _state()
    projected = project_body_physical_input(state, correlation=_correlation())

    assert projected.body_id == "body.7"
    assert projected.correlation == _correlation()
    assert projected.morphology_revision == "morph.4"
    assert projected.morphology_sha256 == state.morphology.morphology_sha256
    assert projected.body_kind == "test-body"
    assert projected.reference_frame == "world.frame"
    assert projected.body_frame == "body.root"
    assert projected.position_m == (1.0, 2.0, 3.0)
    assert projected.orientation_xyzw == (0.0, 0.0, 0.0, 1.0)
    assert projected.linear_velocity_m_per_s == (1.0, 0.0, 0.0)
    assert projected.angular_velocity_rad_per_s == (0.0, 0.0, 0.5)
    assert projected.joints == (JointKinematicState("joint.elbow", 0.25, -0.5),)
    assert projected.joint_position_unit == "rad"
    assert projected.joint_velocity_unit == "rad/s"
    assert projected.contact_link_names == ("body.arm",)
    assert projected.body_material == state.morphology.spec.body_material
    assert projected.fixed_base is True
    assert '<mass value="1"/>' in projected.articulated_description
    assert '<mass value="0.5"/>' in projected.articulated_description
    assert '<geometry><box size="0.1 0.1 0.4"/></geometry>' in projected.articulated_description


def test_projection_does_not_mutate_or_retain_mutable_morphology_mapping() -> None:
    state = _state()
    projected = project_body_physical_input(state, correlation=_correlation())
    original_description = projected.articulated_description

    with pytest.raises(FrozenInstanceError):
        projected.body_id = "body.other"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        state.morphology.spec.segments.clear()
    assert projected.articulated_description == original_description
    assert projected.joints == state.joints


@pytest.mark.parametrize(
    "changes",
    [
        {"world_id": "world.other"},
        {"causal_tick": 3},
        {"body_id": "body.other"},
        {"embodiment_episode_id": "episode.other"},
        {"morphology_revision": "morph.other"},
    ],
)
def test_projection_rejects_correlation_not_bound_to_source_state(changes) -> None:
    with pytest.raises(ValueError, match="does not match the source Embodiment state"):
        project_body_physical_input(_state(), correlation=_correlation(**changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"linear_velocity_m_per_s": (0.0, float("inf"), 0.0)},
        {"position_m": (0.0, float("nan"), 0.0)},
        {"orientation_xyzw": (0.0, 0.0, 0.0, 2.0)},
        {"joint_position_unit": "degree"},
        {"fixed_base": 1},
    ],
)
def test_physical_input_rejects_invalid_values_even_when_built_directly(changes) -> None:
    projected = project_body_physical_input(_state(), correlation=_correlation())
    with pytest.raises(ValueError):
        replace(projected, **changes)


def test_direct_input_rejects_duplicate_or_positional_joint_channels() -> None:
    projected = project_body_physical_input(_state(), correlation=_correlation())
    with pytest.raises(ValueError, match="unique, stable sorted identities"):
        replace(
            projected,
            joints=(
                JointKinematicState("joint.elbow", 0.1, 0.2),
                JointKinematicState("joint.elbow", 0.3, 0.4),
            ),
        )


@pytest.mark.parametrize(
    "changes, message",
    [
        (
            {"joints": (JointKinematicState("joint.elbow", 1.01, 0.0),)},
            "outside projected range",
        ),
        (
            {"joints": (JointKinematicState("joint.elbow", 0.5, 4.01),)},
            "exceeds projected limit",
        ),
        ({"joint_ranges": ()}, "exactly match active morphology"),
        ({"morphology_sha256": "not-a-digest"}, "lowercase SHA-256 digest"),
    ],
)
def test_direct_input_cannot_bypass_active_morphology_constraints(changes, message) -> None:
    projected = project_body_physical_input(_state(), correlation=_correlation())

    with pytest.raises(ValueError, match=message):
        replace(projected, **changes)
