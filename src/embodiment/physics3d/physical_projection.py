"""Engine-neutral projection of Embodiment-owned articulated body state.

The projection is assembled from one validated owner state, rather than
independently supplied pose, velocity, morphology, and joint values. It is a
solver input, not a solver, semantic physics authority, or state transition.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from embodiment.physics3d.articulated_spec import build_articulated_urdf
from embodiment.physics3d.articulated_state import (
    ArticulatedEmbodimentPhysicalState,
    JointKinematicState,
    JointRange,
)
from embodiment.physics3d.mechanics import SurfaceMaterial
from embodiment.physics3d.physical_transition import PhysicalStepCorrelation


@dataclass(frozen=True, slots=True)
class BodyPhysicalInput:
    """Immutable numerical input projected from one owner-held body state.

    Root position and geometry origins are metres. Root orientation uses xyzw.
    Linear/angular root velocities use m/s and rad/s in ``reference_frame``.
    Joint positions and velocities use radians and rad/s, keyed by stable
    ``joint_id``. ``morphology_revision`` identifies the active owner revision;
    ``morphology_sha256`` identifies its complete declared content.

    ``body_material`` and ``fixed_base`` are copied from the active morphology
    descriptor so substrate adapters do not have to infer omitted morphology
    properties from a different source. Their detailed numerical interpretation
    remains the responsibility of the solver adapter contract.
    """

    body_id: str
    correlation: PhysicalStepCorrelation
    morphology_revision: str
    morphology_sha256: str
    body_kind: str
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    linear_velocity_m_per_s: tuple[float, float, float]
    angular_velocity_rad_per_s: tuple[float, float, float]
    joint_ranges: tuple[JointRange, ...]
    joints: tuple[JointKinematicState, ...]
    joint_position_unit: str
    joint_velocity_unit: str
    articulated_description: str
    contact_link_names: tuple[str, ...]
    body_material: SurfaceMaterial
    fixed_base: bool

    def __post_init__(self) -> None:
        for name in (
            "body_id", "morphology_revision", "body_kind", "reference_frame",
            "body_frame", "articulated_description",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
            object.__setattr__(self, name, value.strip())
        if not isinstance(self.correlation, PhysicalStepCorrelation):
            raise ValueError("correlation must be a physical-step correlation")
        if self.body_id != self.correlation.body_id:
            raise ValueError("body identity differs from physical-step correlation")
        if self.morphology_revision != self.correlation.morphology_revision:
            raise ValueError("morphology revision differs from physical-step correlation")
        if (
            not isinstance(self.morphology_sha256, str)
            or len(self.morphology_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.morphology_sha256)
        ):
            raise ValueError("morphology_sha256 must be a lowercase SHA-256 digest")
        for name, size in (
            ("position_m", 3),
            ("orientation_xyzw", 4),
            ("linear_velocity_m_per_s", 3),
            ("angular_velocity_rad_per_s", 3),
        ):
            value = getattr(self, name)
            if not isinstance(value, tuple) or len(value) != size:
                raise ValueError(f"{name} must be a {size}-value tuple")
            if any(
                isinstance(component, bool)
                or not isinstance(component, (int, float))
                or not math.isfinite(float(component))
                for component in value
            ):
                raise ValueError(f"{name} values must be finite numbers")
        if self.orientation_xyzw and abs(sum(float(v) ** 2 for v in self.orientation_xyzw) - 1.0) > 1e-5:
            raise ValueError("orientation_xyzw must be a unit quaternion")
        if self.joint_position_unit != "rad" or self.joint_velocity_unit != "rad/s":
            raise ValueError("unsupported projected joint units")
        if not isinstance(self.joints, tuple) or any(
            not isinstance(item, JointKinematicState) for item in self.joints
        ):
            raise ValueError("joints must be a tuple of owner-defined joint states")
        if not isinstance(self.joint_ranges, tuple) or any(
            not isinstance(item, JointRange) for item in self.joint_ranges
        ):
            raise ValueError("joint_ranges must be a tuple of owner-defined joint ranges")
        range_ids = tuple(item.joint_id for item in self.joint_ranges)
        if len(range_ids) != len(set(range_ids)) or range_ids != tuple(sorted(range_ids)):
            raise ValueError("projected joint ranges must have unique, stable sorted identities")
        joint_ids = tuple(item.joint_id for item in self.joints)
        if len(joint_ids) != len(set(joint_ids)) or joint_ids != tuple(sorted(joint_ids)):
            raise ValueError("projected joints must have unique, stable sorted identities")
        if joint_ids != range_ids:
            raise ValueError("projected joint identities must exactly match active morphology")
        ranges_by_id = {item.joint_id: item for item in self.joint_ranges}
        for joint in self.joints:
            limits = ranges_by_id[joint.joint_id]
            if not limits.lower_rad <= joint.position_rad <= limits.upper_rad:
                raise ValueError(f"joint {joint.joint_id!r} position is outside projected range")
            if abs(joint.velocity_rad_per_s) > limits.max_velocity_rad_per_s:
                raise ValueError(f"joint {joint.joint_id!r} velocity exceeds projected limit")
        if not isinstance(self.contact_link_names, tuple) or any(
            not isinstance(value, str) or not value.strip() for value in self.contact_link_names
        ):
            raise ValueError("contact_link_names must contain explicit link identities")
        if len(self.contact_link_names) != len(set(self.contact_link_names)):
            raise ValueError("contact_link_names must be unique")
        if not isinstance(self.body_material, SurfaceMaterial):
            raise ValueError("body_material must be the active morphology surface material")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in (
                self.body_material.lateral_friction,
                self.body_material.spinning_friction,
                self.body_material.rolling_friction,
                self.body_material.restitution,
                self.body_material.linear_damping,
                self.body_material.angular_damping,
            )
        ):
            raise ValueError("body_material coefficients must be finite numbers")
        if not isinstance(self.fixed_base, bool):
            raise ValueError("fixed_base must be boolean")


def project_body_physical_input(
    state: ArticulatedEmbodimentPhysicalState,
    *,
    correlation: PhysicalStepCorrelation,
) -> BodyPhysicalInput:
    """Project root and joint state from one bound Embodiment-owned value.

    The correlation names the proposed physical execution at the source tick.
    This function verifies that it describes the exact body state being
    projected; it does not authenticate World's authorization. That separate
    cross-owner adoption/authorization contract remains outside this package.
    """

    if not isinstance(state, ArticulatedEmbodimentPhysicalState):
        raise ValueError("physical projection requires an Embodiment-owned articulated state")
    if not isinstance(correlation, PhysicalStepCorrelation):
        raise ValueError("physical projection requires an explicit physical-step correlation")
    root = state.root
    morphology = state.morphology
    expected = (
        root.world_id,
        root.causal_tick,
        root.body_id,
        root.embodiment_episode_id,
        root.morphology_revision,
    )
    actual = (
        correlation.world_id,
        correlation.causal_tick,
        correlation.body_id,
        correlation.embodiment_episode_id,
        correlation.morphology_revision,
    )
    if actual != expected:
        raise ValueError("physical-step correlation does not match the source Embodiment state")
    if (
        morphology.body_id != root.body_id
        or morphology.embodiment_episode_id != root.embodiment_episode_id
        or morphology.morphology_revision != root.morphology_revision
    ):
        raise ValueError("active morphology does not match the source Embodiment state")

    spec = morphology.spec
    return BodyPhysicalInput(
        body_id=root.body_id,
        correlation=correlation,
        morphology_revision=morphology.morphology_revision,
        morphology_sha256=morphology.morphology_sha256,
        body_kind=spec.body_kind,
        reference_frame=root.pose.reference_frame,
        body_frame=root.pose.body_frame,
        position_m=root.pose.position_m,
        orientation_xyzw=root.pose.orientation_xyzw,
        linear_velocity_m_per_s=root.linear_velocity_m_per_s,
        angular_velocity_rad_per_s=root.angular_velocity_rad_per_s,
        joint_ranges=morphology.joint_ranges,
        joints=state.joints,
        joint_position_unit="rad",
        joint_velocity_unit="rad/s",
        articulated_description=build_articulated_urdf(spec),
        contact_link_names=tuple(spec.contact_link_names),
        body_material=spec.body_material,
        fixed_base=spec.fixed_base,
    )


__all__ = ["BodyPhysicalInput", "project_body_physical_input"]
