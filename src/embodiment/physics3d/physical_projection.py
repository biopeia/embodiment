"""Engine-neutral projection of an Embodiment body description and pose.

This is a value passed *to* a physical substrate. It is not a solver, a
semantic physics authority, or a body-state transition. Somatic physiology
that has no defined mechanical mapping is deliberately not projected.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_spec import (
    ArticulatedBodySpec,
    build_articulated_urdf,
)
from embodiment.physics3d.physical_transition import PhysicalStepCorrelation


@dataclass(frozen=True, slots=True)
class BodyPhysicalInput:
    """Immutable solver input assembled from owner-defined physical values.

    ``articulated_description`` is the snapshot of Embodiment-owned morphology
    (mass, segments and joints); root pose and root velocities are supplied by
    Embodiment. Velocities use m/s and rad/s in ``reference_frame``. The solver
    remains responsible for numerical execution and must return results for
    the owner to accept through a separate transition.
    """

    body_id: str
    correlation: PhysicalStepCorrelation
    body_kind: str
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    linear_velocity_m_per_s: tuple[float, float, float]
    angular_velocity_rad_per_s: tuple[float, float, float]
    articulated_description: str
    contact_link_names: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("linear_velocity_m_per_s", "angular_velocity_rad_per_s"):
            value = getattr(self, name)
            if not isinstance(value, tuple) or len(value) != 3:
                raise ValueError(f"{name} must be a 3-vector expressed in reference_frame")
            if any(
                isinstance(component, bool)
                or not isinstance(component, (int, float))
                or not math.isfinite(float(component))
                for component in value
            ):
                raise ValueError(f"{name} components must be finite numbers")


def project_body_physical_input(
    spec: ArticulatedBodySpec,
    pose: BodyPoseSample,
    *,
    correlation: PhysicalStepCorrelation,
    linear_velocity_m_per_s: tuple[float, float, float],
    angular_velocity_rad_per_s: tuple[float, float, float],
) -> BodyPhysicalInput:
    """Snapshot concrete morphology and a validated pose for a substrate.

    No energy, integrity, temperature, fatigue, damage or viability field is
    converted to mechanics here: the CURRENT model defines no mapping from
    those values to solver mass, geometry, force or constraint parameters.
    """

    if correlation.body_id != pose.body_id:
        raise ValueError("physical-step body identity does not match projected pose")
    return BodyPhysicalInput(
        body_id=pose.body_id,
        correlation=correlation,
        body_kind=spec.body_kind,
        reference_frame=pose.reference_frame,
        body_frame=pose.body_frame,
        position_m=pose.position_m,
        orientation_xyzw=pose.orientation_xyzw,
        linear_velocity_m_per_s=linear_velocity_m_per_s,
        angular_velocity_rad_per_s=angular_velocity_rad_per_s,
        articulated_description=build_articulated_urdf(spec),
        contact_link_names=tuple(spec.contact_link_names),
    )


__all__ = ["BodyPhysicalInput", "project_body_physical_input"]
