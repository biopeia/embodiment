"""Embodiment-owned operational observation values.

These types define domain semantics without depending on Lab or transport.
They are not wire records and do not authorize publication by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _vec3(value: tuple[float, float, float], *, name: str) -> tuple[float, float, float]:
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


__all__ = ["BodyPoseSample"]
