"""Owner-scoped persistence composition for a body embodiment episode.

This is a migration-stage format, not a finalized portable World checkpoint.
It composes existing body and metabolism checkpoints without assigning either
Organism identity or World commit authority to Embodiment.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
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


class _CommittedWorldCutReceipt(Protocol):
    """Structural view of World evidence; World remains the trust boundary."""

    world_id: str
    causal_tick: int
    commit_id: str
    owner_checkpoint_references: tuple[_CommittedCheckpointReference, ...]


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


@dataclass(frozen=True, slots=True)
class EmbodimentAdoptionBindingV1:
    """Canonical owner record relating adopted physical and reserve bytes.

    The record alone is not evidence of a World commit. World must verify the
    exact binding and target checkpoint references as members of one cut.
    """

    world_id: str
    source_causal_tick: int
    target_causal_tick: int
    commit_id: str
    physical_step_id: str
    body_id: str
    episode_id: str
    morphology_revision: str
    physical_checkpoint_sha256: str
    reserve_checkpoint_sha256: str

    SCHEMA_VERSION: ClassVar[int] = 1
    OWNER_SCHEMA: ClassVar[str] = "embodiment-adoption-binding-v1"

    @classmethod
    def from_adopted_state(
        cls,
        adopted_body: object,
        reserve_checkpoint: "EmbodimentCheckpoint",
        *,
        world_id: str,
        source_causal_tick: int,
        target_causal_tick: int,
        commit_id: str,
        physical_step_id: str,
    ) -> "EmbodimentAdoptionBindingV1":
        """Create the binding from the exact owner-returned adopted state.

        The function deliberately accepts no caller-supplied expected episode:
        identity is derived from the accepted physical result and the persisted
        reserve checkpoint, then required to agree.
        """
        root = getattr(adopted_body, "root", None)
        checkpoint_bytes = getattr(adopted_body, "checkpoint_bytes", None)
        if root is None or not callable(checkpoint_bytes):
            raise TypeError("binding requires an adopted Embodiment physical state")
        if not isinstance(reserve_checkpoint, EmbodimentCheckpoint):
            raise TypeError("binding requires an Embodiment reserve checkpoint")
        physical = checkpoint_bytes()
        if not isinstance(physical, bytes):
            raise ValueError("adopted physical checkpoint must be bytes")
        step = getattr(root, "last_physical_step", None)
        if (
            step is None
            or step.world_id != world_id
            or step.causal_tick != source_causal_tick
            or step.physical_step_id != physical_step_id
            or root.world_id != world_id
            or root.causal_tick != target_causal_tick
            or root.body_id != reserve_checkpoint.body_id
            or root.embodiment_episode_id != reserve_checkpoint.episode_id
            or getattr(adopted_body, "morphology_revision", None) != root.morphology_revision
        ):
            raise ValueError("adopted physical state and reserve checkpoint do not identify the same transition")
        reserve = reserve_checkpoint.to_bytes()
        return cls(
            world_id=world_id,
            source_causal_tick=source_causal_tick,
            target_causal_tick=target_causal_tick,
            commit_id=commit_id,
            physical_step_id=physical_step_id,
            body_id=root.body_id,
            episode_id=root.embodiment_episode_id,
            morphology_revision=root.morphology_revision,
            physical_checkpoint_sha256=hashlib.sha256(physical).hexdigest(),
            reserve_checkpoint_sha256=hashlib.sha256(reserve).hexdigest(),
        )

    def __post_init__(self) -> None:
        for name in ("world_id", "commit_id", "physical_step_id", "body_id", "episode_id", "morphology_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if (type(self.source_causal_tick) is not int or self.source_causal_tick < 0
                or type(self.target_causal_tick) is not int
                or self.target_causal_tick != self.source_causal_tick + 1):
            raise ValueError("binding ticks must identify one adjacent causal transition")
        for name in ("physical_checkpoint_sha256", "reserve_checkpoint_sha256"):
            value = getattr(self, name)
            if (not isinstance(value, str) or len(value) != 64
                    or any(ch not in "0123456789abcdef" for ch in value)):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")

    def to_bytes(self) -> bytes:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "world_id": self.world_id,
            "source_causal_tick": self.source_causal_tick,
            "target_causal_tick": self.target_causal_tick,
            "commit_id": self.commit_id,
            "physical_step_id": self.physical_step_id,
            "body_id": self.body_id,
            "episode_id": self.episode_id,
            "morphology_revision": self.morphology_revision,
            "physical_checkpoint_sha256": self.physical_checkpoint_sha256,
            "reserve_checkpoint_sha256": self.reserve_checkpoint_sha256,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

    @classmethod
    def from_bytes(cls, encoded: bytes) -> "EmbodimentAdoptionBindingV1":
        if not isinstance(encoded, bytes):
            raise ValueError("binding must be bytes")
        try:
            payload = json.loads(encoded, object_pairs_hook=_unique_object)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("invalid Embodiment adoption binding JSON") from exc
        expected = {
            "schema_version", "world_id", "source_causal_tick", "target_causal_tick", "commit_id",
            "physical_step_id", "body_id", "episode_id", "morphology_revision",
            "physical_checkpoint_sha256", "reserve_checkpoint_sha256",
        }
        if (not isinstance(payload, dict) or set(payload) != expected
                or type(payload.get("schema_version")) is not int
                or payload["schema_version"] != cls.SCHEMA_VERSION):
            raise ValueError("invalid Embodiment adoption binding fields or schema")
        restored = cls(**{key: value for key, value in payload.items() if key != "schema_version"})
        if restored.to_bytes() != encoded:
            raise ValueError("non-canonical Embodiment adoption binding encoding")
        return restored

    @classmethod
    def validate_checkpoint(cls, encoded: bytes, owner_identity: str, schema_version: str) -> bool:
        if schema_version != cls.OWNER_SCHEMA:
            return False
        try:
            binding = cls.from_bytes(encoded)
        except (TypeError, ValueError):
            return False
        return binding.body_id == owner_identity

    @classmethod
    def verify_checkpoint_set(
        cls,
        references: tuple[object, ...],
        *,
        world_id: str,
        source_causal_tick: int,
        target_causal_tick: int,
        commit_id: str,
    ) -> bool:
        """Verify all Embodiment artifacts against the World cut context.

        World invokes this owner contract only with references in one proposed
        or restored cut. World independently checks cut membership and the
        transition context; this method checks Embodiment's cross-artifact
        semantics and content digests.
        """
        from .physics3d.articulated_state import ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA

        if not isinstance(references, tuple) or len(references) != 3:
            return False
        expected_schemas = {
            ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA,
            EmbodimentCheckpoint.OWNER_SCHEMA,
            cls.OWNER_SCHEMA,
        }
        if {getattr(ref, "schema_version", None) for ref in references} != expected_schemas:
            return False
        identities = {getattr(ref, "owner_identity", None) for ref in references}
        owners = {getattr(ref, "owner", None) for ref in references}
        if len(identities) != 1 or len(owners) != 1 or owners != {"embodiment"}:
            return False
        by_schema = {ref.schema_version: ref for ref in references}
        try:
            payloads: dict[str, bytes] = {}
            for schema, reference in by_schema.items():
                encoded = Path(reference.locator).read_bytes()
                if hashlib.sha256(encoded).hexdigest() != reference.sha256:
                    return False
                payloads[schema] = encoded
            binding = cls.from_bytes(payloads[cls.OWNER_SCHEMA])
            reserve = EmbodimentCheckpoint.from_bytes(payloads[EmbodimentCheckpoint.OWNER_SCHEMA])
            physical = json.loads(payloads[ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA])
            root = physical["root"]
            step = root["last_physical_step"]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False
        body_id = next(iter(identities))
        if (
            not isinstance(body_id, str)
            or not EmbodimentCheckpoint.validate_checkpoint(
                payloads[EmbodimentCheckpoint.OWNER_SCHEMA], body_id, EmbodimentCheckpoint.OWNER_SCHEMA
            )
            or not cls.validate_checkpoint(payloads[cls.OWNER_SCHEMA], body_id, cls.OWNER_SCHEMA)
        ):
            return False
        return (
            binding.world_id == world_id
            and binding.source_causal_tick == source_causal_tick
            and binding.target_causal_tick == target_causal_tick
            and binding.commit_id == commit_id
            and binding.body_id == body_id == reserve.body_id == root["body_id"]
            and binding.episode_id == reserve.episode_id == root["embodiment_episode_id"]
            and binding.morphology_revision == root["morphology_revision"]
            and binding.physical_step_id == step["physical_step_id"]
            and root["world_id"] == world_id
            and root["causal_tick"] == target_causal_tick
            and step["world_id"] == world_id
            and step["causal_tick"] == source_causal_tick
            and step["body_id"] == body_id
            and step["embodiment_episode_id"] == binding.episode_id
            and binding.physical_checkpoint_sha256
            == hashlib.sha256(payloads[ARTICULATED_PHYSICAL_CHECKPOINT_SCHEMA]).hexdigest()
            and binding.reserve_checkpoint_sha256
            == hashlib.sha256(payloads[EmbodimentCheckpoint.OWNER_SCHEMA]).hexdigest()
        )


def project_committed_reserve_state(
    checkpoint_bytes: bytes,
    *,
    committed_cut: _CommittedWorldCutReceipt,
    owner_reference: _CommittedCheckpointReference,
) -> ReserveStateObservationProjection:
    """Project reserve values only from bytes named by a committed owner ref.

    No morphology identity is included: EmbodimentCheckpoint v2 does not bind
    a morphology revision to its somatic payload. The supplied World receipt
    provides correlation context; only World can verify commit authenticity.
    """
    if not isinstance(checkpoint_bytes, bytes):
        raise ValueError("Embodiment checkpoint snapshot must be bytes")
    world_id = getattr(committed_cut, "world_id", None)
    causal_tick = getattr(committed_cut, "causal_tick", None)
    commit_id = getattr(committed_cut, "commit_id", None)
    cut_references = getattr(committed_cut, "owner_checkpoint_references", None)
    if not isinstance(world_id, str) or not world_id.strip():
        raise ValueError("World committed-cut receipt must identify a World")
    if type(causal_tick) is not int or causal_tick < 0:
        raise ValueError("World committed-cut receipt must identify a valid causal tick")
    if not isinstance(commit_id, str) or not commit_id.strip():
        raise ValueError("World committed-cut receipt must identify a commit")
    if not isinstance(cut_references, tuple) or owner_reference not in cut_references:
        raise ValueError("Embodiment owner reference is not in the supplied World cut")
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
