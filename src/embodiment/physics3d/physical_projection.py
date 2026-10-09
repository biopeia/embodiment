"""Engine-neutral projection of an Embodiment body description and pose.

This is a value passed *to* a physical substrate. It is not a solver, a
semantic physics authority, or a body-state transition. Somatic physiology
that has no defined mechanical mapping is deliberately not projected.
"""

from __future__ import annotations

from dataclasses import dataclass

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.articulated_spec import (
    ArticulatedBodySpec,
    build_articulated_urdf,
)


@dataclass(frozen=True, slots=True)
class BodyPhysicalInput:
    """Immutable solver input assembled from owner-defined physical values.

    ``articulated_description`` is the snapshot of Embodiment-owned morphology
    (mass, segments and joints); root pose is the supplied Embodiment pose
    sample. The solver remains responsible for numerical execution and must
    return results for the owner to accept through a separate transition.
    """

    body_id: str
    body_kind: str
    reference_frame: str
    body_frame: str
    position_m: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]
    articulated_description: str
    contact_link_names: tuple[str, ...]


def project_body_physical_input(
    spec: ArticulatedBodySpec,
    pose: BodyPoseSample,
) -> BodyPhysicalInput:
    """Snapshot concrete morphology and a validated pose for a substrate.

    No energy, integrity, temperature, fatigue, damage or viability field is
    converted to mechanics here: the CURRENT model defines no mapping from
    those values to solver mass, geometry, force or constraint parameters.
    """

    return BodyPhysicalInput(
        body_id=pose.body_id,
        body_kind=spec.body_kind,
        reference_frame=pose.reference_frame,
        body_frame=pose.body_frame,
        position_m=pose.position_m,
        orientation_xyzw=pose.orientation_xyzw,
        articulated_description=build_articulated_urdf(spec),
        contact_link_names=tuple(spec.contact_link_names),
    )


__all__ = ["BodyPhysicalInput", "project_body_physical_input"]
