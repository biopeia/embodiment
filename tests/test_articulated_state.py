from dataclasses import replace
import json

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_state import (
    ActiveArticulatedMorphology,
    ArticulatedEmbodimentPhysicalState,
    JointKinematicState,
    SolverArticulatedCandidate,
)
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec
from embodiment.physics3d.physical_transition import (
    EmbodimentPhysicalState,
    PhysicalStepCorrelation,
    SolverBodyCandidate,
)


def _correlation(**changes: object) -> PhysicalStepCorrelation:
    values: dict[str, object] = {
        "world_id": "world.1",
        "causal_tick": 4,
        "physical_step_id": "step.5",
        "body_id": "body.1",
        "embodiment_episode_id": "episode.2",
        "morphology_revision": "morph.3",
        "environment_revision": "environment.6",
        "solver_config_revision": "solver.7",
    }
    values.update(changes)
    return PhysicalStepCorrelation(**values)  # type: ignore[arg-type]


def _root() -> EmbodimentPhysicalState:
    return EmbodimentPhysicalState(
        world_id="world.1",
        causal_tick=4,
        body_id="body.1",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.3",
        pose=BodyPoseSample(
            body_id="body.1",
            reference_frame="physics3d.world",
            body_frame="body.root",
            position_m=(0.0, 0.0, 1.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value=4,
        ),
        linear_velocity_m_per_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )


def _morphology(revision: str = "morph.3") -> ActiveArticulatedMorphology:
    spec = ArticulatedBodySpec(
        body_kind="two-link-fixture",
        state_schema_version=1,
        spawn_height=0.0,
        base_link_name="body.root",
        joint_specs=(
            JointSpec("joint.hip", (0.0, 1.0, 0.0), -0.8, 0.8, 10.0, 0.1, 2.0),
            JointSpec("joint.elbow", (0.0, 1.0, 0.0), -1.2, 1.2, 8.0, 0.1, 2.0),
        ),
        joint_topology=(
            JointTopology("joint.hip", "body.root", "body.thigh", (0.0, 0.0, -0.2)),
            JointTopology("joint.elbow", "body.thigh", "body.forearm", (0.0, 0.0, -0.4)),
        ),
        segments={
            "body.root": SegmentSpec(1.0, (0.2, 0.2, 0.2), (0.0, 0.0, 0.0), (0.5, 0.5, 0.5, 1.0)),
            "body.thigh": SegmentSpec(0.3, (0.1, 0.4, 0.1), (0.0, 0.0, -0.2), (0.5, 0.5, 0.5, 1.0)),
            "body.forearm": SegmentSpec(0.2, (0.1, 0.3, 0.1), (0.0, 0.0, -0.15), (0.5, 0.5, 0.5, 1.0)),
        },
        contact_link_names=("body.root", "body.forearm"),
        structural_neighbour_names=(("body.root", "body.thigh"), ("body.thigh", "body.forearm")),
    )
    return ActiveArticulatedMorphology.from_spec(
        body_id="body.1",
        embodiment_episode_id="episode.2",
        morphology_revision=revision,
        spec=spec,
    )


def _state(morphology: ActiveArticulatedMorphology | None = None) -> ArticulatedEmbodimentPhysicalState:
    return ArticulatedEmbodimentPhysicalState(
        root=_root(),
        morphology=morphology or _morphology(),
        joints=(JointKinematicState("joint.hip", 0.1, 0.0), JointKinematicState("joint.elbow", -0.2, 0.0)),
    )


def _candidate(joints: tuple[JointKinematicState, ...] | None = None) -> SolverArticulatedCandidate:
    return SolverArticulatedCandidate(
        root=SolverBodyCandidate(
            correlation=_correlation(),
            reference_frame="physics3d.world",
            body_frame="body.root",
            position_m=(0.0, 0.0, 0.9),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            linear_velocity_m_per_s=(0.0, 0.0, -1.0),
            angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
        ),
        joints=joints if joints is not None else (
            JointKinematicState("joint.elbow", 0.4, 0.2),
            JointKinematicState("joint.hip", -0.3, -0.1),
        ),
    )


def test_adopts_joint_values_by_stable_identity_not_collection_position() -> None:
    state = _state()
    step = _correlation()
    adopted = state.adopt_candidate(_candidate(), expected_step=step)

    assert [(item.joint_id, item.position_rad) for item in adopted.joints] == [
        ("joint.elbow", 0.4),
        ("joint.hip", -0.3),
    ]
    permuted = state.adopt_candidate(
        _candidate(tuple(reversed(_candidate().joints))), expected_step=step
    )
    assert permuted == adopted
    assert state.causal_tick == 4
    assert adopted.causal_tick == 5
    assert adopted.root.last_physical_step == step


@pytest.mark.parametrize(
    "joints",
    [
        (JointKinematicState("joint.hip", 0.0, 0.0),),
        (
            JointKinematicState("joint.hip", 0.0, 0.0),
            JointKinematicState("joint.hip", 0.0, 0.0),
        ),
        (
            JointKinematicState("joint.hip", 0.0, 0.0),
            JointKinematicState("joint.other", 0.0, 0.0),
        ),
        (
            JointKinematicState("joint.hip", 0.0, 0.0),
            JointKinematicState("joint.elbow", 1.3, 0.0),
        ),
        (
            JointKinematicState("joint.hip", 0.0, 10.1),
            JointKinematicState("joint.elbow", 0.0, 0.0),
        ),
    ],
)
def test_rejects_incomplete_duplicate_unknown_or_out_of_range_joint_results(joints) -> None:
    state = _state()
    original_root = state.root
    with pytest.raises(ValueError):
        state.adopt_candidate(_candidate(joints), expected_step=_correlation())
    assert state.root is original_root
    assert state.causal_tick == 4


def test_rejects_stale_morphology_even_when_joint_names_match() -> None:
    state = _state()
    stale = replace(_correlation(), morphology_revision="morph.old")
    candidate = _candidate()
    with pytest.raises(ValueError, match="authorized physical step"):
        state.adopt_candidate(
            SolverArticulatedCandidate(
                replace(candidate.root, correlation=stale), candidate.joints
            ),
            expected_step=_correlation(),
        )
    assert state.causal_tick == 4


def test_articulated_checkpoint_is_deterministic_and_restores_exact_state() -> None:
    state = _state().adopt_candidate(_candidate(), expected_step=_correlation())
    encoded = state.checkpoint_bytes()
    restored = ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        encoded, active_morphology=state.morphology
    )
    assert restored == state
    assert restored.checkpoint_bytes() == encoded
    payload = json.loads(encoded)
    assert payload["schema_version"] == 1
    assert payload["position_unit"] == "rad"
    assert payload["velocity_unit"] == "rad/s"


def test_restored_articulated_state_can_continue_on_the_next_causal_step() -> None:
    first = _state().adopt_candidate(_candidate(), expected_step=_correlation())
    resumed = ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        first.checkpoint_bytes(), active_morphology=first.morphology
    )
    second_step = _correlation(causal_tick=5, physical_step_id="step.6")
    second_candidate = SolverArticulatedCandidate(
        root=SolverBodyCandidate(
            correlation=second_step,
            reference_frame="physics3d.world",
            body_frame="body.root",
            position_m=(0.0, 0.0, 0.8),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            linear_velocity_m_per_s=(0.0, 0.0, -1.0),
            angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
        ),
        joints=(
            JointKinematicState("joint.hip", -0.4, -0.2),
            JointKinematicState("joint.elbow", 0.5, 0.3),
        ),
    )

    second = resumed.adopt_candidate(second_candidate, expected_step=second_step)

    assert first.causal_tick == 5
    assert second.causal_tick == 6
    assert second.root.last_physical_step == second_step
    assert [(item.joint_id, item.position_rad) for item in second.joints] == [
        ("joint.elbow", 0.5),
        ("joint.hip", -0.4),
    ]
    assert ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        second.checkpoint_bytes(), active_morphology=second.morphology
    ) == second


def test_articulated_checkpoint_rejects_unknown_schema_and_implicit_units() -> None:
    state = _state()
    payload = json.loads(state.checkpoint_bytes())
    payload["schema_version"] = 2
    with pytest.raises(ValueError, match="unsupported"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload).encode(), active_morphology=state.morphology
        )
    payload = json.loads(state.checkpoint_bytes())
    payload["schema_version"] = True
    with pytest.raises(ValueError, match="unsupported"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload).encode(), active_morphology=state.morphology
        )
    payload = json.loads(state.checkpoint_bytes())
    payload["position_unit"] = ""
    with pytest.raises(ValueError, match="unsupported"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload).encode(), active_morphology=state.morphology
        )


def test_state_and_checkpoint_must_match_active_morphology_descriptor() -> None:
    with pytest.raises(ValueError, match="active descriptor"):
        ArticulatedEmbodimentPhysicalState(
            root=_root(), morphology=_morphology("morph.old"),
            joints=(JointKinematicState("joint.hip", 0.0, 0.0), JointKinematicState("joint.elbow", 0.0, 0.0)),
        )
    state = _state()
    encoded = state.checkpoint_bytes()
    with pytest.raises(ValueError, match="checkpoint morphology binding"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            encoded, active_morphology=_morphology("morph.next")
        )
