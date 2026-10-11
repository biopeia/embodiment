from dataclasses import replace

import pytest

from embodiment.observation import (
    BodyPoseObservationProjection,
    BodyPoseSample,
    PhysicalStepCorrelation,
)
from embodiment.physics3d.physical_transition import (
    EmbodimentPhysicalState,
    SolverBodyCandidate,
)


def _state() -> EmbodimentPhysicalState:
    return EmbodimentPhysicalState(
        world_id="world.1",
        causal_tick=4,
        body_id="body.1",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.3",
        pose=BodyPoseSample(
            body_id="body.1",
            reference_frame="world.frame",
            body_frame="body.root",
            position_m=(0.0, 0.0, 1.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value=4,
        ),
        linear_velocity_m_per_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )


def _adopted_state() -> EmbodimentPhysicalState:
    correlation = PhysicalStepCorrelation(
        world_id="world.1",
        causal_tick=4,
        physical_step_id="step.5",
        body_id="body.1",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.3",
        environment_revision="environment.6",
        solver_config_revision="solver.7",
    )
    candidate = SolverBodyCandidate(
        correlation=correlation,
        reference_frame="world.frame",
        body_frame="body.root",
        position_m=(0.0, 0.0, 0.9),
        orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
        linear_velocity_m_per_s=(0.0, 0.0, -1.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )

    class _WorldContext:
        world_id = "world.1"
        source_causal_tick = 4
        target_causal_tick = 5
        physical_step_id = "step.5"
        body_id = "body.1"
        embodiment_episode_id = "episode.2"
        morphology_revision = "morph.3"
        environment_revision = "environment.6"
        solver_config_revision = "solver.7"

    return _state().adopt_candidate(candidate, world_context=_WorldContext())


def test_owner_projection_preserves_adopted_identity_revision_and_step_correlation() -> (
    None
):
    adopted = _adopted_state()

    projection = adopted.body_pose_observation_projection()

    assert projection == BodyPoseObservationProjection(
        world_id="world.1",
        causal_tick=5,
        body_id="body.1",
        embodiment_episode_id="episode.2",
        morphology_revision="morph.3",
        pose=adopted.pose,
        last_physical_step_id="step.5",
        last_physical_step_source_tick=4,
        environment_revision="environment.6",
        solver_config_revision="solver.7",
        physical_step_correlation=adopted.last_physical_step,
    )


def test_projection_rejects_pose_with_another_body_identity() -> None:
    adopted = _adopted_state()
    with pytest.raises(ValueError, match="pose body identity"):
        BodyPoseObservationProjection(
            world_id=adopted.world_id,
            causal_tick=adopted.causal_tick,
            body_id="body.other",
            embodiment_episode_id=adopted.embodiment_episode_id,
            morphology_revision=adopted.morphology_revision,
            pose=adopted.pose,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"last_physical_step_id": None},
        {"last_physical_step_source_tick": 3},
        {"environment_revision": ""},
        {"solver_config_revision": None},
    ],
)
def test_projection_rejects_incomplete_or_stale_step_correlation(
    changes: dict[str, object],
) -> None:
    adopted = _adopted_state()
    valid = adopted.body_pose_observation_projection()
    with pytest.raises(ValueError):
        replace(valid, **changes)


def test_projection_rejects_step_id_that_does_not_match_pose_sample() -> None:
    adopted = _adopted_state()
    valid = adopted.body_pose_observation_projection()
    with pytest.raises(ValueError, match="does not identify"):
        replace(valid, last_physical_step_id="step.other")


@pytest.mark.parametrize(
    "changes",
    [
        {"world_id": "world.other"},
        {"embodiment_episode_id": "episode.other"},
        {"morphology_revision": "morph.other"},
        {"environment_revision": "environment.other"},
        {"solver_config_revision": "solver.other"},
    ],
)
def test_projection_rejects_identity_or_revision_not_matching_retained_correlation(
    changes: dict[str, object],
) -> None:
    valid = _adopted_state().body_pose_observation_projection()

    with pytest.raises(ValueError, match="differ from physical-step correlation"):
        replace(valid, **changes)


def test_initial_owner_state_projection_has_no_fabricated_step_correlation() -> None:
    projection = _state().body_pose_observation_projection()

    assert projection.causal_tick == 4
    assert projection.last_physical_step_id is None
    assert projection.last_physical_step_source_tick is None
    assert projection.environment_revision is None
    assert projection.solver_config_revision is None
    assert projection.physical_step_correlation is None


def test_projection_rejects_physics_step_pose_without_retained_correlation() -> None:
    pose = replace(
        _state().pose,
        sample_kind="physics_step",
        sample_value="step.5",
    )

    with pytest.raises(ValueError, match="requires a physical-step correlation"):
        BodyPoseObservationProjection(
            world_id="world.1",
            causal_tick=5,
            body_id="body.1",
            embodiment_episode_id="episode.2",
            morphology_revision="morph.3",
            pose=pose,
        )
