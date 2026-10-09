"""Embodiment-owned joint state and adoption of articulated solver results.

This module accepts numerical candidates; it does not execute a solver or
coordinate a World causal commit. Joint names are stable identities within an
explicit active morphology binding, never positional authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

from embodiment.physics3d.articulated_spec import ArticulatedBodySpec, build_articulated_urdf
from embodiment.physics3d.physical_transition import (
    EmbodimentPhysicalState,
    PhysicalStepCorrelation,
    SolverBodyCandidate,
)


@dataclass(frozen=True, slots=True)
class JointRange:
    joint_id: str
    lower_rad: float
    upper_rad: float
    max_velocity_rad_per_s: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_id", _identity(self.joint_id, "joint_id"))
        _finite(self.lower_rad, "lower_rad")
        _finite(self.upper_rad, "upper_rad")
        _finite(self.max_velocity_rad_per_s, "max_velocity_rad_per_s")
        if self.lower_rad >= self.upper_rad:
            raise ValueError("joint range lower_rad must be less than upper_rad")
        if self.max_velocity_rad_per_s <= 0:
            raise ValueError("max_velocity_rad_per_s must be positive")


@dataclass(frozen=True, slots=True)
class JointKinematicState:
    joint_id: str
    position_rad: float
    velocity_rad_per_s: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_id", _identity(self.joint_id, "joint_id"))
        _finite(self.position_rad, "position_rad")
        _finite(self.velocity_rad_per_s, "velocity_rad_per_s")


@dataclass(frozen=True, slots=True)
class ActiveArticulatedMorphology:
    """Embodiment-owned descriptor bound to body, episode and morphology revision.

    Construct this value at the Embodiment owner boundary from the descriptor
    currently active for the episode/revision. This value does not authenticate
    its own origin: callers must not accept an arbitrary caller-supplied
    descriptor as authority. State construction and recovery verify against
    this owner-supplied descriptor rather than trusting checkpoint ranges.
    """

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    description_sha256: str
    joint_ranges: tuple[JointRange, ...]

    @classmethod
    def from_spec(
        cls,
        *,
        body_id: str,
        embodiment_episode_id: str,
        morphology_revision: str,
        spec: ArticulatedBodySpec,
    ) -> ActiveArticulatedMorphology:
        topology_ids = tuple(item.joint_name for item in spec.joint_topology)
        spec_ids = tuple(item.name for item in spec.joint_specs)
        if topology_ids != spec_ids:
            raise ValueError("active morphology requires the ordered topology contract of ArticulatedBodySpec")
        description = build_articulated_urdf(spec)
        ranges = tuple(
            JointRange(item.name, item.lower, item.upper, item.max_velocity)
            for item in spec.joint_specs
        )
        return cls(
            body_id=body_id,
            embodiment_episode_id=embodiment_episode_id,
            morphology_revision=morphology_revision,
            description_sha256=hashlib.sha256(description.encode("utf-8")).hexdigest(),
            joint_ranges=ranges,
        )

    def __post_init__(self) -> None:
        for field in ("body_id", "embodiment_episode_id", "morphology_revision"):
            object.__setattr__(self, field, _identity(getattr(self, field), field))
        digest = _identity(self.description_sha256, "description_sha256")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("description_sha256 must be a lowercase SHA-256 digest")
        ranges = _unique_by_id(self.joint_ranges, "active joint range")
        object.__setattr__(self, "joint_ranges", tuple(ranges[key] for key in sorted(ranges)))


@dataclass(frozen=True, slots=True)
class SolverArticulatedCandidate:
    """Untrusted root and joint values returned for one authorized step."""

    root: SolverBodyCandidate
    joints: tuple[JointKinematicState, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.root, SolverBodyCandidate):
            raise ValueError("articulated candidate requires a root body candidate")
        _unique_by_id(self.joints, "candidate joint")


@dataclass(frozen=True, slots=True)
class ArticulatedEmbodimentPhysicalState:
    """Owner-held root and joint state verified against its active morphology."""

    root: EmbodimentPhysicalState
    morphology: ActiveArticulatedMorphology
    joints: tuple[JointKinematicState, ...]
    state_owner: str = "EMBODIMENT_OWNED"

    def __post_init__(self) -> None:
        if self.state_owner != "EMBODIMENT_OWNED":
            raise ValueError("articulated physical state must be Embodiment-owned")
        if not isinstance(self.morphology, ActiveArticulatedMorphology):
            raise ValueError("articulated state requires the active Embodiment morphology descriptor")
        if (
            self.root.body_id != self.morphology.body_id
            or self.root.embodiment_episode_id != self.morphology.embodiment_episode_id
            or self.root.morphology_revision != self.morphology.morphology_revision
        ):
            raise ValueError("root state identity/episode/morphology does not match active descriptor")
        ranges = {item.joint_id: item for item in self.morphology.joint_ranges}
        joints = _unique_by_id(self.joints, "joint state")
        if set(ranges) != set(joints):
            raise ValueError("joint state identities must exactly match active morphology joints")
        for joint_id, state in joints.items():
            bounds = ranges[joint_id]
            if not bounds.lower_rad <= state.position_rad <= bounds.upper_rad:
                raise ValueError(f"joint {joint_id!r} position is outside active morphology range")
            if abs(state.velocity_rad_per_s) > bounds.max_velocity_rad_per_s:
                raise ValueError(f"joint {joint_id!r} velocity exceeds active morphology limit")
        object.__setattr__(self, "joints", tuple(joints[key] for key in sorted(joints)))

    @property
    def morphology_revision(self) -> str:
        return self.morphology.morphology_revision

    @property
    def causal_tick(self) -> int:
        return self.root.causal_tick

    def adopt_candidate(
        self,
        candidate: SolverArticulatedCandidate,
        *,
        expected_step: PhysicalStepCorrelation,
    ) -> ArticulatedEmbodimentPhysicalState:
        """Validate all identity-bound channels, then return a new owner state."""

        candidate_joints = _unique_by_id(candidate.joints, "candidate joint")
        active_ids = {item.joint_id for item in self.morphology.joint_ranges}
        if set(candidate_joints) != active_ids:
            raise ValueError("solver joint identities do not match active morphology")
        accepted_root = self.root.adopt_candidate(candidate.root, expected_step=expected_step)
        return ArticulatedEmbodimentPhysicalState(
            root=accepted_root,
            morphology=self.morphology,
            joints=tuple(candidate_joints[key] for key in sorted(candidate_joints)),
        )

    def checkpoint_bytes(self) -> bytes:
        payload = {
            "schema_version": 1,
            "state_owner": self.state_owner,
            "root": json.loads(self.root.checkpoint_bytes()),
            "active_morphology": {
                "body_id": self.morphology.body_id,
                "embodiment_episode_id": self.morphology.embodiment_episode_id,
                "morphology_revision": self.morphology.morphology_revision,
                "description_sha256": self.morphology.description_sha256,
            },
            "joints": [
                {
                    "joint_id": item.joint_id,
                    "position_rad": item.position_rad,
                    "velocity_rad_per_s": item.velocity_rad_per_s,
                }
                for item in self.joints
            ],
            "position_unit": "rad",
            "velocity_unit": "rad/s",
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

    @classmethod
    def restore_checkpoint(
        cls,
        encoded: bytes,
        *,
        active_morphology: ActiveArticulatedMorphology,
    ) -> ArticulatedEmbodimentPhysicalState:
        if not isinstance(encoded, bytes):
            raise ValueError("articulated checkpoint must be bytes")
        try:
            payload = json.loads(encoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid articulated Embodiment checkpoint JSON") from exc
        expected = {
            "schema_version", "state_owner", "root", "active_morphology", "joints",
            "position_unit", "velocity_unit",
        }
        if not isinstance(payload, dict) or set(payload) != expected:
            raise ValueError("invalid articulated Embodiment checkpoint fields")
        if payload["schema_version"] != 1 or payload["position_unit"] != "rad" or payload["velocity_unit"] != "rad/s":
            raise ValueError("unsupported articulated Embodiment checkpoint schema or units")
        expected_binding = {
            "body_id": active_morphology.body_id,
            "embodiment_episode_id": active_morphology.embodiment_episode_id,
            "morphology_revision": active_morphology.morphology_revision,
            "description_sha256": active_morphology.description_sha256,
        }
        if payload["active_morphology"] != expected_binding:
            raise ValueError("checkpoint morphology binding differs from active Embodiment descriptor")
        try:
            if not isinstance(payload["root"], dict) or not isinstance(payload["joints"], list):
                raise ValueError("invalid articulated checkpoint values")
            root = EmbodimentPhysicalState.restore_checkpoint(
                json.dumps(payload["root"], sort_keys=True, separators=(",", ":")).encode()
            )
            return cls(
                root=root,
                morphology=active_morphology,
                joints=tuple(JointKinematicState(**item) for item in payload["joints"]),
                state_owner=payload["state_owner"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid articulated Embodiment checkpoint value") from exc


def _identity(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty stable identity")
    return value.strip()


def _finite(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")


def _unique_by_id(items: tuple[JointRange, ...] | tuple[JointKinematicState, ...], label: str):
    if not isinstance(items, tuple):
        raise ValueError(f"{label}s must be an immutable tuple")
    values = {}
    for item in items:
        if not isinstance(item, (JointRange, JointKinematicState)):
            raise ValueError(f"invalid {label} value")
        if item.joint_id in values:
            raise ValueError(f"duplicate {label} identity {item.joint_id!r}")
        values[item.joint_id] = item
    return values


__all__ = [
    "ActiveArticulatedMorphology",
    "ArticulatedEmbodimentPhysicalState",
    "JointKinematicState",
    "JointRange",
    "SolverArticulatedCandidate",
]
