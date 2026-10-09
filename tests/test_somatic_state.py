from embodiment import LivingBodyState, MetabolicLedger, VitalState


def test_living_body_checkpoint_round_trip_preserves_somatic_state():
    state = LivingBodyState(
        energy_reserve=1.25,
        structural_integrity=0.7,
        temperature=0.6,
        fatigue=0.2,
        age_ticks=9,
    )

    restored = LivingBodyState.from_checkpoint(state.checkpoint())

    assert restored.energy_reserve == 1.25
    assert restored.structural_integrity == 0.7
    assert restored.temperature == 0.6
    assert restored.fatigue == 0.2
    assert restored.age_ticks == 9
    assert restored.vital_state is VitalState.ACTIVE


def test_body_backed_metabolic_charge_debits_physical_energy_once():
    state = LivingBodyState(energy_reserve=1.0, max_energy=2.0)
    ledger = MetabolicLedger(body_state=state)

    ledger.charge("cognition", 0.1)

    assert state.energy_reserve == 0.9
    assert ledger.body_state is state
    assert ledger.snapshot().spent["cognition"] == 0.1


def test_depleted_body_state_uses_current_code_dead_vital_label():
    state = LivingBodyState(energy_reserve=0.1)

    consumed = state.consume_energy(0.2)

    assert consumed == 0.1
    assert state.vital_state is VitalState.DEAD
    assert state.death_tick == 0
