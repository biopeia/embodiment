"""Stable Embodiment-owned receptor attachments and sample-point projection.

This module describes physical receptor identity and location only. It assigns
no meaning to any sampled environmental value and does not authorize World
causality.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import math
from typing import Protocol

from embodiment.physics3d.physical_transition import EmbodimentPhysicalState


class ReceptorWorldStepContext(Protocol):
    """Structural source-step view; callers supply the World-issued context."""

    world_id: str
    source_causal_tick: int
    physical_step_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str


@dataclass(frozen=True, slots=True)
class EmbodimentReceptor:
    """A receptor attached to a stable body frame for one morphology revision.

    ``position_in_body_frame_m`` is expressed in metres in ``body_frame``.
    ``receptor_id`` is the identity; collection order and solver-local IDs have
    no authority.
    """

    receptor_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    body_frame: str
    position_in_body_frame_m: tuple[float, float, float]

    def __post_init__(self) -> None:
        for name in (
            "receptor_id", "body_id", "embodiment_episode_id",
            "morphology_revision", "body_frame",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        point = self.position_in_body_frame_m
        if not isinstance(point, tuple) or len(point) != 3 or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in point
        ):
            raise ValueError("position_in_body_frame_m must contain three finite metre values")
        object.__setattr__(self, "position_in_body_frame_m", tuple(float(value) for value in point))


@dataclass(frozen=True, slots=True)
class ReceptorSamplePoint:
    """Embodiment-projected sample location at a World physical step's source cut."""

    receptor_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    world_id: str
    source_causal_tick: int
    physical_step_id: str
    frame_id: str
    position_m: tuple[float, float, float]


def project_receptor_sample_point(
    receptor: EmbodimentReceptor,
    state: EmbodimentPhysicalState,
    world_step: ReceptorWorldStepContext,
) -> ReceptorSamplePoint:
    """Resolve an attached receptor into the declared reference frame.

    Owner state must match the World context's source cut. This checks local
    correlation but is not authentication of a caller-supplied context.
    """
    if not isinstance(receptor, EmbodimentReceptor):
        raise ValueError("receptor must be EmbodimentReceptor")
    if not isinstance(state, EmbodimentPhysicalState):
        raise ValueError("state must be EmbodimentPhysicalState")
    for name in ("world_id", "physical_step_id", "body_id", "embodiment_episode_id", "morphology_revision"):
        value = getattr(world_step, name, None)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"World physical-step {name} must be a non-empty string")
    if type(getattr(world_step, "source_causal_tick", None)) is not int or world_step.source_causal_tick < 0:
        raise ValueError("World physical-step source_causal_tick must be a non-negative integer")
    if (
        receptor.body_id != state.body_id
        or receptor.embodiment_episode_id != state.embodiment_episode_id
        or receptor.morphology_revision != state.morphology_revision
    ):
        raise ValueError("receptor identity or morphology differs from active Embodiment state")
    if (
        state.world_id != world_step.world_id
        or state.causal_tick != world_step.source_causal_tick
        or state.body_id != world_step.body_id
        or state.embodiment_episode_id != world_step.embodiment_episode_id
        or state.morphology_revision != world_step.morphology_revision
    ):
        raise ValueError("World physical-step context differs from Embodiment source state")
    if receptor.body_frame != state.pose.body_frame:
        raise ValueError("receptor attachment frame differs from active body frame")

    rotated = _rotate_xyzw(state.pose.orientation_xyzw, receptor.position_in_body_frame_m)
    point = tuple(origin + offset for origin, offset in zip(state.pose.position_m, rotated))
    return ReceptorSamplePoint(
        receptor_id=receptor.receptor_id,
        body_id=state.body_id,
        embodiment_episode_id=state.embodiment_episode_id,
        morphology_revision=state.morphology_revision,
        world_id=state.world_id,
        source_causal_tick=state.causal_tick,
        physical_step_id=world_step.physical_step_id,
        frame_id=state.pose.reference_frame,
        position_m=point,
    )


def receptors_by_id(receptors: Iterable[EmbodimentReceptor]) -> dict[str, EmbodimentReceptor]:
    """Index receptor descriptors by stable identity, rejecting ambiguity."""
    result: dict[str, EmbodimentReceptor] = {}
    for receptor in receptors:
        if not isinstance(receptor, EmbodimentReceptor):
            raise ValueError("all receptor entries must be EmbodimentReceptor")
        if receptor.receptor_id in result:
            raise ValueError("receptor_id values must be unique")
        result[receptor.receptor_id] = receptor
    return result


def _rotate_xyzw(
    quaternion: tuple[float, float, float, float],
    vector: tuple[float, float, float],
) -> tuple[float, float, float]:
    x, y, z, w = quaternion
    vx, vy, vz = vector
    # Equivalent to q * (v, 0) * conjugate(q) for a unit xyzw quaternion.
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    )


__all__ = [
    "EmbodimentReceptor",
    "ReceptorSamplePoint",
    "ReceptorWorldStepContext",
    "project_receptor_sample_point",
    "receptors_by_id",
]
