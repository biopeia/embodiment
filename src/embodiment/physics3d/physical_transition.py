"""Embodiment-owned acceptance of a physical solver candidate.

This module does not execute a solver or commit a World cut. It provides the
owner boundary which validates a correlated candidate and returns a new,
Embodiment-owned pose state. The state is currently in-memory only; it is not
durably referenceable until an owner checkpoint contract includes it.
"""

from __future__ import annotations

from dataclasses import dataclass
from embodiment.observation import BodyPoseSample


@dataclass(frozen=True, slots=True)
class PhysicalStepCorrelation:
    """Identity and revisions for one physical execution, never a solver API."""

    world_id: str
    causal_tick: int
    physical_step_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    environment_revision: str
    solver_config_revision: str

    def __post_init__(self) -> None:
        for name in (
            "world_id", "physical_step_id", "body_id", "embodiment_episode_id",
            "morphology_revision", "environment_revision", "solver_config_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if isinstance(self.causal_tick, bool) or not isinstance(self.causal_tick, int) or self.causal_tick < 0:
            raise ValueError("causal_tick must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SolverBodyCandidate:
    """Untrusted numerical result proposed for owner adoption.

    Position is metres and orientation is xyzw in the declared reference/body
    frames. The solver is responsible only for producing these numerical
    values; this type does not grant them authority.
    """

    correlation: PhysicalStepCorrelation
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class EmbodimentPhysicalState:
    """Current owner-held body pose at a World causal tick.

    This is explicitly ``EMBODIMENT_OWNED`` and in-memory only. It has no
    durable checkpoint reference; World must not commit it as recoverable until
    a durable owner checkpoint is available.
    """

    world_id: str
    causal_tick: int
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    pose: BodyPoseSample
    state_owner: str = "EMBODIMENT_OWNED"
    durable_reference: str | None = None

    def __post_init__(self) -> None:
        for name in ("world_id", "body_id", "embodiment_episode_id", "morphology_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if self.state_owner != "EMBODIMENT_OWNED":
            raise ValueError("physical pose state must be Embodiment-owned")
        if self.durable_reference is not None:
            raise ValueError("this in-memory state type cannot claim a durable reference")
        if isinstance(self.causal_tick, bool) or not isinstance(self.causal_tick, int) or self.causal_tick < 0:
            raise ValueError("causal_tick must be a non-negative integer")
        if self.pose.body_id != self.body_id:
            raise ValueError("pose body identity differs from owner state")

    @property
    def durably_referenceable(self) -> bool:
        return False

    def adopt_candidate(
        self,
        candidate: SolverBodyCandidate,
        *,
        expected_step: PhysicalStepCorrelation,
    ) -> EmbodimentPhysicalState:
        """Validate and adopt a next-tick pose, returning a new owner state.

        Rejection leaves this immutable state untouched. A candidate is valid
        only for the exact active identities/revisions and current causal tick.
        """

        c = candidate.correlation
        if c != expected_step:
            raise ValueError("solver candidate does not match the authorized physical step")
        expected = (
            self.world_id,
            self.causal_tick,
            self.body_id,
            self.embodiment_episode_id,
            self.morphology_revision,
        )
        actual = (c.world_id, c.causal_tick, c.body_id, c.embodiment_episode_id, c.morphology_revision)
        if actual != expected:
            raise ValueError("solver candidate correlation does not match active Embodiment state")
        if not candidate.reference_frame.strip() or not candidate.body_frame.strip():
            raise ValueError("candidate reference and body frames must be explicit")
        if (
            candidate.reference_frame != self.pose.reference_frame
            or candidate.body_frame != self.pose.body_frame
        ):
            raise ValueError("solver candidate frames do not match active Embodiment pose frames")
        pose = BodyPoseSample(
            body_id=self.body_id,
            reference_frame=candidate.reference_frame,
            body_frame=candidate.body_frame,
            position_m=candidate.position_m,
            orientation_xyzw=candidate.orientation_xyzw,
            sample_kind="physics_step",
            sample_value=c.physical_step_id,
        )
        return EmbodimentPhysicalState(
            world_id=self.world_id,
            causal_tick=self.causal_tick + 1,
            body_id=self.body_id,
            embodiment_episode_id=self.embodiment_episode_id,
            morphology_revision=self.morphology_revision,
            pose=pose,
        )


__all__ = ["EmbodimentPhysicalState", "PhysicalStepCorrelation", "SolverBodyCandidate"]
