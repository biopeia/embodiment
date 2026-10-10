import json

import pytest

from embodiment import (
    EmbodimentCheckpoint,
    LivingBodyState,
    MetabolicLedger,
    ResourcePressure,
)
from embodiment.physiology_config import PhysiologyConfig


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


def test_checkpoint_rejects_duplicate_json_fields():
    with pytest.raises(ValueError, match="checkpoint JSON"):
        EmbodimentCheckpoint.from_bytes(
            b'{"schema_version":2,"schema_version":2}'
        )


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

    payload["schema_version"] = 1
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

    assert EmbodimentCheckpoint.validate_checkpoint(
        encoded, "body-17", "embodiment-checkpoint-v2"
    )
    assert not EmbodimentCheckpoint.validate_checkpoint(
        encoded, "body-other", "embodiment-checkpoint-v2"
    )
    assert not EmbodimentCheckpoint.validate_checkpoint(encoded, "body-17", "embodiment-checkpoint-v1")
    assert not EmbodimentCheckpoint.validate_checkpoint(encoded, "body-17", "unsupported-schema")
    assert not EmbodimentCheckpoint.validate_checkpoint(
        b"not a checkpoint", "body-17", "embodiment-checkpoint-v2"
    )


def test_checkpoint_preserves_custom_physiology_and_pending_spend():
    body = LivingBodyState(energy_reserve=1.5, max_energy=2.0)
    config = PhysiologyConfig(ratio_severe=0.6, ratio_elevated=0.9)
    ledger = MetabolicLedger(body_state=body, physiology_config=config, tick=4)
    ledger.charge("cognition", 0.2)
    original = EmbodimentCheckpoint("body-17", "episode-3", body, ledger)

    restored = EmbodimentCheckpoint.from_bytes(original.to_bytes())

    assert restored.metabolic_ledger.physiology_config == config
    assert restored.metabolic_ledger.pressure() is ResourcePressure.ELEVATED
    assert restored.metabolic_ledger.snapshot().spent["cognition"] == pytest.approx(0.2)
    assert restored.to_bytes() == original.to_bytes()

    original_result = original.metabolic_ledger.advance()
    restored_result = restored.metabolic_ledger.advance()
    assert restored_result == original_result
    assert restored.to_bytes() == original.to_bytes()


def test_metabolic_checkpoint_rejects_old_schema_missing_or_unknown_fields():
    payload = json.loads(_checkpoint().to_bytes())
    ledger = payload["metabolic_ledger"]

    old_schema = dict(ledger, schema_version=2)
    with pytest.raises(ValueError, match="metabolic checkpoint"):
        MetabolicLedger.from_checkpoint(old_schema)

    missing = dict(ledger)
    del missing["physiology_config"]
    with pytest.raises(ValueError, match="metabolic checkpoint"):
        MetabolicLedger.from_checkpoint(missing)

    unknown = dict(ledger, unrecognized=True)
    with pytest.raises(ValueError, match="metabolic checkpoint"):
        MetabolicLedger.from_checkpoint(unknown)


def test_metabolic_checkpoint_rejects_invalid_config_and_spent_values():
    payload = json.loads(_checkpoint().to_bytes())["metabolic_ledger"]
    bad_config = json.loads(json.dumps(payload))
    bad_config["physiology_config"]["ratio_elevated"] = True
    with pytest.raises(ValueError, match="physiology configuration"):
        MetabolicLedger.from_checkpoint(bad_config)

    bad_spent = json.loads(json.dumps(payload))
    bad_spent["spent"]["cognition"] = True
    with pytest.raises(ValueError, match="spent"):
        MetabolicLedger.from_checkpoint(bad_spent)


def test_metabolic_checkpoint_rejects_out_of_range_pending_spend():
    payload = json.loads(_checkpoint().to_bytes())["metabolic_ledger"]
    payload["spent"]["cognition"] = payload["capacity"]["cognition"] * 2.1
    with pytest.raises(ValueError, match="spent"):
        MetabolicLedger.from_checkpoint(payload)
