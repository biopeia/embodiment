from dataclasses import replace

import pytest

from embodiment.observation import BodyPoseSample
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


def _state() -> EmbodimentPhysicalState:
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
    )


def _candidate(correlation: PhysicalStepCorrelation) -> SolverBodyCandidate:
    return SolverBodyCandidate(
        correlation=correlation,
        reference_frame="physics3d.world",
        body_frame="body.root",
        position_m=(0.0, 0.0, 0.9),
        orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
    )


def test_adoption_requires_exact_authorized_step_and_returns_new_owner_state() -> None:
    state = _state()
    authorized = _correlation()
    adopted = state.adopt_candidate(_candidate(authorized), expected_step=authorized)

    assert adopted is not state
    assert adopted.state_owner == "EMBODIMENT_OWNED"
    assert adopted.causal_tick == 5
    assert adopted.pose.position_m == (0.0, 0.0, 0.9)
    assert state.causal_tick == 4
    assert state.pose.position_m == (0.0, 0.0, 1.0)


@pytest.mark.parametrize(
    "change",
    [
        {"world_id": "world.other"},
        {"causal_tick": 3},
        {"physical_step_id": "step.other"},
        {"body_id": "body.other"},
        {"embodiment_episode_id": "episode.other"},
        {"morphology_revision": "morph.stale"},
        {"environment_revision": "environment.other"},
        {"solver_config_revision": "solver.other"},
    ],
)
def test_rejects_stale_or_wrong_correlation_without_mutating_owner_state(change: dict[str, object]) -> None:
    state = _state()
    authorized = _correlation()
    before = state
    with pytest.raises(ValueError):
        state.adopt_candidate(_candidate(replace(authorized, **change)), expected_step=authorized)
    assert state is before
    assert state.causal_tick == 4
    assert state.pose.position_m == (0.0, 0.0, 1.0)


def test_current_candidate_cannot_be_adopted_under_another_authorized_step() -> None:
    state = _state()
    candidate_correlation = _correlation()
    wrong_authorization = _correlation(solver_config_revision="solver.new")
    with pytest.raises(ValueError, match="authorized physical step"):
        state.adopt_candidate(_candidate(candidate_correlation), expected_step=wrong_authorization)
    assert state.causal_tick == 4


def test_adopted_state_explicitly_has_no_durable_checkpoint_reference() -> None:
    state = _state()
    assert state.state_owner == "EMBODIMENT_OWNED"
    assert state.durable_reference is None
    assert state.durably_referenceable is False
