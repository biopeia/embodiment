"""Body-side acceptance of explicit material transfers.

The caller owns obtaining and authorizing the transfer. This module only
applies a transfer addressed to a body to that body's somatic energy state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .physiology import LivingBodyState


@dataclass(frozen=True, slots=True)
class MaterialTransfer:
    """Scalar material transfer addressed to one body instance.

    ``source_id`` and ``composition`` are provenance/description fields; the
    current acceptance rule does not interpret either field.
    """

    source_id: str
    target_body_id: str
    amount: float
    composition: str = "organic"

    def __post_init__(self) -> None:
        if not self.target_body_id:
            raise ValueError("target_body_id must not be empty")
        if not math.isfinite(self.amount) or self.amount < 0.0:
            raise ValueError("transfer amount must be finite and non-negative")


def absorb_material_transfer(
    *, body_id: str, body_state: LivingBodyState, transfer: MaterialTransfer
) -> float:
    """Apply the CURRENT body-side scalar acceptance rule.

    A transfer addressed to another body is rejected. Otherwise the body's
    existing ``add_energy`` operation determines the accepted amount, including
    dead-body and capacity behavior. Source selection, environmental stock,
    refunds, and transaction ordering remain outside Embodiment.
    """

    if transfer.target_body_id != body_id:
        return 0.0
    return body_state.add_energy(transfer.amount)


__all__ = ["MaterialTransfer", "absorb_material_transfer"]
