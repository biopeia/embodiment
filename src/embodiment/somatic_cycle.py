"""Bounded body-local basal cycle extracted from the current body runtime."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .physiology import LivingBodyState


@dataclass(frozen=True, slots=True)
class SomaticCycle:
    """Apply the source body's basal-energy, wear, and age transition.

    This is only the body-local rule formerly implemented by
    ``Body.tick_physics``. It does not schedule causal ticks, resolve a World,
    model a physics solver, or assert biological validity.
    """

    basal_metabolic_rate: float = 0.005
    degradation_rate: float = 0.0005

    def __post_init__(self) -> None:
        for name in ("basal_metabolic_rate", "degradation_rate"):
            value = getattr(self, name)
            try:
                normalized = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} must be numeric") from exc
            if not math.isfinite(normalized) or normalized < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
            object.__setattr__(self, name, normalized)

    def advance(self, body_state: LivingBodyState) -> None:
        """Advance one source-compatible body cycle in the original order."""
        if not isinstance(body_state, LivingBodyState):
            raise ValueError("body_state must be LivingBodyState")
        if not body_state.alive:
            return
        body_state.consume_energy(self.basal_metabolic_rate)
        body_state.apply_wear(self.degradation_rate)
        body_state.advance_age()


__all__ = ["SomaticCycle"]
