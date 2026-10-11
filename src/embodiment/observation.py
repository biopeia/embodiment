"""Embodiment-owned operational observation values.

These types define domain semantics without depending on Lab or transport.
They are not wire records and do not authorize publication by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _vec3(
    value: tuple[float, float, float], *, name: str
) -> tuple[float, float, float]:
    result = tuple(float(item) for item in value)
    if len(result) != 3 or not all(isfinite(item) for item in result):
        raise ValueError(f"{name} must contain three finite values")
    return result


def _quat_xyzw(
    value: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    result = tuple(float(item) for item in value)
    if len(result) != 4 or not all(isfinite(item) for item in result):
        raise ValueError("orientation_xyzw must contain four finite values")
    norm_sq = sum(item * item for item in result)
    if abs(norm_sq - 1.0) > 1e-5:
        raise ValueError("orientation_xyzw must be a unit quaternion")
    return result


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
            "world_id",
            "physical_step_id",
            "body_id",
            "embodiment_episode_id",
            "morphology_revision",
            "environment_revision",
            "solver_config_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if (
            isinstance(self.causal_tick, bool)
            or not isinstance(self.causal_tick, int)
            or self.causal_tick < 0
        ):
            raise ValueError("causal_tick must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class BodyPoseSample:
    """Canonical Embodiment Body Pose v1 base-Body sample.

    Position is always metres and orientation is xyzw. The concrete Physics3D
    producer must prove/convert its inputs before constructing this value.
    """

    body_id: str
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    sample_kind: str
    sample_value: int | float | str
    sample_time_s: float | None = None
    contract_revision: str = "v1"

    def __post_init__(self) -> None:
        body_id = self.body_id.strip()
        reference_frame = self.reference_frame.strip()
        body_frame = self.body_frame.strip()
        sample_kind = self.sample_kind.strip()
        revision = self.contract_revision.strip()
        if not body_id:
            raise ValueError("body_id must not be empty")
        if not reference_frame:
            raise ValueError("reference_frame must not be empty")
        if not body_frame:
            raise ValueError("body_frame must not be empty")
        if not sample_kind:
            raise ValueError("sample_kind must not be empty")
        if not revision:
            raise ValueError("contract_revision must not be empty")
        if self.sample_time_s is not None and not isfinite(float(self.sample_time_s)):
            raise ValueError("sample_time_s must be finite when provided")
        object.__setattr__(self, "body_id", body_id)
        object.__setattr__(self, "reference_frame", reference_frame)
        object.__setattr__(self, "body_frame", body_frame)
        object.__setattr__(self, "sample_kind", sample_kind)
        object.__setattr__(self, "contract_revision", revision)
        if self.sample_time_s is not None:
            object.__setattr__(self, "sample_time_s", float(self.sample_time_s))
        object.__setattr__(
            self,
            "position_m",
            _vec3(self.position_m, name="position_m"),
        )
        object.__setattr__(
            self,
            "orientation_xyzw",
            _quat_xyzw(self.orientation_xyzw),
        )


@dataclass(frozen=True, slots=True)
class BodyPoseObservationProjection:
    """Owner-derived pose projection with the identity needed by consumers.

    This value is produced from adopted Embodiment state. It is not a World
    commit receipt and does not authorize publication; World must independently
    correlate it to a committed causal cut.
    """

    world_id: str
    causal_tick: int
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    pose: BodyPoseSample
    last_physical_step_id: str | None = None
    last_physical_step_source_tick: int | None = None
    environment_revision: str | None = None
    solver_config_revision: str | None = None
    physical_step_correlation: PhysicalStepCorrelation | None = None

    def __post_init__(self) -> None:
        for name in (
            "world_id",
            "body_id",
            "embodiment_episode_id",
            "morphology_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if (
            isinstance(self.causal_tick, bool)
            or not isinstance(self.causal_tick, int)
            or self.causal_tick < 0
        ):
            raise ValueError("causal_tick must be a non-negative integer")
        if not isinstance(self.pose, BodyPoseSample):
            raise TypeError("pose must be an Embodiment BodyPoseSample")
        if self.pose.body_id != self.body_id:
            raise ValueError("pose body identity differs from projection")

        step_values = (
            self.last_physical_step_id,
            self.last_physical_step_source_tick,
            self.environment_revision,
            self.solver_config_revision,
        )
        if all(value is None for value in step_values):
            if self.pose.sample_kind == "physics_step":
                raise ValueError(
                    "physics-step pose sample requires a physical-step correlation"
                )
            if self.physical_step_correlation is not None:
                raise ValueError("initial projection cannot carry a physical-step correlation")
            return
        if any(value is None for value in step_values):
            raise ValueError("physical-step projection correlation must be complete")
        assert self.last_physical_step_id is not None
        assert self.last_physical_step_source_tick is not None
        assert self.environment_revision is not None
        assert self.solver_config_revision is not None
        for name in (
            "last_physical_step_id",
            "environment_revision",
            "solver_config_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{name} must be a non-empty string when a step is present"
                )
            object.__setattr__(self, name, value.strip())
        if (
            isinstance(self.last_physical_step_source_tick, bool)
            or not isinstance(self.last_physical_step_source_tick, int)
            or self.last_physical_step_source_tick < 0
            or self.last_physical_step_source_tick + 1 != self.causal_tick
        ):
            raise ValueError(
                "physical-step source tick must immediately precede projection tick"
            )
        if (
            self.pose.sample_kind != "physics_step"
            or self.pose.sample_value != self.last_physical_step_id
        ):
            raise ValueError(
                "pose sample does not identify the projected physical step"
            )
        correlation = self.physical_step_correlation
        if not isinstance(correlation, PhysicalStepCorrelation):
            raise ValueError("physical-step correlation record is required")
        if (
            correlation.world_id != self.world_id
            or correlation.causal_tick != self.last_physical_step_source_tick
            or correlation.physical_step_id != self.last_physical_step_id
            or correlation.body_id != self.body_id
            or correlation.embodiment_episode_id != self.embodiment_episode_id
            or correlation.morphology_revision != self.morphology_revision
            or correlation.environment_revision != self.environment_revision
            or correlation.solver_config_revision != self.solver_config_revision
        ):
            raise ValueError("projection identity/revisions differ from physical-step correlation")


__all__ = [
    "BodyPoseObservationProjection",
    "BodyPoseSample",
    "PhysicalStepCorrelation",
]
