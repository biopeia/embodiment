"""Projection of owner-issued opaque motor commands to physical ports.

The interfaces below are structural. Embodiment does not import Organism's
private command/surface implementations at runtime; the inputs are validated
against the small fields required at this boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from embodiment.checkpoint import EmbodimentCheckpoint
from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec


class MotorCommandLike(Protocol):
    """Minimal structural view of the provenance-bearing owner command."""

    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    channels: tuple[tuple[str, float], ...]
    issued_at_tick: int
    embodiment_id: str | None


class ActuatorChannelLike(Protocol):
    """Command range for one opaque actuator channel."""

    actuator_id: str
    available: bool
    command_min: float
    neutral: float
    command_max: float


class ActuatorSurfaceLike(Protocol):
    """Minimal structural view of the opaque surface supplied by Embodiment."""

    contract_fingerprint: str
    channels: tuple[ActuatorChannelLike, ...]
    actuator_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhysicalActuationInput:
    """Complete physical-port vector plus the command lineage that produced it.

    `channels` follows `ArticulatedBodySpec.effector_ids()` order. Its values
    are the opaque requested activations, not forces or delivered actuator
    work. A solver adapter may consume the vector, but this type does not run
    a solver or accept any result into authoritative body state.
    """

    body_id: str
    embodiment_id: str
    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    issued_at_tick: int
    channels: tuple[tuple[str, float], ...]
    zeroed_missing_effector_ids: tuple[str, ...]


def project_motor_command(
    command: MotorCommandLike,
    surface: ActuatorSurfaceLike,
    spec: ArticulatedBodySpec,
    *,
    body_pose: BodyPoseSample,
    embodiment_checkpoint: EmbodimentCheckpoint,
    expected_embodiment_id: str,
) -> PhysicalActuationInput:
    """Check owner provenance and map opaque actuator IDs to physical ports.

    The exact surface cardinality is required before positional mapping. The
    command must name this explicitly supplied embodiment identity, while the
    body's pose identity must agree with the owner checkpoint. This function
    does not assume that checkpoint.episode_id and command.embodiment_id share
    semantics; the caller supplies their validated binding. The source
    Physics3D implementation executes omitted physical ports as zero; this
    projection therefore explicitly zero-fills omitted command channels.
    """

    command_id = _required_text(command.command_id, "command_id")
    commitment_id = _required_text(command.commitment_id, "commitment_id")
    controller_id = _required_text(command.controller_id, "controller_id")
    fingerprint = _required_text(command.surface_fingerprint, "surface_fingerprint")
    surface_fingerprint = _required_text(surface.contract_fingerprint, "surface fingerprint")
    if fingerprint != surface_fingerprint:
        raise ValueError("motor command targets a different actuator surface")

    checkpoint_body_id = _required_text(embodiment_checkpoint.body_id, "checkpoint body_id")
    expected_embodiment_id = _required_text(expected_embodiment_id, "expected_embodiment_id")
    body_id = _required_text(body_pose.body_id, "pose body_id")
    if body_id != checkpoint_body_id:
        raise ValueError("physical pose body identity does not match Embodiment checkpoint")
    command_embodiment_id = command.embodiment_id
    if not isinstance(command_embodiment_id, str) or not command_embodiment_id:
        raise ValueError("motor command must name its embodiment identity")
    if command_embodiment_id != expected_embodiment_id:
        raise ValueError("motor command targets a different embodiment identity")

    issued_at_tick = command.issued_at_tick
    if isinstance(issued_at_tick, bool) or not isinstance(issued_at_tick, int) or issued_at_tick < 0:
        raise ValueError("issued_at_tick must be a non-negative causal tick")

    surface_channels = tuple(surface.channels)
    actuator_ids = tuple(surface.actuator_ids)
    channel_ids = tuple(channel.actuator_id for channel in surface_channels)
    if channel_ids != actuator_ids:
        raise ValueError("surface channel order disagrees with actuator_ids")
    for channel in surface_channels:
        _validate_surface_channel(channel)
    effector_ids = tuple(spec.effector_ids())
    if len(actuator_ids) != len(effector_ids):
        raise ValueError("physical body effector surface must exactly match motor constitution")
    if any(not isinstance(value, str) or not value for value in actuator_ids):
        raise ValueError("actuator surface ids must be non-empty strings")
    if len(set(actuator_ids)) != len(actuator_ids):
        raise ValueError("actuator surface ids must be unique")

    command_values: dict[str, float] = {}
    for actuator_id, raw_activation in command.channels:
        if not isinstance(actuator_id, str) or not actuator_id:
            raise ValueError("motor command channel ids must be non-empty strings")
        if actuator_id in command_values:
            raise ValueError("motor command channels must be unique")
        if actuator_id not in actuator_ids:
            raise ValueError("motor command contains an actuator outside the current surface")
        if isinstance(raw_activation, bool) or not isinstance(raw_activation, (int, float)):
            raise ValueError("motor activation must be numeric")
        activation = float(raw_activation)
        if not math.isfinite(activation) or not 0.0 <= activation <= 1.0:
            raise ValueError("motor activation must be finite and within [0, 1]")
        channel = surface_channels[actuator_ids.index(actuator_id)]
        if not channel.available:
            raise ValueError("motor command targets an unavailable actuator")
        if activation < channel.command_min or activation > channel.command_max:
            raise ValueError("motor activation is outside the actuator command range")
        command_values[actuator_id] = activation

    # The established CURRENT adapter maps the ordered opaque command surface
    # to the ordered physical ports only after confirming equal cardinality.
    channels = tuple(
        (effector_id, command_values.get(actuator_id, 0.0))
        for actuator_id, effector_id in zip(actuator_ids, effector_ids)
    )
    zeroed = tuple(
        effector_id
        for actuator_id, effector_id in zip(actuator_ids, effector_ids)
        if actuator_id not in command_values
    )
    competence_id = command.competence_id
    if competence_id is not None and (not isinstance(competence_id, str) or not competence_id):
        raise ValueError("competence_id must be a non-empty string or None")

    return PhysicalActuationInput(
        body_id=body_id,
        embodiment_id=expected_embodiment_id,
        command_id=command_id,
        commitment_id=commitment_id,
        controller_id=controller_id,
        competence_id=competence_id,
        surface_fingerprint=fingerprint,
        issued_at_tick=issued_at_tick,
        channels=channels,
        zeroed_missing_effector_ids=zeroed,
    )


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _validate_surface_channel(channel: ActuatorChannelLike) -> None:
    """Recheck the surface value contract at this structural boundary."""

    if not isinstance(channel.available, bool):
        raise ValueError("actuator availability must be boolean")

    values = (channel.command_min, channel.neutral, channel.command_max)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("actuator command range values must be numeric")
    minimum, neutral, maximum = (float(value) for value in values)
    if not all(math.isfinite(value) for value in (minimum, neutral, maximum)):
        raise ValueError("actuator command range values must be finite")
    if not 0.0 <= minimum <= neutral <= maximum <= 1.0:
        raise ValueError(
            "actuator command contract must satisfy 0 <= min <= neutral <= max <= 1"
        )


__all__ = [
    "ActuatorChannelLike",
    "ActuatorSurfaceLike",
    "MotorCommandLike",
    "PhysicalActuationInput",
    "project_motor_command",
]
