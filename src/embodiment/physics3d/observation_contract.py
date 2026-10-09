"""Physics3D conformance declaration for Embodiment Body Pose v1.

All canonical Physics3D geometric coordinates supplied by this package are
interpreted in metres. A caller using another unit must convert before entering
this apparatus contract.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

PHYSICS3D_BODY_POSE_SEMANTICS: Mapping[str, str] = MappingProxyType(
    {
        "position_unit": "m",
        "handedness": "right",
        "up_axis": "+z",
        "orientation": "xyzw",
        "reference_frame": "physics3d.world",
        "body_frame": "body.root",
        "contract_revision": "v1",
    }
)

PHYSICS3D_JOINT_KINEMATICS_SEMANTICS: Mapping[str, str] = MappingProxyType(
    {
        "joint_type": "revolute",
        "position_unit": "rad",
        "velocity_unit": "rad/s",
        "identity_scope": "body_local",
        "contract_revision": "v1",
    }
)


def body_pose_semantics() -> dict[str, str]:
    """Return a fresh canonical declaration suitable for exported physical state."""

    return dict(PHYSICS3D_BODY_POSE_SEMANTICS)


def joint_kinematics_semantics() -> dict[str, str]:
    """Return the current Physics3D revolute-joint conformance declaration."""

    return dict(PHYSICS3D_JOINT_KINEMATICS_SEMANTICS)


__all__ = [
    "PHYSICS3D_BODY_POSE_SEMANTICS",
    "PHYSICS3D_JOINT_KINEMATICS_SEMANTICS",
    "body_pose_semantics",
    "joint_kinematics_semantics",
]
