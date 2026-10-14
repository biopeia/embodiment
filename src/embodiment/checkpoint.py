"""Owner-scoped persistence composition for a body embodiment episode.

This is a migration-stage format, not a finalized portable World checkpoint.
It composes existing body and metabolism checkpoints without assigning either
Organism identity or World commit authority to Embodiment.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from .metabolism import MetabolicLedger
from .physiology import LivingBodyState


class _CommittedCheckpointReference(Protocol):
    """Structural view of a World-issued owner checkpoint reference."""

    owner: str
    owner_identity: str
    checkpoint_id: str
    schema_version: str
    sha256: str


@dataclass(frozen=True, slots=True)
class ReserveStateObservationProjection:
    """Embodiment-owned reserve snapshot from one committed checkpoint."""

    body_id: str
    episode_id: str
    amount: float
    capacity: float
    fraction: float
    quantity_kind: str
    world_id: str
    causal_tick: int
    commit_id: str
    checkpoint_id: str
    checkpoint_schema: str
    checkpoint_version: int
    source_owner_checkpoint_sha256: str

    semantic_family_id: ClassVar[str] = "biopeia.embodiment.reserve_state_snapshot"
    semantic_revision: ClassVar[str] = "1"
    semantic_authority: ClassVar[str] = "EMBODIMENT"
    semantic_asserter: ClassVar[str] = "embodiment.owner_checkpoint"
    semantic_producer: ClassVar[str] = "embodiment.checkpoint.project_committed_reserve_state"


def project_committed_reserve_state(
    checkpoint_bytes: bytes,
    *,
    owner_reference: _CommittedCheckpointReference,
    world_id: str,
    causal_tick: int,
    commit_id: str,
) -> ReserveStateObservationProjection:
    """Project reserve values only from bytes named by a committed owner ref.

    No morphology identity is included: EmbodimentCheckpoint v2 does not bind
    a morphology revision to its somatic payload.
    """
    if not isinstance(checkpoint_bytes, bytes):
        raise ValueError("Embodiment checkpoint snapshot must be bytes")
    for name, value in (("world_id", world_id), ("commit_id", commit_id)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty text")
    if type(causal_tick) is not int or causal_tick < 0:
        raise ValueError("causal_tick must be a non-negative integer")
    expected_digest = hashlib.sha256(checkpoint_bytes).hexdigest()
    if (
        getattr(owner_reference, "owner", None) != "embodiment"
        or getattr(owner_reference, "schema_version", None) != EmbodimentCheckpoint.OWNER_SCHEMA
        or getattr(owner_reference, "sha256", None) != expected_digest
    ):
        raise ValueError("checkpoint does not match the committed Embodiment owner reference")
    checkpoint_id = getattr(owner_reference, "checkpoint_id", None)
    owner_identity = getattr(owner_reference, "owner_identity", None)
    if not isinstance(checkpoint_id, str) or not checkpoint_id.strip():
        raise ValueError("committed Embodiment checkpoint id is required")
    if not isinstance(owner_identity, str) or not owner_identity.strip():
        raise ValueError("committed Embodiment owner identity is required")
    restored = EmbodimentCheckpoint.from_bytes(checkpoint_bytes)
    if restored.body_id != owner_identity:
        raise ValueError("checkpoint body identity differs from committed owner reference")
    reserve = restored.body_state.operational_observation()["reserve"]
    if not isinstance(reserve, dict) or reserve.get("quantity_kind") != "model_amount":
        raise ValueError("Embodiment reserve does not match the accepted model_amount contract")
    return ReserveStateObservationProjection(
        body_id=restored.body_id,
        episode_id=restored.episode_id,
        amount=float(reserve["amount"]),
        capacity=float(reserve["capacity"]),
        fraction=float(reserve["fraction"]),
        quantity_kind="model_amount",
        world_id=world_id,
        causal_tick=causal_tick,
        commit_id=commit_id,
        checkpoint_id=checkpoint_id,
        checkpoint_schema=EmbodimentCheckpoint.OWNER_SCHEMA,
        checkpoint_version=EmbodimentCheckpoint.SCHEMA_VERSION,
        source_owner_checkpoint_sha256=expected_digest,
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate checkpoint key: {key}")
        result[key] = value
    return result


@dataclass(slots=True)
class EmbodimentCheckpoint:
    """A body state and its metabolic accounting tied to one episode identity."""

    body_id: str
    episode_id: str
    body_state: LivingBodyState
    metabolic_ledger: MetabolicLedger

    SCHEMA_VERSION = 2
    OWNER_SCHEMA: ClassVar[str] = "embodiment-checkpoint-v2"

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
            payload: Any = json.loads(encoded, object_pairs_hook=_unique_object)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
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
        if schema_version != cls.OWNER_SCHEMA:
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


__all__ = ["EmbodimentCheckpoint", "ReserveStateObservationProjection", "project_committed_reserve_state"]
