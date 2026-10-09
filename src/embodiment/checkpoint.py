"""Owner-scoped persistence composition for a body embodiment episode.

This is a migration-stage format, not a finalized portable World checkpoint.
It composes existing body and metabolism checkpoints without assigning either
Organism identity or World commit authority to Embodiment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .metabolism import MetabolicLedger
from .physiology import LivingBodyState


@dataclass(slots=True)
class EmbodimentCheckpoint:
    """A body state and its metabolic accounting tied to one episode identity."""

    body_id: str
    episode_id: str
    body_state: LivingBodyState
    metabolic_ledger: MetabolicLedger

    SCHEMA_VERSION = 1

    def __post_init__(self) -> None:
        if not isinstance(self.body_id, str) or not self.body_id.strip():
            raise ValueError("body_id must be a non-empty string")
        if not isinstance(self.episode_id, str) or not self.episode_id.strip():
            raise ValueError("episode_id must be a non-empty string")
        if not isinstance(self.body_state, LivingBodyState):
            raise ValueError("body_state must be LivingBodyState")
        if not isinstance(self.metabolic_ledger, MetabolicLedger):
            raise ValueError("metabolic_ledger must be MetabolicLedger")
        if self.metabolic_ledger.body_state is not self.body_state:
            raise ValueError("metabolic ledger must be bound to the checkpoint body state")

    def to_bytes(self) -> bytes:
        """Encode a deterministic JSON payload suitable for hashing/storage."""
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "body_id": self.body_id,
            "episode_id": self.episode_id,
            "body_state": self.body_state.checkpoint(),
            "metabolic_ledger": self.metabolic_ledger.checkpoint(),
        }
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "EmbodimentCheckpoint":
        if not isinstance(encoded, bytes):
            raise ValueError("checkpoint must be bytes")
        try:
            payload: Any = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid embodiment checkpoint JSON") from exc
        expected_keys = {
            "schema_version",
            "body_id",
            "episode_id",
            "body_state",
            "metabolic_ledger",
        }
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise ValueError("invalid embodiment checkpoint fields")
        schema_version = payload["schema_version"]
        if type(schema_version) is not int or schema_version != cls.SCHEMA_VERSION:
            raise ValueError("unsupported embodiment checkpoint schema")
        body_id = payload.get("body_id")
        episode_id = payload.get("episode_id")
        body_payload = payload.get("body_state")
        ledger_payload = payload.get("metabolic_ledger")
        if (
            not isinstance(body_id, str)
            or not isinstance(episode_id, str)
            or not isinstance(body_payload, dict)
            or not isinstance(ledger_payload, dict)
        ):
            raise ValueError("invalid embodiment checkpoint fields")
        body_state = LivingBodyState.from_checkpoint(body_payload)
        ledger = MetabolicLedger.from_checkpoint(ledger_payload, body_state=body_state)
        return cls(body_id, episode_id, body_state, ledger)

    @classmethod
    def validate_checkpoint(cls, encoded: bytes, owner_identity: str, schema_version: str) -> bool:
        """Validate Embodiment-owned bytes without issuing a World receipt."""
        if schema_version != "embodiment-checkpoint-v1":
            return False
        try:
            checkpoint = cls.from_bytes(encoded)
        except (TypeError, ValueError):
            return False
        return checkpoint.body_id == owner_identity

    @classmethod
    def verify_restoration(cls, encoded: bytes, owner_identity: str, schema_version: str) -> bool:
        """Verify a restored checkpoint through the owner checkpoint codec."""
        return cls.validate_checkpoint(encoded, owner_identity, schema_version)


__all__ = ["EmbodimentCheckpoint"]
