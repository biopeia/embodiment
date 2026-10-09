"""Explicit candidate projection from owner motor commands to effectors.

This module defines structural inputs because Organism owns its command types
and Embodiment owns the active morphology. Stable effector identifiers, not
tuple order, establish the association. The result is an input candidate only:
it neither invokes a solver nor mutates authoritative body state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Protocol

from embodiment.checkpoint import EmbodimentCheckpoint
from embodiment.observation import BodyPoseSample


SaturationPolicy = Literal["reject"]


class MotorCommandLike(Protocol):
    """Organism-issued command bound to its current embodiment episode."""

    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    channels: tuple[tuple[str, float], ...]
    issued_at_tick: int
    embodiment_id: str | None


class EffectorContractLike(Protocol):
    """Active morphology's explicit physical quantity contract per effector."""

    effector_id: str
    quantity: str
    unit: str
    minimum: float
    neutral: float
    maximum: float
    saturation: SaturationPolicy


class MorphologyLike(Protocol):
    """Owner-selected active body and its versioned stable effector contracts."""

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    effectors: tuple[EffectorContractLike, ...]


class ActuatorChannelLike(Protocol):
    """An explicit actuator-to-effector association and command contract."""

    actuator_id: str
    effector_id: str
    command_kind: str
    quantity: str
    unit: str
    minimum: float
    neutral: float
    maximum: float
    saturation: SaturationPolicy
    available: bool


class ActuatorSurfaceLike(Protocol):
    """Surface bound to one exact active morphology revision."""

    contract_fingerprint: str
    morphology_revision: str
    channels: tuple[ActuatorChannelLike, ...]


@dataclass(frozen=True, slots=True)
class PhysicalActuationCandidate:
    """Sparse commands addressed by stable, fully-contextual effector channels.

    Each physical channel repeats its body, episode, morphology revision,
    effector, command semantics and units. Omitted channels stay absent.
    Out-of-range values are rejected, never clipped or saturated implicitly.
    This candidate is not a delivered force/work result or body-state update.
    """

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    command_kind: str
    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    issued_at_tick: int
    channels: tuple[PhysicalActuationChannel, ...]


@dataclass(frozen=True, slots=True)
class PhysicalActuationChannel:
    """One sparse physical command with explicit identity and units."""

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    effector_id: str
    command_kind: str
    value: float
    quantity: str
    unit: str
    minimum: float
    neutral: float
    maximum: float
    saturation: SaturationPolicy


def project_motor_command(
    command: MotorCommandLike,
    surface: ActuatorSurfaceLike,
    active_morphology: MorphologyLike,
    *,
    body_pose: BodyPoseSample,
    embodiment_checkpoint: EmbodimentCheckpoint,
    command_kind: str,
) -> PhysicalActuationCandidate:
    """Validate provenance/contracts and return sparse effector commands.

    Surface channel entries bind opaque command actuator ids to stable
    morphology effector ids explicitly. Neither command nor output order has
    any mapping authority. Missing channels mean *no command*, not zero,
    neutral, hold, or another inferred physical action.
    """

    command_id = _required_text(command.command_id, "command_id")
    commitment_id = _required_text(command.commitment_id, "commitment_id")
    controller_id = _required_text(command.controller_id, "controller_id")
    fingerprint = _required_text(command.surface_fingerprint, "surface_fingerprint")
    if fingerprint != _required_text(surface.contract_fingerprint, "surface fingerprint"):
        raise ValueError("motor command targets a different actuator surface")

    body_id = _required_text(active_morphology.body_id, "active morphology body_id")
    episode_id = _required_text(
        active_morphology.embodiment_episode_id, "active morphology embodiment_episode_id"
    )
    revision = _required_text(active_morphology.morphology_revision, "morphology_revision")
    if _required_text(body_pose.body_id, "pose body_id") != body_id:
        raise ValueError("physical pose body identity does not match active morphology")
    if _required_text(embodiment_checkpoint.body_id, "checkpoint body_id") != body_id:
        raise ValueError("checkpoint body identity does not match active morphology")
    if _required_text(embodiment_checkpoint.episode_id, "checkpoint episode_id") != episode_id:
        raise ValueError("checkpoint episode identity does not match active morphology")
    if _required_text(command.embodiment_id, "command embodiment_id") != episode_id:
        raise ValueError("motor command targets a different embodiment episode")
    if _required_text(surface.morphology_revision, "surface morphology_revision") != revision:
        raise ValueError("actuator surface targets a different morphology revision")
    command_kind = _required_text(command_kind, "command_kind")

    issued_at_tick = command.issued_at_tick
    if isinstance(issued_at_tick, bool) or not isinstance(issued_at_tick, int) or issued_at_tick < 0:
        raise ValueError("issued_at_tick must be a non-negative causal tick")

    morphology_effectors = tuple(active_morphology.effectors)
    channels = tuple(surface.channels)
    effectors_by_id = {}
    for effector in morphology_effectors:
        _validate_effector_contract(effector)
        effector_id = _required_text(effector.effector_id, "effector_id")
        if effector_id in effectors_by_id:
            raise ValueError("active morphology effector ids must be unique")
        effectors_by_id[effector_id] = effector

    actuator_ids: set[str] = set()
    surface_by_actuator = {}
    covered_effector_ids: set[str] = set()
    for channel in channels:
        actuator_id = _required_text(channel.actuator_id, "actuator_id")
        effector_id = _required_text(channel.effector_id, "surface effector_id")
        if actuator_id in actuator_ids:
            raise ValueError("surface actuator ids must be unique")
        actuator_ids.add(actuator_id)
        if effector_id in covered_effector_ids:
            raise ValueError("surface effector ids must be unique")
        covered_effector_ids.add(effector_id)
        if effector_id not in effectors_by_id:
            raise ValueError("surface references an effector outside the active morphology")
        if not isinstance(channel.available, bool):
            raise ValueError("actuator availability must be boolean")
        _validate_effector_contract(channel)
        if _required_text(channel.command_kind, "surface command_kind") != command_kind:
            raise ValueError("actuator surface command_kind does not match command")
        active = effectors_by_id[effector_id]
        if _contract_tuple(channel) != _contract_tuple(active):
            raise ValueError("surface effector contract differs from active morphology")
        surface_by_actuator[actuator_id] = channel
    if covered_effector_ids != set(effectors_by_id):
        raise ValueError("actuator surface must explicitly cover every active morphology effector")

    values_by_effector: dict[str, float] = {}
    seen_actuators: set[str] = set()
    for actuator_id, raw_value in command.channels:
        actuator_id = _required_text(actuator_id, "command actuator_id")
        if actuator_id in seen_actuators:
            raise ValueError("motor command channels must be unique")
        seen_actuators.add(actuator_id)
        channel = surface_by_actuator.get(actuator_id)
        if channel is None:
            raise ValueError("motor command contains an actuator outside the current surface")
        if not channel.available:
            raise ValueError("motor command targets an unavailable actuator")
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise ValueError("motor command value must be numeric")
        value = float(raw_value)
        if not math.isfinite(value):
            raise ValueError("motor command value must be finite")
        if value < channel.minimum or value > channel.maximum:
            if channel.saturation == "reject":
                raise ValueError("motor command value is outside the declared effector range")
        values_by_effector[channel.effector_id] = value

    competence_id = command.competence_id
    if competence_id is not None and (not isinstance(competence_id, str) or not competence_id):
        raise ValueError("competence_id must be a non-empty string or None")

    physical_channels = tuple(
        PhysicalActuationChannel(
            body_id=body_id,
            embodiment_episode_id=episode_id,
            morphology_revision=revision,
            effector_id=effector_id,
            command_kind=command_kind,
            value=value,
            quantity=effectors_by_id[effector_id].quantity,
            unit=effectors_by_id[effector_id].unit,
            minimum=float(effectors_by_id[effector_id].minimum),
            neutral=float(effectors_by_id[effector_id].neutral),
            maximum=float(effectors_by_id[effector_id].maximum),
            saturation=effectors_by_id[effector_id].saturation,
        )
        for effector_id, value in sorted(values_by_effector.items())
    )
    return PhysicalActuationCandidate(
        body_id=body_id,
        embodiment_episode_id=episode_id,
        morphology_revision=revision,
        command_kind=command_kind,
        command_id=command_id,
        commitment_id=commitment_id,
        controller_id=controller_id,
        competence_id=competence_id,
        surface_fingerprint=fingerprint,
        issued_at_tick=issued_at_tick,
        channels=physical_channels,
    )


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _validate_effector_contract(contract: EffectorContractLike) -> None:
    _required_text(contract.effector_id, "effector_id")
    _required_text(contract.quantity, "effector quantity")
    _required_text(contract.unit, "effector unit")
    values = (contract.minimum, contract.neutral, contract.maximum)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("effector range and neutral values must be numeric")
    minimum, neutral, maximum = (float(value) for value in values)
    if not all(math.isfinite(value) for value in (minimum, neutral, maximum)):
        raise ValueError("effector range and neutral values must be finite")
    if not minimum <= neutral <= maximum:
        raise ValueError("effector contract must satisfy minimum <= neutral <= maximum")
    if contract.saturation != "reject":
        raise ValueError("unsupported saturation policy; only explicit reject is supported")


def _contract_tuple(contract: EffectorContractLike) -> tuple[object, ...]:
    return (
        contract.quantity,
        contract.unit,
        float(contract.minimum),
        float(contract.neutral),
        float(contract.maximum),
        contract.saturation,
    )


__all__ = [
    "ActuatorChannelLike",
    "ActuatorSurfaceLike",
    "EffectorContractLike",
    "MorphologyLike",
    "MotorCommandLike",
    "PhysicalActuationCandidate",
    "PhysicalActuationChannel",
    "SaturationPolicy",
    "project_motor_command",
]
