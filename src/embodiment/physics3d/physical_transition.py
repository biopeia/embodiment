"""Embodiment-owned acceptance of a physical solver candidate.

This module does not execute a solver or commit a World cut. It provides the
owner boundary which validates a correlated candidate and returns a new,
Embodiment-owned pose state. It also defines deterministic checkpoint bytes;
external storage is required before those bytes are durably referenceable.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Protocol

from embodiment.observation import (
    BodyPoseObservationProjection,
    BodyPoseSample,
    PhysicalStepCorrelation,
)


class WorldPhysicalStepContext(Protocol):
    """Structural view of the World-issued context required for adoption.

    Embodiment intentionally does not depend on the World package. Callers
    must pass the context received from the World coordinator; this protocol
    is a typing boundary, not authentication of an arbitrary Python object.
    """

    world_id: str
    source_causal_tick: int
    target_causal_tick: int
    physical_step_id: str
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    environment_revision: str
    solver_config_revision: str


@dataclass(frozen=True, slots=True)
class SolverBodyCandidate:
    """Untrusted numerical result proposed for owner adoption.

    Position is metres and orientation is xyzw in the declared reference/body
    frames. Root linear velocity is metres/second and root angular velocity is
    radians/second; both vectors are expressed in ``reference_frame``. The
    solver is responsible only for producing these numerical values; this
    type does not grant them authority.
    """

    correlation: PhysicalStepCorrelation
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    linear_velocity_m_per_s: tuple[float, float, float]
    angular_velocity_rad_per_s: tuple[float, float, float]

    def __post_init__(self) -> None:
        _validate_vector(self.linear_velocity_m_per_s, "linear_velocity_m_per_s")
        _validate_vector(self.angular_velocity_rad_per_s, "angular_velocity_rad_per_s")


@dataclass(frozen=True, slots=True)
class EmbodimentPhysicalState:
    """Current owner-held free-root rigid-body state at a World causal tick.

    This is explicitly ``EMBODIMENT_OWNED``. Its checkpoint encoding is a
    recoverable value but it has no durable checkpoint reference until an
    external store persists and verifies its bytes.
    """

    world_id: str
    causal_tick: int
    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    pose: BodyPoseSample
    linear_velocity_m_per_s: tuple[float, float, float]
    angular_velocity_rad_per_s: tuple[float, float, float]
    last_physical_step: PhysicalStepCorrelation | None = None
    state_owner: str = "EMBODIMENT_OWNED"
    durable_reference: str | None = None

    def __post_init__(self) -> None:
        for name in ("world_id", "body_id", "embodiment_episode_id", "morphology_revision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if self.state_owner != "EMBODIMENT_OWNED":
            raise ValueError("physical pose state must be Embodiment-owned")
        if self.durable_reference is not None:
            raise ValueError("this in-memory state type cannot claim a durable reference")
        if isinstance(self.causal_tick, bool) or not isinstance(self.causal_tick, int) or self.causal_tick < 0:
            raise ValueError("causal_tick must be a non-negative integer")
        if self.pose.body_id != self.body_id:
            raise ValueError("pose body identity differs from owner state")
        _validate_vector(self.linear_velocity_m_per_s, "linear_velocity_m_per_s")
        _validate_vector(self.angular_velocity_rad_per_s, "angular_velocity_rad_per_s")
        sample_value = self.pose.sample_value
        if isinstance(sample_value, bool) or not isinstance(sample_value, (int, float, str)):
            raise ValueError("pose sample_value must be a string or number")
        if isinstance(sample_value, (int, float)) and not math.isfinite(float(sample_value)):
            raise ValueError("pose numeric sample_value must be finite")
        if self.last_physical_step is not None:
            step = self.last_physical_step
            if not isinstance(step, PhysicalStepCorrelation):
                raise ValueError("last_physical_step must be a physical-step correlation")
            if (
                step.world_id != self.world_id
                or step.body_id != self.body_id
                or step.embodiment_episode_id != self.embodiment_episode_id
                or step.morphology_revision != self.morphology_revision
            ):
                raise ValueError("last physical step identity/revision differs from owner state")
            if step.causal_tick + 1 != self.causal_tick:
                raise ValueError("last physical step tick does not precede owner state tick")
            if self.pose.sample_kind != "physics_step" or self.pose.sample_value != step.physical_step_id:
                raise ValueError("owner pose sample does not identify the last accepted physical step")

    @property
    def durably_referenceable(self) -> bool:
        """Whether this in-memory value itself has a durable store reference."""
        return False

    def body_pose_observation_projection(self) -> BodyPoseObservationProjection:
        """Return a passive projection of this adopted owner state.

        The result is not a World commit receipt and must not be published as
        committed without independent World-side verification.
        """

        step = self.last_physical_step
        return BodyPoseObservationProjection(
            world_id=self.world_id,
            causal_tick=self.causal_tick,
            body_id=self.body_id,
            embodiment_episode_id=self.embodiment_episode_id,
            morphology_revision=self.morphology_revision,
            pose=self.pose,
            last_physical_step_id=None if step is None else step.physical_step_id,
            last_physical_step_source_tick=None if step is None else step.causal_tick,
            environment_revision=None if step is None else step.environment_revision,
            solver_config_revision=None if step is None else step.solver_config_revision,
            physical_step_correlation=step,
        )

    def checkpoint_bytes(self) -> bytes:
        """Encode this owner state deterministically for an external checkpoint store.

        The bytes are a recoverable value, not proof that they have been
        persisted. World may use their digest as a reference only after its
        configured checkpoint store has durably stored and verified them.
        """

        pose = self.pose
        payload = {
            "schema_version": 2,
            "state_owner": self.state_owner,
            "world_id": self.world_id,
            "causal_tick": self.causal_tick,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "linear_velocity_m_per_s": list(self.linear_velocity_m_per_s),
            "angular_velocity_rad_per_s": list(self.angular_velocity_rad_per_s),
            "linear_velocity_unit": "m/s",
            "angular_velocity_unit": "rad/s",
            "velocity_frame": pose.reference_frame,
            "last_physical_step": (
                None if self.last_physical_step is None else {
                    "world_id": self.last_physical_step.world_id,
                    "causal_tick": self.last_physical_step.causal_tick,
                    "physical_step_id": self.last_physical_step.physical_step_id,
                    "body_id": self.last_physical_step.body_id,
                    "embodiment_episode_id": self.last_physical_step.embodiment_episode_id,
                    "morphology_revision": self.last_physical_step.morphology_revision,
                    "environment_revision": self.last_physical_step.environment_revision,
                    "solver_config_revision": self.last_physical_step.solver_config_revision,
                }
            ),
            "pose": {
                "reference_frame": pose.reference_frame,
                "body_frame": pose.body_frame,
                "position_m": list(pose.position_m),
                "orientation_xyzw": list(pose.orientation_xyzw),
                "sample_kind": pose.sample_kind,
                "sample_value": pose.sample_value,
                "sample_time_s": pose.sample_time_s,
                "contract_revision": pose.contract_revision,
                "position_unit": "m",
                "orientation_order": "xyzw",
            },
        }
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")

    @property
    def checkpoint_digest(self) -> str:
        """Stable content identifier; it does not assert external durability."""

        return hashlib.sha256(self.checkpoint_bytes()).hexdigest()

    @classmethod
    def restore_checkpoint(cls, encoded: bytes) -> EmbodimentPhysicalState:
        """Decode and validate a checkpoint value previously emitted here."""

        if not isinstance(encoded, bytes):
            raise ValueError("physical checkpoint must be bytes")
        try:
            payload = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid Embodiment physical checkpoint JSON") from exc
        expected_keys = {
            "schema_version", "state_owner", "world_id", "causal_tick", "body_id",
            "embodiment_episode_id", "morphology_revision", "last_physical_step", "pose",
            "linear_velocity_m_per_s", "angular_velocity_rad_per_s",
            "linear_velocity_unit", "angular_velocity_unit", "velocity_frame",
        }
        if not isinstance(payload, dict) or set(payload) != expected_keys:
            raise ValueError("invalid Embodiment physical checkpoint fields")
        if payload["schema_version"] != 2:
            raise ValueError("unsupported Embodiment physical checkpoint schema")
        pose_payload = payload["pose"]
        if not isinstance(pose_payload, dict):
            raise ValueError("invalid Embodiment physical checkpoint pose")
        if (
            payload["linear_velocity_unit"] != "m/s"
            or payload["angular_velocity_unit"] != "rad/s"
            or payload["velocity_frame"] != pose_payload.get("reference_frame")
        ):
            raise ValueError("unsupported physical velocity units or frame")
        for name in ("linear_velocity_m_per_s", "angular_velocity_rad_per_s"):
            if not isinstance(payload[name], list):
                raise ValueError(f"checkpoint {name} must be an array")
        step_payload = payload["last_physical_step"]
        if step_payload is not None:
            step_keys = {
                "world_id", "causal_tick", "physical_step_id", "body_id",
                "embodiment_episode_id", "morphology_revision", "environment_revision",
                "solver_config_revision",
            }
            if not isinstance(step_payload, dict) or set(step_payload) != step_keys:
                raise ValueError("invalid checkpoint physical-step correlation")
        pose_keys = {
            "reference_frame", "body_frame", "position_m", "orientation_xyzw",
            "sample_kind", "sample_value", "sample_time_s", "contract_revision",
            "position_unit", "orientation_order",
        }
        if not isinstance(pose_payload, dict) or set(pose_payload) != pose_keys:
            raise ValueError("invalid Embodiment physical checkpoint pose")
        if pose_payload["position_unit"] != "m" or pose_payload["orientation_order"] != "xyzw":
            raise ValueError("unsupported physical pose units or orientation ordering")
        sample_value = pose_payload["sample_value"]
        if isinstance(sample_value, bool) or not isinstance(sample_value, (int, float, str)):
            raise ValueError("checkpoint pose sample_value must be a string or number")
        for name in ("position_m", "orientation_xyzw"):
            if not isinstance(pose_payload[name], list):
                raise ValueError(f"checkpoint pose {name} must be an array")
        try:
            pose = BodyPoseSample(
                body_id=payload["body_id"],
                reference_frame=pose_payload["reference_frame"],
                body_frame=pose_payload["body_frame"],
                position_m=tuple(pose_payload["position_m"]),
                orientation_xyzw=tuple(pose_payload["orientation_xyzw"]),
                sample_kind=pose_payload["sample_kind"],
                sample_value=pose_payload["sample_value"],
                sample_time_s=pose_payload["sample_time_s"],
                contract_revision=pose_payload["contract_revision"],
            )
            return cls(
                world_id=payload["world_id"],
                causal_tick=payload["causal_tick"],
                body_id=payload["body_id"],
                embodiment_episode_id=payload["embodiment_episode_id"],
                morphology_revision=payload["morphology_revision"],
                pose=pose,
                linear_velocity_m_per_s=tuple(payload["linear_velocity_m_per_s"]),
                angular_velocity_rad_per_s=tuple(payload["angular_velocity_rad_per_s"]),
                last_physical_step=(
                    None if step_payload is None else PhysicalStepCorrelation(**step_payload)
                ),
                state_owner=payload["state_owner"],
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid Embodiment physical checkpoint value") from exc

    def adopt_candidate(
        self,
        candidate: SolverBodyCandidate,
        *,
        world_context: WorldPhysicalStepContext,
    ) -> EmbodimentPhysicalState:
        """Validate a World-correlated candidate and return staged owner state.

        Rejection leaves this immutable state untouched. A candidate is valid
        only for the exact active identities/revisions and current causal tick.
        ``world_context`` must come from the active World coordinator call path;
        structural typing does not authenticate fabricated context values.
        This pure value transition does not publish a commit or enforce global
        single-use; World selects the checkpoint reference that becomes
        authoritative when it commits the causal cut.
        """

        expected_step = _correlation_from_world_context(world_context)
        c = candidate.correlation
        if c != expected_step:
            raise ValueError("solver candidate does not match the World physical-step context")
        expected = (
            self.world_id,
            self.causal_tick,
            self.body_id,
            self.embodiment_episode_id,
            self.morphology_revision,
        )
        actual = (c.world_id, c.causal_tick, c.body_id, c.embodiment_episode_id, c.morphology_revision)
        if actual != expected:
            raise ValueError("solver candidate correlation does not match active Embodiment state")
        if not candidate.reference_frame.strip() or not candidate.body_frame.strip():
            raise ValueError("candidate reference and body frames must be explicit")
        if (
            candidate.reference_frame != self.pose.reference_frame
            or candidate.body_frame != self.pose.body_frame
        ):
            raise ValueError("solver candidate frames do not match active Embodiment pose frames")
        pose = BodyPoseSample(
            body_id=self.body_id,
            reference_frame=candidate.reference_frame,
            body_frame=candidate.body_frame,
            position_m=candidate.position_m,
            orientation_xyzw=candidate.orientation_xyzw,
            sample_kind="physics_step",
            sample_value=c.physical_step_id,
        )
        return EmbodimentPhysicalState(
            world_id=self.world_id,
            causal_tick=self.causal_tick + 1,
            body_id=self.body_id,
            embodiment_episode_id=self.embodiment_episode_id,
            morphology_revision=self.morphology_revision,
            pose=pose,
            linear_velocity_m_per_s=candidate.linear_velocity_m_per_s,
            angular_velocity_rad_per_s=candidate.angular_velocity_rad_per_s,
            last_physical_step=expected_step,
        )


def _correlation_from_world_context(
    context: WorldPhysicalStepContext,
) -> PhysicalStepCorrelation:
    """Validate and project the shared World context into Embodiment's value."""

    names = (
        "world_id", "physical_step_id", "body_id", "embodiment_episode_id",
        "morphology_revision", "environment_revision", "solver_config_revision",
    )
    try:
        values = {name: getattr(context, name) for name in names}
        source_tick = context.source_causal_tick
        target_tick = context.target_causal_tick
    except AttributeError as exc:
        raise ValueError("World physical-step context is incomplete") from exc
    if any(type(value) is not str or not value.strip() for value in values.values()):
        raise ValueError("World physical-step context identities and revisions must be non-empty")
    if type(source_tick) is not int or type(target_tick) is not int:
        raise ValueError("World physical-step context ticks must be integers")
    if source_tick < 0 or target_tick != source_tick + 1:
        raise ValueError("World physical-step target tick must immediately follow its source tick")
    return PhysicalStepCorrelation(causal_tick=source_tick, **values)


def _validate_vector(value: object, name: str) -> None:
    if not isinstance(value, tuple) or len(value) != 3:
        raise ValueError(f"{name} must be a 3-vector in its declared frame")
    if any(isinstance(component, bool) or not isinstance(component, (int, float)) for component in value):
        raise ValueError(f"{name} components must be numeric")
    if any(not math.isfinite(float(component)) for component in value):
        raise ValueError(f"{name} components must be finite")


__all__ = [
    "BodyPoseObservationProjection",
    "EmbodimentPhysicalState",
    "PhysicalStepCorrelation",
    "SolverBodyCandidate",
    "WorldPhysicalStepContext",
]
