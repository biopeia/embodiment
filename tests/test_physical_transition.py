from dataclasses import dataclass, replace
import json

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


@dataclass(frozen=True)
class _WorldContext:
    world_id: str = "world.1"
    source_causal_tick: int = 4
    target_causal_tick: int = 5
    physical_step_id: str = "step.5"
    body_id: str = "body.1"
    embodiment_episode_id: str = "episode.2"
    morphology_revision: str = "morph.3"
    environment_revision: str = "environment.6"
    solver_config_revision: str = "solver.7"


def _world_context(**changes: object) -> _WorldContext:
    return replace(_WorldContext(), **changes)


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
        linear_velocity_m_per_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )


def _candidate(correlation: PhysicalStepCorrelation) -> SolverBodyCandidate:
    return SolverBodyCandidate(
        correlation=correlation,
        reference_frame="physics3d.world",
        body_frame="body.root",
        position_m=(0.0, 0.0, 0.9),
        orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
        linear_velocity_m_per_s=(0.0, 0.0, -1.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )


def test_adoption_requires_exact_authorized_step_and_returns_new_owner_state() -> None:
    state = _state()
    authorized = _correlation()
    adopted = state.adopt_candidate(_candidate(authorized), world_context=_world_context())

    assert adopted is not state
    assert adopted.state_owner == "EMBODIMENT_OWNED"
    assert adopted.causal_tick == 5
    assert adopted.pose.position_m == (0.0, 0.0, 0.9)
    assert adopted.linear_velocity_m_per_s == (0.0, 0.0, -1.0)
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
        state.adopt_candidate(_candidate(replace(authorized, **change)), world_context=_world_context())
    assert state is before
    assert state.causal_tick == 4
    assert state.pose.position_m == (0.0, 0.0, 1.0)


def test_current_candidate_cannot_be_adopted_under_another_authorized_step() -> None:
    state = _state()
    candidate_correlation = _correlation()
    wrong_authorization = _world_context(solver_config_revision="solver.new")
    with pytest.raises(ValueError, match="World physical-step context"):
        state.adopt_candidate(_candidate(candidate_correlation), world_context=wrong_authorization)
    assert state.causal_tick == 4


@pytest.mark.parametrize(
    "changes",
    [
        {"target_causal_tick": 6},
        {"source_causal_tick": -1, "target_causal_tick": 0},
        {"target_causal_tick": True},
        {"environment_revision": " "},
    ],
)
def test_rejects_invalid_world_context(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="World physical-step"):
        _state().adopt_candidate(
            _candidate(_correlation()), world_context=_world_context(**changes)
        )


def test_adoption_stages_values_and_world_commit_selects_authoritative_result() -> None:
    state = _state()
    context = _world_context()
    first_candidate = _candidate(_correlation())
    second_candidate = replace(first_candidate, position_m=(0.0, 0.0, 0.8))

    first = state.adopt_candidate(first_candidate, world_context=context)
    second = state.adopt_candidate(second_candidate, world_context=context)

    # Embodiment returns staged immutable values; only World commit selects
    # which owner checkpoint reference is authoritative. Neither call mutates
    # the source state or claims a commit.
    assert first.pose.position_m != second.pose.position_m
    assert first.causal_tick == second.causal_tick == 5
    assert state.causal_tick == 4
    assert state.last_physical_step is None


def test_adopted_state_explicitly_has_no_durable_checkpoint_reference() -> None:
    state = _state()
    assert state.state_owner == "EMBODIMENT_OWNED"
    assert state.durable_reference is None
    assert state.durably_referenceable is False


def test_checkpoint_bytes_are_deterministic_and_restore_exact_adopted_state() -> None:
    initial = _state()
    step = _correlation()
    adopted = initial.adopt_candidate(_candidate(step), world_context=_world_context())

    encoded = adopted.checkpoint_bytes()
    restored = EmbodimentPhysicalState.restore_checkpoint(encoded)

    assert encoded == adopted.checkpoint_bytes()
    assert restored == adopted
    assert restored.last_physical_step == step
    assert restored.pose.position_m == adopted.pose.position_m
    assert restored.pose.orientation_xyzw == adopted.pose.orientation_xyzw
    assert restored.pose.reference_frame == "physics3d.world"
    assert restored.pose.body_frame == "body.root"
    assert json.loads(encoded)["pose"]["position_unit"] == "m"
    assert json.loads(encoded)["pose"]["orientation_order"] == "xyzw"
    assert json.loads(encoded)["linear_velocity_unit"] == "m/s"
    assert json.loads(encoded)["angular_velocity_unit"] == "rad/s"
    assert json.loads(encoded)["velocity_frame"] == "physics3d.world"
    assert restored.linear_velocity_m_per_s == adopted.linear_velocity_m_per_s
    assert restored.angular_velocity_rad_per_s == adopted.angular_velocity_rad_per_s
    assert restored.checkpoint_digest == adopted.checkpoint_digest
    # Encoding/decoding alone does not imply that a store durably persisted it.
    assert restored.durably_referenceable is False


def test_checkpoint_restore_rejects_unsupported_units_and_malformed_bytes() -> None:
    state = _state()
    payload = json.loads(state.checkpoint_bytes())
    payload["schema_version"] = 1
    with pytest.raises(ValueError, match="unsupported Embodiment physical checkpoint schema"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )

    payload = json.loads(state.checkpoint_bytes())
    payload["pose"]["position_unit"] = "cm"
    with pytest.raises(ValueError, match="units"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )
    payload = json.loads(state.checkpoint_bytes())
    payload["angular_velocity_unit"] = "deg/s"
    with pytest.raises(ValueError, match="velocity units or frame"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        )
    with pytest.raises(ValueError, match="JSON"):
        EmbodimentPhysicalState.restore_checkpoint(b"not-json")


@pytest.mark.parametrize("field", ["linear_velocity_m_per_s", "angular_velocity_rad_per_s"])
@pytest.mark.parametrize("value", [(0.0, float("nan"), 0.0), (0.0, 1.0), (0.0, True, 0.0)])
def test_owner_state_rejects_invalid_root_velocity_vectors(field: str, value: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        replace(_state(), **{field: value})


def test_owner_state_rejects_last_step_with_mismatched_identity_or_revision() -> None:
    state = _state()
    step = _correlation()
    adopted = state.adopt_candidate(_candidate(step), world_context=_world_context())

    with pytest.raises(ValueError, match="identity/revision"):
        replace(adopted, last_physical_step=replace(step, morphology_revision="morph.stale"))
    with pytest.raises(ValueError, match="identity/revision"):
        replace(adopted, last_physical_step=replace(step, body_id="body.other"))


def test_owner_state_rejects_physics_step_pose_without_retained_correlation() -> None:
    with pytest.raises(ValueError, match="requires a physical-step correlation"):
        replace(
            _state(),
            pose=replace(_state().pose, sample_kind="physics_step", sample_value="step.5"),
        )


def test_checkpoint_restore_rejects_inconsistent_last_step_and_nonfinite_pose_sample() -> None:
    initial = _state()
    step = _correlation()
    adopted = initial.adopt_candidate(_candidate(step), world_context=_world_context())

    inconsistent = json.loads(adopted.checkpoint_bytes())
    inconsistent["last_physical_step"]["morphology_revision"] = "morph.stale"
    with pytest.raises(ValueError, match="invalid Embodiment physical checkpoint value"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(inconsistent, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        )

    with pytest.raises(ValueError, match="pose numeric sample_value must be finite"):
        replace(initial, pose=replace(initial.pose, sample_value=float("nan")))

    missing_step = json.loads(initial.checkpoint_bytes())
    missing_step["pose"]["sample_kind"] = "physics_step"
    missing_step["pose"]["sample_value"] = "step.5"
    with pytest.raises(ValueError, match="invalid Embodiment physical checkpoint value"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(missing_step, sort_keys=True, separators=(",", ":")).encode()
        )

    nonfinite_sample = json.loads(initial.checkpoint_bytes())
    nonfinite_sample["pose"]["sample_value"] = float("inf")
    with pytest.raises(ValueError, match="invalid Embodiment physical checkpoint value"):
        EmbodimentPhysicalState.restore_checkpoint(
            json.dumps(nonfinite_sample, sort_keys=True, separators=(",", ":"), allow_nan=True).encode()
        )
