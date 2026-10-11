"""Embodiment-owned TARGET composition for the bounded differential fixture.

This module converts opaque Organism actuator activations through an explicit,
body/episode/morphology-bound Embodiment mapping into typed joint-torque input.
It does not execute a solver, adopt body state, or authorize a World commit.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Protocol

from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.joint_torque import (
    EmbodimentJointTorqueBinding,
    JointTorqueInputChannel,
    JointTorqueRequest,
    project_joint_torque_command,
)


class MotorCommandLike(Protocol):
    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    channels: tuple[tuple[str, float], ...]
    issued_at_tick: int
    embodiment_id: str | None


@dataclass(frozen=True, slots=True)
class DifferentialMotorPair:
    """Explicit activation pair and scale for one stable morphology joint."""

    joint_id: str
    positive_actuator_id: str
    negative_actuator_id: str
    scale: float

    def __post_init__(self) -> None:
        for name in ("joint_id", "positive_actuator_id", "negative_actuator_id"):
            _text(getattr(self, name), name)
        if self.positive_actuator_id == self.negative_actuator_id:
            raise ValueError("differential pair actuator ids must be distinct")
        _finite(self.scale, "differential binding scale")
        if self.scale < 0:
            raise ValueError("differential binding scale must be non-negative")

    def _payload(self) -> dict[str, object]:
        return {
            "joint_id": self.joint_id,
            "positive_actuator_id": self.positive_actuator_id,
            "negative_actuator_id": self.negative_actuator_id,
            "scale": self.scale,
        }


@dataclass(frozen=True, slots=True)
class EmbodimentDifferentialMotorBinding:
    """Strict, checkpointable mapping for one active body surface/revision."""

    binding_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    source_surface_fingerprint: str
    pairs: tuple[DifferentialMotorPair, ...]

    SCHEMA_VERSION = 1

    def __post_init__(self) -> None:
        for name in (
            "binding_id", "body_id", "embodiment_episode_id",
            "morphology_revision", "source_surface_fingerprint",
        ):
            _text(getattr(self, name), name)
        pairs = tuple(self.pairs)
        if not pairs or any(not isinstance(pair, DifferentialMotorPair) for pair in pairs):
            raise ValueError("differential motor binding requires explicit pairs")
        if len({pair.joint_id for pair in pairs}) != len(pairs):
            raise ValueError("differential motor joint ids must be unique")
        actuator_ids = [
            actuator_id
            for pair in pairs
            for actuator_id in (pair.positive_actuator_id, pair.negative_actuator_id)
        ]
        if len(set(actuator_ids)) != len(actuator_ids):
            raise ValueError("differential motor actuator ids must be unique across pairs")
        object.__setattr__(self, "pairs", pairs)

    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "binding_id": self.binding_id,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "source_surface_fingerprint": self.source_surface_fingerprint,
            "pairs": [pair._payload() for pair in sorted(self.pairs, key=lambda item: item.joint_id)],
        }

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_checkpoint(self) -> dict[str, object]:
        return self._payload() | {"fingerprint": self.fingerprint}

    def to_bytes(self) -> bytes:
        return json.dumps(
            self.to_checkpoint(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "EmbodimentDifferentialMotorBinding":
        if not isinstance(encoded, bytes):
            raise ValueError("differential motor binding checkpoint must be bytes")
        try:
            raw: object = json.loads(encoded, object_pairs_hook=_object_without_duplicate_keys)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid differential motor binding checkpoint JSON") from exc
        fields = {
            "schema_version", "binding_id", "body_id", "embodiment_episode_id",
            "morphology_revision", "source_surface_fingerprint", "pairs", "fingerprint",
        }
        pair_fields = {"joint_id", "positive_actuator_id", "negative_actuator_id", "scale"}
        if not isinstance(raw, dict) or set(raw) != fields:
            raise ValueError("invalid differential motor binding checkpoint fields")
        if type(raw["schema_version"]) is not int or raw["schema_version"] != cls.SCHEMA_VERSION:
            raise ValueError("unsupported differential motor binding checkpoint schema")
        if not isinstance(raw["pairs"], list) or any(
            not isinstance(pair, dict) or set(pair) != pair_fields for pair in raw["pairs"]
        ):
            raise ValueError("invalid differential motor binding pair checkpoint fields")
        try:
            binding = cls(
                raw["binding_id"], raw["body_id"], raw["embodiment_episode_id"],
                raw["morphology_revision"], raw["source_surface_fingerprint"],
                tuple(DifferentialMotorPair(**pair) for pair in raw["pairs"]),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid differential motor binding checkpoint") from exc
        if raw["fingerprint"] != binding.fingerprint:
            raise ValueError("differential motor binding checkpoint fingerprint mismatch")
        return binding


def compose_differential_motor_command(
    command: MotorCommandLike,
    binding: EmbodimentDifferentialMotorBinding,
    torque_binding: EmbodimentJointTorqueBinding,
    active_morphology: ActiveArticulatedMorphology,
) -> JointTorqueRequest:
    """Compose a MotorCommand into typed N*m channels using explicit binding.

    For each declared pair, ``torque = (positive - negative) *
    morphology.max_motor_torque * binding.scale``. Both channels absent means
    no command; a partial pair is rejected. Values are never clipped.
    """

    if not isinstance(binding, EmbodimentDifferentialMotorBinding):
        raise ValueError("differential composition requires an EmbodimentDifferentialMotorBinding")
    if not isinstance(torque_binding, EmbodimentJointTorqueBinding):
        raise ValueError("differential composition requires an EmbodimentJointTorqueBinding")
    if not isinstance(active_morphology, ActiveArticulatedMorphology):
        raise ValueError("differential composition requires active Embodiment morphology")

    context = (active_morphology.body_id, active_morphology.embodiment_episode_id,
               active_morphology.morphology_revision)
    if (binding.body_id, binding.embodiment_episode_id, binding.morphology_revision) != context:
        raise ValueError("differential binding does not match active body, episode and morphology revision")
    if (torque_binding.body_id, torque_binding.embodiment_episode_id,
        torque_binding.morphology_revision) != context:
        raise ValueError("joint torque binding does not match active body, episode and morphology revision")
    if binding.source_surface_fingerprint != torque_binding.source_surface_fingerprint:
        raise ValueError("differential binding and torque binding target different actuator surfaces")
    surface = _text(command.surface_fingerprint, "command surface fingerprint")
    if surface != binding.source_surface_fingerprint:
        raise ValueError("motor command targets a different actuator surface")
    if command.embodiment_id != active_morphology.embodiment_episode_id:
        raise ValueError("motor command targets a different embodiment episode")

    joint_specs = {joint.name: joint for joint in active_morphology.spec.joint_specs}
    physical_channels = {channel.joint_id: channel for channel in torque_binding.channels}
    if set(physical_channels) != set(joint_specs):
        raise ValueError("joint torque binding must explicitly cover every active joint")
    for pair in binding.pairs:
        if pair.joint_id not in joint_specs:
            raise ValueError("differential binding references a joint outside active morphology")
        if pair.joint_id not in physical_channels:
            raise ValueError("differential binding does not agree with torque binding")

    activations: dict[str, float] = {}
    for channel in command.channels:
        if not isinstance(channel, (tuple, list)) or len(channel) != 2:
            raise ValueError("motor command channel must contain stable actuator id and activation")
        actuator_id = _text(channel[0], "motor command actuator id")
        value = _finite(channel[1], "motor activation")
        if value < 0.0 or value > 1.0:
            raise ValueError("motor activation is outside the declared [0, 1] range")
        if actuator_id in activations:
            raise ValueError("motor command actuator ids must be unique")
        activations[actuator_id] = value
    mapped_ids = {
        actuator_id
        for pair in binding.pairs
        for actuator_id in (pair.positive_actuator_id, pair.negative_actuator_id)
    }
    if set(activations) - mapped_ids:
        raise ValueError("motor command contains an actuator outside the active differential binding")

    output: list[JointTorqueInputChannel] = []
    for pair in sorted(binding.pairs, key=lambda item: item.joint_id):
        positive_present = pair.positive_actuator_id in activations
        negative_present = pair.negative_actuator_id in activations
        if positive_present != negative_present:
            raise ValueError("incomplete differential pair command")
        if not positive_present:
            continue
        joint = joint_specs[pair.joint_id]
        maximum = _finite(joint.max_motor_torque, "morphology max_motor_torque")
        if maximum <= 0:
            raise ValueError("morphology max_motor_torque must be positive")
        signed_effort = activations[pair.positive_actuator_id] - activations[pair.negative_actuator_id]
        torque = signed_effort * maximum * pair.scale
        if not math.isfinite(torque) or torque < -maximum or torque > maximum:
            raise ValueError("mapped torque is outside the declared morphology range")
        output_id = physical_channels[pair.joint_id].actuator_id
        output.append(JointTorqueInputChannel(output_id, torque, "joint_torque", "N*m"))

    request = JointTorqueRequest(
        command_id=_text(command.command_id, "command_id"),
        commitment_id=_text(command.commitment_id, "commitment_id"),
        controller_id=_text(command.controller_id, "controller_id"),
        competence_id=command.competence_id,
        surface_fingerprint=surface,
        channels=tuple(output),
        issued_at_tick=command.issued_at_tick,
        embodiment_id=active_morphology.embodiment_episode_id,
    )
    # Validate the constructed typed request against the active physical binding
    # before publishing it to the World adapter.
    project_joint_torque_command(request, torque_binding, active_morphology)
    return request


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate differential motor binding checkpoint field: {key}")
        result[key] = value
    return result


__all__ = [
    "DifferentialMotorPair", "EmbodimentDifferentialMotorBinding",
    "MotorCommandLike", "compose_differential_motor_command",
]
