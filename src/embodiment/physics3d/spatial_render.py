"""Embodiment-owned render projections.

This module exposes explicitly authored box geometry and revolute joint
topology, plus validation/binding of already-computed dynamic link poses. It
never calculates kinematics or proves a World commit/cut. Dynamic pose values
are candidates from the same physical step; World remains responsible for
binding a published sample to a confirmed causal cut.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import math
import re
from typing import Any

import rfc8785

from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.physical_transition import WorldPhysicalStepContext


CONTRACT_REVISION = "embodiment.render_morphology/v1"
COORDINATE_SYSTEM = "right_handed_z_up"
LENGTH_UNIT = "m"
MAX_LINKS = 128
MAX_SEGMENTS = 128
MAX_REVOLUTE_JOINTS = 127
MAX_DESCRIPTOR_BYTES = 256 * 1024
MAX_DYNAMIC_POSE_BYTES = 256 * 1024
QUATERNION_NORM_TOLERANCE = 1e-6
_DIGEST_PREFIX = b"biopeia:embodiment.render_morphology/v1\n"
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be a non-empty, trimmed identity")
    return value


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{field} must be a finite number") from error
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _vector(value: object, length: int, field: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise ValueError(f"{field} must contain exactly {length} values")
    return tuple(_finite_number(item, field) for item in value)


@dataclass(frozen=True, slots=True)
class RenderSegment:
    """Owner-authored box geometry attached to one stable link identity."""

    segment_id: str
    dimensions_m: tuple[float, float, float]
    visual_origin_in_link_m: tuple[float, float, float]
    shape: str = "box"

    def __post_init__(self) -> None:
        _identity(self.segment_id, "segment_id")
        if self.shape != "box":
            raise ValueError("only explicitly authored box geometry is supported")
        dimensions = _vector(self.dimensions_m, 3, "dimensions_m")
        if any(value <= 0.0 for value in dimensions):
            raise ValueError("box dimensions must be positive")
        origin = _vector(self.visual_origin_in_link_m, 3, "visual_origin_in_link_m")
        object.__setattr__(self, "dimensions_m", dimensions)
        object.__setattr__(self, "visual_origin_in_link_m", origin)

    def to_payload(self) -> dict[str, object]:
        return {
            "segment_id": self.segment_id,
            "shape": self.shape,
            "dimensions_m": list(self.dimensions_m),
            "visual_origin_in_link_m": list(self.visual_origin_in_link_m),
        }


@dataclass(frozen=True, slots=True)
class RenderJoint:
    """Owner-authored revolute topology; contains no mechanics limits."""

    joint_id: str
    parent_link_id: str
    child_link_id: str
    joint_origin_in_parent_m: tuple[float, float, float]
    axis_in_joint_frame: tuple[float, float, float]
    joint_type: str = "revolute"

    def __post_init__(self) -> None:
        for field in ("joint_id", "parent_link_id", "child_link_id"):
            _identity(getattr(self, field), field)
        if self.joint_type != "revolute":
            raise ValueError("only revolute joints are supported")
        origin = _vector(self.joint_origin_in_parent_m, 3, "joint_origin_in_parent_m")
        axis = _vector(self.axis_in_joint_frame, 3, "axis_in_joint_frame")
        norm = math.sqrt(sum(value * value for value in axis))
        if not math.isfinite(norm) or norm == 0.0:
            raise ValueError("joint axis must be finite and non-zero")
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("joint axis must already be normalized in the active morphology")
        object.__setattr__(self, "joint_origin_in_parent_m", origin)
        object.__setattr__(self, "axis_in_joint_frame", axis)

    def to_payload(self) -> dict[str, object]:
        return {
            "joint_id": self.joint_id,
            "parent_link_id": self.parent_link_id,
            "child_link_id": self.child_link_id,
            "joint_type": self.joint_type,
            "joint_origin_in_parent_m": list(self.joint_origin_in_parent_m),
            "axis_in_joint_frame": list(self.axis_in_joint_frame),
        }


@dataclass(frozen=True, slots=True)
class RenderMorphologyProjection:
    """Closed, static render subset bound to one active morphology."""

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    geometry_revision: str
    segments: tuple[RenderSegment, ...]
    joints: tuple[RenderJoint, ...]
    render_geometry_sha256: str
    contract_revision: str = CONTRACT_REVISION
    schema_version: int = 1
    coordinate_system: str = COORDINATE_SYSTEM
    length_unit: str = LENGTH_UNIT

    def __post_init__(self) -> None:
        for field in ("body_id", "embodiment_episode_id", "morphology_revision", "geometry_revision"):
            _identity(getattr(self, field), field)
        if self.contract_revision != CONTRACT_REVISION or type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported render morphology contract revision")
        if self.coordinate_system != COORDINATE_SYSTEM or self.length_unit != LENGTH_UNIT:
            raise ValueError("unsupported coordinate system or length unit")
        if not isinstance(self.segments, tuple) or any(not isinstance(item, RenderSegment) for item in self.segments):
            raise ValueError("segments must be a tuple of RenderSegment values")
        if not isinstance(self.joints, tuple) or any(not isinstance(item, RenderJoint) for item in self.joints):
            raise ValueError("joints must be a tuple of RenderJoint values")
        if len(self.segments) > MAX_SEGMENTS or len(self.joints) > MAX_REVOLUTE_JOINTS:
            raise ValueError("render morphology exceeds item-count limits")
        segment_ids = tuple(item.segment_id for item in self.segments)
        joint_ids = tuple(item.joint_id for item in self.joints)
        if segment_ids != tuple(sorted(set(segment_ids))):
            raise ValueError("segments must have unique stable IDs in lexical order")
        if joint_ids != tuple(sorted(set(joint_ids))):
            raise ValueError("joints must have unique stable IDs in lexical order")
        # A morphology may contain articulated carrier links without an
        # authored SegmentSpec. Topology endpoints need not have display
        # geometry; never synthesize a placeholder segment for them.
        links = set(segment_ids)
        for joint in self.joints:
            if joint.parent_link_id == joint.child_link_id:
                raise ValueError("render joint parent and child must differ")
            links.add(joint.parent_link_id)
            links.add(joint.child_link_id)
        if len(links) > MAX_LINKS:
            raise ValueError("render morphology exceeds link-count limit")
        if not isinstance(self.render_geometry_sha256, str) or not _SHA256_RE.fullmatch(self.render_geometry_sha256):
            raise ValueError("render_geometry_sha256 must be a lowercase SHA-256 digest")
        expected = _render_digest(self._render_content_payload())
        if self.render_geometry_sha256 != expected:
            raise ValueError("render_geometry_sha256 does not match render content")
        if len(self.canonical_bytes()) > MAX_DESCRIPTOR_BYTES:
            raise ValueError("canonical render morphology descriptor exceeds byte limit")

    @classmethod
    def from_active_morphology(
        cls,
        morphology: ActiveArticulatedMorphology,
        *,
        geometry_revision: str,
    ) -> RenderMorphologyProjection:
        """Project only authored display geometry from owner-bound morphology.

        ``geometry_revision`` must come from the Embodiment owner's revision
        source; it is deliberately not synthesized from the content digest.
        Links without an authored SegmentSpec remain non-renderable and are not
        assigned placeholder geometry.
        """

        if not isinstance(morphology, ActiveArticulatedMorphology):
            raise TypeError("morphology must be an active Embodiment morphology")
        _identity(geometry_revision, "geometry_revision")
        spec = morphology.spec
        links = {spec.base_link_name}
        links.update(item.child_link for item in spec.joint_topology)
        links.update(item.child_link for item in spec.fixed_link_topology)
        if len(links) > MAX_LINKS:
            raise ValueError("active morphology exceeds link-count limit")
        if len(spec.segments) > MAX_SEGMENTS or len(spec.joint_topology) > MAX_REVOLUTE_JOINTS:
            raise ValueError("active morphology exceeds render item-count limits")
        if not set(spec.segments).issubset(links):
            raise ValueError("segment geometry references an undeclared morphology link")
        for topology in spec.joint_topology:
            if topology.parent_link not in links or topology.child_link not in links:
                raise ValueError("joint topology references an undeclared morphology link")

        segments = tuple(
            RenderSegment(
                segment_id=link_id,
                dimensions_m=segment.size,
                visual_origin_in_link_m=segment.origin,
            )
            for link_id, segment in sorted(spec.segments.items())
        )
        joint_specs = {item.name: item for item in spec.joint_specs}
        joints = tuple(
            RenderJoint(
                joint_id=topology.joint_name,
                parent_link_id=topology.parent_link,
                child_link_id=topology.child_link,
                joint_origin_in_parent_m=topology.origin,
                axis_in_joint_frame=joint_specs[topology.joint_name].axis,
            )
            for topology in sorted(spec.joint_topology, key=lambda item: item.joint_name)
        )
        content = _render_content_payload(segments, joints)
        return cls(
            body_id=morphology.body_id,
            embodiment_episode_id=morphology.embodiment_episode_id,
            morphology_revision=morphology.morphology_revision,
            geometry_revision=geometry_revision,
            segments=segments,
            joints=joints,
            render_geometry_sha256=_render_digest(content),
        )

    def _render_content_payload(self) -> dict[str, object]:
        return _render_content_payload(self.segments, self.joints)

    def to_payload(self) -> dict[str, object]:
        """Return the closed local projection value, not an Observation record."""

        return {
            "contract_revision": self.contract_revision,
            "schema_version": self.schema_version,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "geometry_revision": self.geometry_revision,
            "render_geometry_sha256": self.render_geometry_sha256,
            "coordinate_system": self.coordinate_system,
            "length_unit": self.length_unit,
            "segments": [item.to_payload() for item in self.segments],
            "joints": [item.to_payload() for item in self.joints],
        }

    def canonical_bytes(self) -> bytes:
        """RFC 8785 bytes for the complete bounded descriptor."""

        return rfc8785.dumps(self.to_payload())

    def validate_dynamic_pose_candidate(
        self,
        *,
        world_context: WorldPhysicalStepContext,
        poses: tuple[RenderLinkPose, ...],
    ) -> RenderDynamicPoseCandidate:
        """Validate World-supplied poses against this exact static subset.

        This is deliberately a candidate, not a committed-cut receipt. The
        caller must supply transforms computed by its physical solver; this
        method only validates, orders, and binds them to this morphology.
        """

        candidate = RenderDynamicPoseCandidate(
            body_id=self.body_id,
            embodiment_episode_id=self.embodiment_episode_id,
            morphology_revision=self.morphology_revision,
            geometry_revision=self.geometry_revision,
            render_geometry_sha256=self.render_geometry_sha256,
            source_world_id=world_context.world_id,
            physical_step_id=world_context.physical_step_id,
            environment_revision=world_context.environment_revision,
            solver_config_revision=world_context.solver_config_revision,
            source_causal_tick=world_context.source_causal_tick,
            target_causal_tick=world_context.target_causal_tick,
            poses=poses,
            expected_segment_ids=tuple(item.segment_id for item in self.segments),
        )
        self.validate_dynamic_pose_candidate_binding(candidate)
        if (
            world_context.body_id != self.body_id
            or world_context.embodiment_episode_id != self.embodiment_episode_id
            or world_context.morphology_revision != self.morphology_revision
        ):
            raise ValueError("World step context identity does not match static morphology")
        return candidate

    def validate_dynamic_pose_candidate_binding(
        self, candidate: RenderDynamicPoseCandidate
    ) -> None:
        """Reject candidate identities or link sets that differ from this descriptor."""

        if not isinstance(candidate, RenderDynamicPoseCandidate):
            raise TypeError("candidate must be a RenderDynamicPoseCandidate")
        expected = (
            self.body_id, self.embodiment_episode_id, self.morphology_revision,
            self.geometry_revision, self.render_geometry_sha256,
        )
        actual = (
            candidate.body_id, candidate.embodiment_episode_id,
            candidate.morphology_revision, candidate.geometry_revision,
            candidate.render_geometry_sha256,
        )
        if actual != expected:
            raise ValueError("dynamic pose candidate identity/revision does not match static morphology")
        if candidate.expected_segment_ids != tuple(item.segment_id for item in self.segments):
            raise ValueError("dynamic pose candidate renderable links do not match static morphology")

    @classmethod
    def from_payload(cls, payload: object) -> RenderMorphologyProjection:
        """Validate a closed descriptor payload and its render-only digest."""

        expected = {
            "contract_revision", "schema_version", "body_id", "embodiment_episode_id",
            "morphology_revision", "geometry_revision", "render_geometry_sha256",
            "coordinate_system", "length_unit", "segments", "joints",
        }
        if not isinstance(payload, Mapping) or set(payload) != expected:
            raise ValueError("invalid render morphology descriptor fields")
        raw_segments = payload["segments"]
        raw_joints = payload["joints"]
        if not isinstance(raw_segments, list) or len(raw_segments) > MAX_SEGMENTS:
            raise ValueError("segments must be a bounded array")
        if not isinstance(raw_joints, list) or len(raw_joints) > MAX_REVOLUTE_JOINTS:
            raise ValueError("joints must be a bounded array")
        segments = tuple(_parse_segment(item) for item in raw_segments)
        joints = tuple(_parse_joint(item) for item in raw_joints)
        return cls(
            contract_revision=payload["contract_revision"],
            schema_version=payload["schema_version"],
            body_id=payload["body_id"],
            embodiment_episode_id=payload["embodiment_episode_id"],
            morphology_revision=payload["morphology_revision"],
            geometry_revision=payload["geometry_revision"],
            render_geometry_sha256=payload["render_geometry_sha256"],
            coordinate_system=payload["coordinate_system"],
            length_unit=payload["length_unit"],
            segments=segments,
            joints=joints,
        )


@dataclass(frozen=True, slots=True)
class RenderLinkPose:
    """One solver-computed world-from-link transform for a renderable link."""

    segment_id: str
    translation_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        _identity(self.segment_id, "segment_id")
        translation = _vector(self.translation_m, 3, "translation_m")
        orientation = _vector(self.orientation_xyzw, 4, "orientation_xyzw")
        norm = math.sqrt(sum(value * value for value in orientation))
        if not math.isfinite(norm) or not math.isclose(
            norm, 1.0, rel_tol=0.0, abs_tol=QUATERNION_NORM_TOLERANCE
        ):
            raise ValueError("orientation_xyzw must be a unit quaternion")
        object.__setattr__(self, "translation_m", translation)
        object.__setattr__(self, "orientation_xyzw", orientation)

    def to_payload(self) -> dict[str, object]:
        return {
            "segment_id": self.segment_id,
            "translation_m": list(self.translation_m),
            "orientation_xyzw": list(self.orientation_xyzw),
        }


@dataclass(frozen=True, slots=True)
class RenderDynamicPoseCandidate:
    """Complete, validated same-step link poses; not evidence of World commit."""

    body_id: str
    embodiment_episode_id: str
    morphology_revision: str
    geometry_revision: str
    render_geometry_sha256: str
    source_world_id: str
    physical_step_id: str
    environment_revision: str
    solver_config_revision: str
    source_causal_tick: int
    target_causal_tick: int
    poses: tuple[RenderLinkPose, ...]
    expected_segment_ids: tuple[str, ...]
    # Internal validation aid; not serialized or interpreted as World proof.
    contract_revision: str = "embodiment.render_link_pose_candidate/v1"
    reference_frame: str = "physics3d.world"
    coordinate_system: str = COORDINATE_SYSTEM
    length_unit: str = LENGTH_UNIT

    def __post_init__(self) -> None:
        for field in (
            "body_id", "embodiment_episode_id", "morphology_revision",
            "geometry_revision", "source_world_id", "physical_step_id",
            "environment_revision", "solver_config_revision",
        ):
            _identity(getattr(self, field), field)
        if not isinstance(self.render_geometry_sha256, str) or not _SHA256_RE.fullmatch(self.render_geometry_sha256):
            raise ValueError("render_geometry_sha256 must be a lowercase SHA-256 digest")
        if self.contract_revision != "embodiment.render_link_pose_candidate/v1":
            raise ValueError("unsupported dynamic pose candidate revision")
        if self.reference_frame != "physics3d.world" or self.coordinate_system != COORDINATE_SYSTEM or self.length_unit != LENGTH_UNIT:
            raise ValueError("unsupported dynamic pose reference frame, basis, or unit")
        if (
            type(self.source_causal_tick) is not int
            or type(self.target_causal_tick) is not int
            or self.source_causal_tick < 0
            or self.target_causal_tick != self.source_causal_tick + 1
        ):
            raise ValueError("dynamic pose candidate must identify adjacent source and target ticks")
        if not isinstance(self.poses, tuple) or any(not isinstance(item, RenderLinkPose) for item in self.poses):
            raise ValueError("poses must be a tuple of RenderLinkPose values")
        if not isinstance(self.expected_segment_ids, tuple):
            raise ValueError("expected_segment_ids must be a tuple")
        expected = tuple(sorted(set(self.expected_segment_ids)))
        actual = tuple(item.segment_id for item in self.poses)
        if self.expected_segment_ids != expected or actual != expected:
            raise ValueError("dynamic poses must exactly match sorted renderable segment IDs")
        if len(actual) > MAX_SEGMENTS:
            raise ValueError("dynamic pose candidate exceeds render segment limit")
        if len(rfc8785.dumps(self.to_payload())) > MAX_DYNAMIC_POSE_BYTES:
            raise ValueError("canonical dynamic pose candidate exceeds byte limit")

    def to_payload(self) -> dict[str, object]:
        return {
            "contract_revision": self.contract_revision,
            "body_id": self.body_id,
            "embodiment_episode_id": self.embodiment_episode_id,
            "morphology_revision": self.morphology_revision,
            "geometry_revision": self.geometry_revision,
            "render_geometry_sha256": self.render_geometry_sha256,
            "source_world_id": self.source_world_id,
            "physical_step_id": self.physical_step_id,
            "environment_revision": self.environment_revision,
            "solver_config_revision": self.solver_config_revision,
            "source_causal_tick": self.source_causal_tick,
            "target_causal_tick": self.target_causal_tick,
            "reference_frame": self.reference_frame,
            "coordinate_system": self.coordinate_system,
            "length_unit": self.length_unit,
            "completeness": "complete",
            "poses": [item.to_payload() for item in self.poses],
        }

    def canonical_bytes(self) -> bytes:
        """Bounded candidate encoding; this is not a World cut proof digest."""

        return rfc8785.dumps(self.to_payload())


def _render_content_payload(
    segments: tuple[RenderSegment, ...], joints: tuple[RenderJoint, ...]
) -> dict[str, object]:
    return {
        "contract_revision": CONTRACT_REVISION,
        "schema_version": 1,
        "coordinate_system": COORDINATE_SYSTEM,
        "length_unit": LENGTH_UNIT,
        "segments": [item.to_payload() for item in segments],
        "joints": [item.to_payload() for item in joints],
    }


def _render_digest(content: Mapping[str, Any]) -> str:
    return hashlib.sha256(_DIGEST_PREFIX + rfc8785.dumps(dict(content))).hexdigest()


def _parse_segment(value: object) -> RenderSegment:
    expected = {"segment_id", "shape", "dimensions_m", "visual_origin_in_link_m"}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError("invalid render segment fields")
    return RenderSegment(
        segment_id=value["segment_id"],
        shape=value["shape"],
        dimensions_m=_vector(value["dimensions_m"], 3, "dimensions_m"),
        visual_origin_in_link_m=_vector(value["visual_origin_in_link_m"], 3, "visual_origin_in_link_m"),
    )


def _parse_joint(value: object) -> RenderJoint:
    expected = {
        "joint_id", "parent_link_id", "child_link_id", "joint_type",
        "joint_origin_in_parent_m", "axis_in_joint_frame",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError("invalid render joint fields")
    return RenderJoint(
        joint_id=value["joint_id"],
        parent_link_id=value["parent_link_id"],
        child_link_id=value["child_link_id"],
        joint_type=value["joint_type"],
        joint_origin_in_parent_m=_vector(value["joint_origin_in_parent_m"], 3, "joint_origin_in_parent_m"),
        axis_in_joint_frame=_vector(value["axis_in_joint_frame"], 3, "axis_in_joint_frame"),
    )


__all__ = [
    "CONTRACT_REVISION",
    "MAX_DESCRIPTOR_BYTES",
    "MAX_LINKS",
    "MAX_REVOLUTE_JOINTS",
    "MAX_SEGMENTS",
    "RenderJoint",
    "RenderMorphologyProjection",
    "RenderSegment",
]
