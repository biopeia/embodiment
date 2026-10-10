"""Embodiment-owned, revision-bound actuator channel binding.

The binding is immutable and has a strict checkpoint representation. Its
fingerprint identifies the complete binding content; it is not a solver or
World authorization token.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Literal

SaturationPolicy = Literal["reject"]


@dataclass(frozen=True, slots=True)
class ActuatorChannelBinding:
    actuator_id: str
    effector_id: str
    command_kind: str
    quantity: str
    unit: str
    minimum: float
    neutral: float
    maximum: float
    saturation: SaturationPolicy
    available: bool = True

    def __post_init__(self) -> None:
        for field_name in ("actuator_id", "effector_id", "command_kind", "quantity", "unit"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if type(self.available) is not bool:
            raise ValueError("actuator availability must be boolean")
        values = (self.minimum, self.neutral, self.maximum)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise ValueError("effector range and neutral values must be numeric")
        minimum, neutral, maximum = (float(value) for value in values)
        if not all(math.isfinite(value) for value in (minimum, neutral, maximum)):
            raise ValueError("effector range and neutral values must be finite")
        if not minimum <= neutral <= maximum:
            raise ValueError("effector contract must satisfy minimum <= neutral <= maximum")
        if self.saturation != "reject":
            raise ValueError("unsupported saturation policy; only explicit reject is supported")
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "neutral", neutral)
        object.__setattr__(self, "maximum", maximum)

    def _payload(self) -> dict[str, object]:
        return {
            "actuator_id": self.actuator_id,
            "effector_id": self.effector_id,
            "command_kind": self.command_kind,
            "quantity": self.quantity,
            "unit": self.unit,
            "minimum": self.minimum,
            "neutral": self.neutral,
            "maximum": self.maximum,
            "saturation": self.saturation,
            "available": self.available,
        }


@dataclass(frozen=True, slots=True)
class EmbodimentActuatorBinding:
    """One Embodiment-owned actuator map for an exact body episode/morphology."""

    binding_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    source_surface_fingerprint: str
    channels: tuple[ActuatorChannelBinding, ...]

    SCHEMA_VERSION = 1

    def __post_init__(self) -> None:
        for field_name in (
            "binding_id", "body_id", "embodiment_episode_id", "morphology_revision",
            "source_surface_fingerprint",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        channels = tuple(self.channels)
        if not channels or any(not isinstance(channel, ActuatorChannelBinding) for channel in channels):
            raise ValueError("binding channels must be a non-empty tuple of ActuatorChannelBinding")
        actuator_ids = [channel.actuator_id for channel in channels]
        effector_ids = [channel.effector_id for channel in channels]
        if len(set(actuator_ids)) != len(actuator_ids):
            raise ValueError("binding actuator ids must be unique")
        if len(set(effector_ids)) != len(effector_ids):
            raise ValueError("binding effector ids must be unique")
        object.__setattr__(self, "channels", channels)

    @property
    def fingerprint(self) -> str:
        """SHA-256 identity of the canonical versioned binding content."""
        encoded = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def to_checkpoint(self) -> dict[str, object]:
        """Return the strict owner checkpoint payload for this binding."""
        return self._payload() | {"fingerprint": self.fingerprint}

    def to_bytes(self) -> bytes:
        """Serialize a deterministic, hash-verifiable checkpoint payload."""
        return json.dumps(
            self.to_checkpoint(), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    def _payload(self) -> dict[str, object]:
        return {
            "schema_version": self.SCHEMA_VERSION,
            "binding_id": self.binding_id,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "source_surface_fingerprint": self.source_surface_fingerprint,
            "channels": [channel._payload() for channel in sorted(self.channels, key=lambda item: item.actuator_id)],
        }

    @classmethod
    def restore(cls, payload: object) -> "EmbodimentActuatorBinding":
        """Restore only the exact supported schema; unknown fields fail closed."""
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version", "binding_id", "body_id", "embodiment_episode_id",
            "morphology_revision", "source_surface_fingerprint", "channels", "fingerprint",
        }:
            raise ValueError("invalid actuator binding checkpoint fields")
        if type(payload["schema_version"]) is not int or payload["schema_version"] != cls.SCHEMA_VERSION:
            raise ValueError("unsupported actuator binding checkpoint schema")
        raw_channels = payload["channels"]
        if not isinstance(raw_channels, list):
            raise ValueError("invalid actuator binding checkpoint channels")
        channels: list[ActuatorChannelBinding] = []
        fields = {"actuator_id", "effector_id", "command_kind", "quantity", "unit", "minimum", "neutral", "maximum", "saturation", "available"}
        for item in raw_channels:
            if not isinstance(item, dict) or set(item) != fields:
                raise ValueError("invalid actuator binding channel checkpoint fields")
            try:
                channels.append(ActuatorChannelBinding(**item))
            except (TypeError, ValueError) as exc:
                raise ValueError("invalid actuator binding channel checkpoint") from exc
        try:
            binding = cls(
                binding_id=payload["binding_id"], body_id=payload["body_id"],
                embodiment_episode_id=payload["embodiment_episode_id"],
                morphology_revision=payload["morphology_revision"],
                source_surface_fingerprint=payload["source_surface_fingerprint"],
                channels=tuple(channels),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid actuator binding checkpoint") from exc
        if payload["fingerprint"] != binding.fingerprint:
            raise ValueError("actuator binding checkpoint fingerprint mismatch")
        return binding

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "EmbodimentActuatorBinding":
        """Decode and validate a serialized owner checkpoint."""
        if not isinstance(encoded, bytes):
            raise ValueError("actuator binding checkpoint must be bytes")
        try:
            payload: object = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid actuator binding checkpoint JSON") from exc
        return cls.restore(payload)


__all__ = ["ActuatorChannelBinding", "EmbodimentActuatorBinding"]
