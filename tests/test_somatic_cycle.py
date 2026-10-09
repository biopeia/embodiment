import pytest

from embodiment import LivingBodyState, SomaticCycle, VitalState


def test_somatic_cycle_applies_body_local_cost_wear_and_age_in_source_order():
    body = LivingBodyState(energy_reserve=1.0, structural_integrity=1.0)

    SomaticCycle().advance(body)

    assert body.energy_reserve == pytest.approx(0.995)
    assert body.structural_integrity == pytest.approx(0.9995)
    assert body.age_ticks == 1
    assert body.vital_state is VitalState.ACTIVE


def test_somatic_cycle_preserves_source_behavior_when_energy_depletion_marks_dead():
    body = LivingBodyState(energy_reserve=0.001, structural_integrity=1.0)

    SomaticCycle().advance(body)

    # Source ordering still applies passive wear after the energy debit; age
    # does not advance because consume_energy has already made the body dead.
    assert body.energy_reserve == 0.0
    assert body.structural_integrity == pytest.approx(0.9995)
    assert body.age_ticks == 0
    assert body.vital_state is VitalState.DEAD
    assert body.death_tick == 0


def test_somatic_cycle_does_not_advance_an_already_dead_body():
    body = LivingBodyState(energy_reserve=0.0)
    body.mark_dead(0)
    before = body.checkpoint()

    SomaticCycle().advance(body)

    assert body.checkpoint() == before


@pytest.mark.parametrize("rate", [-1.0, float("inf"), float("nan")])
def test_somatic_cycle_rejects_invalid_rates(rate):
    with pytest.raises(ValueError):
        SomaticCycle(basal_metabolic_rate=rate)


def test_somatic_cycle_rejects_non_body_state():
    with pytest.raises(ValueError, match="body_state"):
        SomaticCycle().advance(object())  # type: ignore[arg-type]
