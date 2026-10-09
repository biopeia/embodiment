import json

import pytest

from embodiment import EmbodimentCheckpoint, LivingBodyState, MetabolicLedger


def _checkpoint() -> EmbodimentCheckpoint:
    body = LivingBodyState(energy_reserve=1.2, max_energy=2.0, age_ticks=7)
    ledger = MetabolicLedger(body_state=body, tick=7)
    ledger.charge("cognition", 0.2)
    return EmbodimentCheckpoint("body-17", "episode-3", body, ledger)


def test_checkpoint_round_trip_is_deterministic_and_preserves_episode_identity():
    original = _checkpoint()
    encoded = original.to_bytes()
    restored = EmbodimentCheckpoint.from_bytes(encoded)

    assert restored.to_bytes() == encoded
    assert restored.body_id == "body-17"
    assert restored.episode_id == "episode-3"
    assert restored.body_state.energy_reserve == pytest.approx(1.0)
    assert restored.body_state.age_ticks == 7
    assert restored.metabolic_ledger.tick == 7
    assert restored.metabolic_ledger.body_state is restored.body_state


@pytest.mark.parametrize("payload", [b"not json", b"[]", b'{"schema_version":99}'])
def test_checkpoint_rejects_malformed_or_unsupported_payload(payload: bytes):
    with pytest.raises(ValueError):
        EmbodimentCheckpoint.from_bytes(payload)


def test_checkpoint_rejects_unknown_envelope_fields():
    payload = json.loads(_checkpoint().to_bytes())
    payload["unrecognized"] = "must not be ignored"

    with pytest.raises(ValueError, match="checkpoint fields"):
        EmbodimentCheckpoint.from_bytes(json.dumps(payload).encode())


def test_checkpoint_rejects_boolean_schema_version():
    payload = json.loads(_checkpoint().to_bytes())
    payload["schema_version"] = True

    with pytest.raises(ValueError, match="schema"):
        EmbodimentCheckpoint.from_bytes(json.dumps(payload).encode())


def test_checkpoint_rejects_ledger_body_energy_mismatch():
    payload = json.loads(_checkpoint().to_bytes())
    payload["metabolic_ledger"]["physical_energy_reserve"] += 0.5

    with pytest.raises(ValueError, match="contradicts"):
        EmbodimentCheckpoint.from_bytes(json.dumps(payload).encode())


def test_checkpoint_requires_ledger_bound_to_same_body_object():
    body = LivingBodyState()
    ledger = MetabolicLedger()

    with pytest.raises(ValueError, match="bound"):
        EmbodimentCheckpoint("body", "episode", body, ledger)


def test_owner_checkpoint_validation_checks_identity_schema_and_bytes():
    encoded = _checkpoint().to_bytes()

    assert EmbodimentCheckpoint.validate_checkpoint(encoded, "body-17", "embodiment-checkpoint-v1")
    assert not EmbodimentCheckpoint.validate_checkpoint(encoded, "body-other", "embodiment-checkpoint-v1")
    assert not EmbodimentCheckpoint.validate_checkpoint(encoded, "body-17", "unsupported-schema")
    assert not EmbodimentCheckpoint.validate_checkpoint(b"not a checkpoint", "body-17", "embodiment-checkpoint-v1")
