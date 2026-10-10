"""Revision-bound joint-torque command projection owned by Embodiment.

This is a numerical input candidate only. It does not execute a solver, mutate
somatic state, or authorize a World commit. Joint names are the stable joint
identities declared by the active Embodiment morphology; tuple order and
solver-native IDs have no authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Protocol

from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology


@dataclass(frozen=True, slots=True)
class JointTorqueChannelBinding:
    actuator_id: str
    joint_id: str
    axis: tuple[float, float, float]
    available: bool = True

    def __post_init__(self) -> None:
        _text(self.actuator_id, "actuator_id")
        _text(self.joint_id, "joint_id")
        if type(self.available) is not bool:
            raise ValueError("joint torque availability must be boolean")
        axis = _vector(self.axis, "axis")
        if not math.isclose(math.sqrt(sum(x * x for x in axis)), 1.0, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError("joint torque axis must be a unit vector")
        object.__setattr__(self, "axis", axis)

    def _payload(self) -> dict[str, object]:
        return {"actuator_id": self.actuator_id, "joint_id": self.joint_id,
                "axis": list(self.axis), "available": self.available}


@dataclass(frozen=True, slots=True)
class EmbodimentJointTorqueBinding:
    binding_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    source_surface_fingerprint: str
    channels: tuple[JointTorqueChannelBinding, ...]

    SCHEMA_VERSION = 1

    def __post_init__(self) -> None:
        for name in ("binding_id", "body_id", "embodiment_episode_id", "morphology_revision", "source_surface_fingerprint"):
            _text(getattr(self, name), name)
        channels = tuple(self.channels)
        if not channels or any(not isinstance(item, JointTorqueChannelBinding) for item in channels):
            raise ValueError("joint torque binding requires channels")
        if len({item.actuator_id for item in channels}) != len(channels):
            raise ValueError("joint torque actuator ids must be unique")
        if len({item.joint_id for item in channels}) != len(channels):
            raise ValueError("joint torque joint ids must be unique")
        object.__setattr__(self, "channels", channels)

    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "binding_id": self.binding_id,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "source_surface_fingerprint": self.source_surface_fingerprint,
            "channels": [c._payload() for c in sorted(self.channels, key=lambda item: item.actuator_id)],
        }

    @property
    def fingerprint(self) -> str:
        data = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_checkpoint(self) -> dict[str, object]:
        return self._payload() | {"fingerprint": self.fingerprint}

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_checkpoint(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "EmbodimentJointTorqueBinding":
        try:
            raw = json.loads(encoded)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid joint torque binding JSON") from exc
        top = {"schema_version", "binding_id", "body_id", "embodiment_episode_id", "morphology_revision", "source_surface_fingerprint", "channels", "fingerprint"}
        channel_fields = {"actuator_id", "joint_id", "axis", "available"}
        if not isinstance(raw, dict) or set(raw) != top or type(raw.get("schema_version")) is not int or raw["schema_version"] != cls.SCHEMA_VERSION:
            raise ValueError("invalid joint torque binding checkpoint fields or schema")
        if not isinstance(raw["channels"], list) or any(not isinstance(c, dict) or set(c) != channel_fields for c in raw["channels"]):
            raise ValueError("invalid joint torque binding channel fields")
        try:
            binding = cls(
                raw["binding_id"], raw["body_id"], raw["embodiment_episode_id"], raw["morphology_revision"],
                raw["source_surface_fingerprint"], tuple(JointTorqueChannelBinding(**c) for c in raw["channels"]),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid joint torque binding checkpoint") from exc
        if raw["fingerprint"] != binding.fingerprint:
            raise ValueError("joint torque binding fingerprint mismatch")
        return binding


@dataclass(frozen=True, slots=True)
class JointTorqueInputChannel:
    """Typed upstream physical request; no unit inference from raw floats."""

    actuator_id: str
    value: float
    quantity: str
    unit: str

    def __post_init__(self) -> None:
        _text(self.actuator_id, "actuator_id")
        if self.quantity != "joint_torque":
            raise ValueError("joint torque input quantity must be joint_torque")
        if self.unit != "N*m":
            raise ValueError("joint torque input unit must be N*m")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)) or not math.isfinite(float(self.value)):
            raise ValueError("joint torque input value must be finite")


@dataclass(frozen=True, slots=True)
class JointTorqueRequest:
    """Owner-boundary request with explicit per-channel physical semantics."""

    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    surface_fingerprint: str
    channels: tuple[JointTorqueInputChannel, ...]
    issued_at_tick: int
    embodiment_id: str

    def __post_init__(self) -> None:
        for name in ("command_id", "commitment_id", "controller_id", "surface_fingerprint", "embodiment_id"):
            _text(getattr(self, name), name)
        if isinstance(self.issued_at_tick, bool) or not isinstance(self.issued_at_tick, int) or self.issued_at_tick < 0:
            raise ValueError("issued_at_tick must be a non-negative causal tick")
        channels = tuple(self.channels)
        if any(not isinstance(channel, JointTorqueInputChannel) for channel in channels):
            raise ValueError("joint torque request requires typed input channels")
        if len({channel.actuator_id for channel in channels}) != len(channels):
            raise ValueError("joint torque request actuator ids must be unique")
        if self.competence_id is not None:
            _text(self.competence_id, "competence_id")
        object.__setattr__(self, "channels", channels)


@dataclass(frozen=True, slots=True)
class JointTorqueCommand:
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    joint_id: str
    joint_parent_link_id: str
    joint_child_link_id: str
    axis: tuple[float, float, float]
    axis_frame_id: str
    positive_direction: str
    torque_nm: float
    quantity: str
    unit: str
    minimum_nm: float
    neutral_nm: float
    maximum_nm: float


@dataclass(frozen=True, slots=True)
class JointTorqueCandidate:
    binding_id: str
    binding_fingerprint: str
    command_id: str
    commitment_id: str
    controller_id: str
    competence_id: str | None
    issued_at_tick: int
    channels: tuple[JointTorqueCommand, ...]


def project_joint_torque_command(
    command: JointTorqueRequest,
    binding: EmbodimentJointTorqueBinding,
    active_morphology: ActiveArticulatedMorphology,
) -> JointTorqueCandidate:
    """Validate a sparse actuator command against active joints and emit N·m."""
    if not isinstance(binding, EmbodimentJointTorqueBinding):
        raise ValueError("joint torque projection requires an EmbodimentJointTorqueBinding")
    if not isinstance(active_morphology, ActiveArticulatedMorphology):
        raise ValueError("joint torque projection requires active Embodiment morphology")
    if not isinstance(command, JointTorqueRequest):
        raise ValueError("joint torque projection requires explicitly typed JointTorqueRequest")
    if command.surface_fingerprint != binding.source_surface_fingerprint:
        raise ValueError("motor command targets a different actuator surface")
    if command.embodiment_id != active_morphology.embodiment_episode_id:
        raise ValueError("motor command targets a different embodiment episode")
    if (binding.body_id, binding.embodiment_episode_id, binding.morphology_revision) != (
        active_morphology.body_id, active_morphology.embodiment_episode_id, active_morphology.morphology_revision
    ):
        raise ValueError("joint torque binding does not match active body, episode and morphology revision")
    joints = {joint.name: joint for joint in active_morphology.spec.joint_specs}
    topology = {joint.joint_name: joint for joint in active_morphology.spec.joint_topology}
    by_actuator: dict[str, JointTorqueChannelBinding] = {}
    for channel in binding.channels:
        joint = joints.get(channel.joint_id)
        if joint is None:
            raise ValueError("binding references a joint outside active morphology")
        if tuple(joint.axis) != channel.axis:
            raise ValueError("binding axis differs from active morphology joint axis")
        if channel.actuator_id in by_actuator:
            raise ValueError("joint torque actuator ids must be unique")
        by_actuator[channel.actuator_id] = channel
    if set(c.joint_id for c in binding.channels) != set(joints):
        raise ValueError("joint torque binding must explicitly cover every active joint")

    seen: set[str] = set()
    output: list[JointTorqueCommand] = []
    for request_channel in command.channels:
        actuator_id = request_channel.actuator_id
        if actuator_id in seen:
            raise ValueError("motor command channels must be unique")
        seen.add(actuator_id)
        channel = by_actuator.get(actuator_id)
        if channel is None:
            raise ValueError("motor command contains an actuator outside the current binding")
        if not channel.available:
            raise ValueError("motor command targets an unavailable actuator")
        if request_channel.quantity != "joint_torque" or request_channel.unit != "N*m":
            raise ValueError("joint torque request quantity/unit mismatch")
        joint = joints[channel.joint_id]
        torque = float(request_channel.value)
        bound = float(joint.max_motor_torque)
        if torque < -bound or torque > bound:
            raise ValueError("joint torque is outside the declared morphology range")
        joint_topology = topology[channel.joint_id]
        output.append(JointTorqueCommand(
            active_morphology.body_id, active_morphology.embodiment_episode_id,
            active_morphology.morphology_revision, channel.joint_id,
            joint_topology.parent_link, joint_topology.child_link, channel.axis,
            f"joint-frame:{channel.joint_id}@{active_morphology.morphology_revision}",
            "right_hand_about_declared_axis", torque, "joint_torque", "N*m", -bound, 0.0, bound,
        ))
    return JointTorqueCandidate(
        binding.binding_id, binding.fingerprint, command.command_id, command.commitment_id,
        command.controller_id, command.competence_id, command.issued_at_tick,
        tuple(sorted(output, key=lambda item: item.joint_id)),
    )


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return value


def _vector(value: object, field: str) -> tuple[float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{field} must contain three finite values")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in value):
        raise ValueError(f"{field} must contain three finite values")
    result = tuple(float(x) for x in value)
    if not all(math.isfinite(x) for x in result):
        raise ValueError(f"{field} must contain three finite values")
    return result  # type: ignore[return-value]


__all__ = [
    "EmbodimentJointTorqueBinding", "JointTorqueCandidate", "JointTorqueChannelBinding",
    "JointTorqueCommand", "JointTorqueInputChannel", "JointTorqueRequest",
    "project_joint_torque_command",
]
