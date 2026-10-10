from dataclasses import dataclass, replace
import hashlib
import json

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_state import (
    ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
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


def _world_context(step: PhysicalStepCorrelation | None = None) -> _WorldContext:
    if step is None:
        return _WorldContext()
    return _WorldContext(
        world_id=step.world_id,
        source_causal_tick=step.causal_tick,
        target_causal_tick=step.causal_tick + 1,
        physical_step_id=step.physical_step_id,
        body_id=step.body_id,
        embodiment_episode_id=step.embodiment_episode_id,
        morphology_revision=step.morphology_revision,
        environment_revision=step.environment_revision,
        solver_config_revision=step.solver_config_revision,
    )


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
    adopted = state.adopt_candidate(_candidate(), world_context=_world_context(step))

    assert [(item.joint_id, item.position_rad) for item in adopted.joints] == [
        ("joint.elbow", 0.4),
        ("joint.hip", -0.3),
    ]
    permuted = state.adopt_candidate(
        _candidate(tuple(reversed(_candidate().joints))), world_context=_world_context(step)
    )
    assert permuted == adopted
    assert state.causal_tick == 4
    assert adopted.causal_tick == 5
    assert adopted.root.last_physical_step == step


def test_active_morphology_holds_an_immutable_segment_snapshot() -> None:
    morphology = _morphology()
    digest = morphology.morphology_sha256

    with pytest.raises(AttributeError):
        morphology.spec.segments.clear()

    assert morphology.morphology_sha256 == digest


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
        state.adopt_candidate(_candidate(joints), world_context=_world_context())
    assert state.root is original_root
    assert state.causal_tick == 4


def test_rejects_stale_morphology_even_when_joint_names_match() -> None:
    state = _state()
    stale = replace(_correlation(), morphology_revision="morph.old")
    candidate = _candidate()
    with pytest.raises(ValueError, match="World physical-step context"):
        state.adopt_candidate(
            SolverArticulatedCandidate(
                replace(candidate.root, correlation=stale), candidate.joints
            ),
            world_context=_world_context(),
        )
    assert state.causal_tick == 4


def test_articulated_checkpoint_is_deterministic_and_restores_exact_state() -> None:
    state = _state().adopt_candidate(_candidate(), world_context=_world_context())
    encoded = state.checkpoint_bytes()
    restored = ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        encoded, active_morphology=state.morphology
    )
    assert restored == state
    assert restored.checkpoint_bytes() == encoded
    payload = json.loads(encoded)
    assert payload["schema_version"] == 2
    assert payload["position_unit"] == "rad"
    assert payload["velocity_unit"] == "rad/s"
    assert payload["active_morphology"]["spec"]["contact_link_names"] == ["body.root", "body.forearm"]
    assert payload["active_morphology"]["morphology_sha256"] == state.morphology.morphology_sha256
    assert state.durably_referenceable is False
    assert state.checkpoint_digest == __import__("hashlib").sha256(encoded).hexdigest()


def test_restored_articulated_state_can_continue_on_the_next_causal_step() -> None:
    first = _state().adopt_candidate(_candidate(), world_context=_world_context())
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

    second = resumed.adopt_candidate(second_candidate, world_context=_world_context(second_step))

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
    payload["schema_version"] = 1
    with pytest.raises(ValueError, match="unsupported"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload).encode(), active_morphology=state.morphology
        )


def test_checkpoint_binds_the_complete_body_specification() -> None:
    state = _state()
    payload = json.loads(state.checkpoint_bytes())
    payload["active_morphology"]["spec"]["contact_link_names"] = ["body.root"]

    with pytest.raises(ValueError, match="morphology binding"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            json.dumps(payload).encode(), active_morphology=state.morphology
        )


def test_checkpoint_v1_is_rejected_without_compatibility_fallback() -> None:
    state = _state()
    payload = json.loads(state.checkpoint_bytes())
    payload["schema_version"] = 1
    payload["active_morphology"].pop("spec")
    payload["active_morphology"].pop("morphology_sha256")

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


def test_owner_validation_and_restoration_verification_bind_checkpoint_reference() -> None:
    state = _state()
    encoded = state.checkpoint_bytes()
    reference_digest = state.checkpoint_digest

    assert ArticulatedEmbodimentPhysicalState.validate_checkpoint(
        encoded,
        active_morphology=state.morphology,
        expected_sha256=reference_digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    restored = ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        encoded, active_morphology=state.morphology
    )
    assert ArticulatedEmbodimentPhysicalState.verify_restoration(
        encoded,
        restored,
        active_morphology=state.morphology,
        expected_sha256=reference_digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )


def test_owner_validation_and_restore_reject_noncanonical_json_bytes() -> None:
    state = _state()
    canonical = state.checkpoint_bytes()
    noncanonical = json.dumps(json.loads(canonical), indent=2).encode()

    # Integrity is checked against the exact supplied reference, but a valid
    # digest must not make alternate encodings acceptable to restore while
    # verify_restoration requires the canonical checkpoint bytes.
    noncanonical_digest = hashlib.sha256(noncanonical).hexdigest()
    assert not ArticulatedEmbodimentPhysicalState.validate_checkpoint(
        noncanonical,
        active_morphology=state.morphology,
        expected_sha256=noncanonical_digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    with pytest.raises(ValueError, match="non-canonical"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            noncanonical, active_morphology=state.morphology
        )


@pytest.mark.parametrize(
    "active_morphology",
    [
        replace(_morphology(), body_id="body.other"),
        replace(_morphology(), embodiment_episode_id="episode.other"),
        _morphology("morph.other"),
    ],
)
def test_owner_validation_rejects_wrong_body_episode_or_revision(active_morphology) -> None:
    state = _state()
    encoded = state.checkpoint_bytes()

    assert not ArticulatedEmbodimentPhysicalState.validate_checkpoint(
        encoded,
        active_morphology=active_morphology,
        expected_sha256=state.checkpoint_digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )


def test_owner_validation_rejects_malformed_wrong_schema_and_tampered_bytes() -> None:
    state = _state()
    encoded = state.checkpoint_bytes()
    digest = state.checkpoint_digest
    validate = ArticulatedEmbodimentPhysicalState.validate_checkpoint

    assert not validate(
        b"not json",
        active_morphology=state.morphology,
        expected_sha256=digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    assert not validate(
        encoded,
        active_morphology=state.morphology,
        expected_sha256=digest,
        schema_version="embodiment-articulated-physical-checkpoint-v1",
    )
    assert not validate(
        encoded,
        active_morphology=state.morphology,
        expected_sha256="0" * 64,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    changed_payload = json.loads(encoded)
    changed_payload["joints"][0]["position_rad"] += 0.01
    tampered = json.dumps(changed_payload, sort_keys=True, separators=(",", ":")).encode()
    assert not validate(
        tampered,
        active_morphology=state.morphology,
        expected_sha256=digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )


def test_owner_validation_rejects_integer_overflow_in_checkpoint_numeric_fields() -> None:
    state = _state()
    payload = json.loads(state.checkpoint_bytes())
    payload["joints"][0]["position_rad"] = 10**400
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    assert not ArticulatedEmbodimentPhysicalState.validate_checkpoint(
        encoded,
        active_morphology=state.morphology,
        expected_sha256=hashlib.sha256(encoded).hexdigest(),
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    with pytest.raises(ValueError, match="invalid articulated Embodiment checkpoint value"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            encoded, active_morphology=state.morphology
        )


def test_restoration_verification_rejects_state_from_another_checkpoint_without_mutation() -> None:
    state = _state()
    encoded = state.checkpoint_bytes()
    restored = ArticulatedEmbodimentPhysicalState.restore_checkpoint(
        encoded, active_morphology=state.morphology
    )
    other = ArticulatedEmbodimentPhysicalState(
        root=replace(restored.root, causal_tick=restored.causal_tick + 1),
        morphology=restored.morphology,
        joints=restored.joints,
    )
    before = other.checkpoint_bytes()

    assert not ArticulatedEmbodimentPhysicalState.verify_restoration(
        encoded,
        other,
        active_morphology=state.morphology,
        expected_sha256=state.checkpoint_digest,
        schema_version=ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
    )
    assert other.checkpoint_bytes() == before


def test_articulated_checkpoint_rejects_duplicate_json_keys() -> None:
    encoded = _state().checkpoint_bytes()
    duplicate = encoded.replace(b'"schema_version":2', b'"schema_version":2,"schema_version":2', 1)

    with pytest.raises(ValueError, match="invalid articulated Embodiment checkpoint JSON"):
        ArticulatedEmbodimentPhysicalState.restore_checkpoint(
            duplicate, active_morphology=_morphology()
        )
