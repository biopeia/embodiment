import pytest

from embodiment import LivingBodyState, MaterialTransfer, VitalState, absorb_material_transfer


def test_transfer_to_matching_body_accepts_only_available_capacity():
    body = LivingBodyState(energy_reserve=1.8, max_energy=2.0)
    transfer = MaterialTransfer(
        source_id="world:cell-1",
        target_body_id="body-1",
        amount=0.5,
    )

    accepted = absorb_material_transfer(
        body_id="body-1", body_state=body, transfer=transfer
    )

    assert accepted == pytest.approx(0.2)
    assert body.energy_reserve == pytest.approx(2.0)


def test_transfer_for_different_body_is_rejected_without_state_change():
    body = LivingBodyState(energy_reserve=1.0)
    before = body.checkpoint()
    transfer = MaterialTransfer(
        source_id="world:cell-1",
        target_body_id="body-2",
        amount=0.5,
    )

    accepted = absorb_material_transfer(
        body_id="body-1", body_state=body, transfer=transfer
    )

    assert accepted == 0.0
    assert body.checkpoint() == before


def test_matching_transfer_to_dead_body_is_not_accepted():
    body = LivingBodyState(energy_reserve=0.0)
    body.mark_dead(0)
    before = body.checkpoint()
    transfer = MaterialTransfer(
        source_id="world:cell-1",
        target_body_id="body-1",
        amount=0.5,
    )

    accepted = absorb_material_transfer(
        body_id="body-1", body_state=body, transfer=transfer
    )

    assert accepted == 0.0
    assert body.vital_state is VitalState.DEAD
    assert body.checkpoint() == before


def test_zero_amount_transfer_is_accepted_as_zero():
    body = LivingBodyState(energy_reserve=1.0)
    transfer = MaterialTransfer(
        source_id="world:cell-1",
        target_body_id="body-1",
        amount=0.0,
    )

    assert absorb_material_transfer(body_id="body-1", body_state=body, transfer=transfer) == 0.0
    assert body.energy_reserve == 1.0


@pytest.mark.parametrize("amount", [-0.1, float("inf"), float("nan")])
def test_transfer_rejects_negative_or_non_finite_amount(amount):
    with pytest.raises(ValueError, match="transfer amount"):
        MaterialTransfer(source_id="world:cell-1", target_body_id="body-1", amount=amount)


def test_transfer_rejects_empty_target_body_id():
    with pytest.raises(ValueError, match="target_body_id"):
        MaterialTransfer(source_id="world:cell-1", target_body_id="", amount=0.5)
