"""Types and constants shared by every Physics3D body.

Human-readable anatomy exists only inside the apparatus. The organism sees
opaque ``rec.N`` / ``eff.N`` channels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

JOINT_LIMIT_SOLVER_TOLERANCE = math.radians(0.5)
MECHANICAL_LIMIT_GUARD = math.radians(2.0)
END_RANGE_MARGIN = math.radians(6.0)
END_RANGE_STIFFNESS = 18.0
END_RANGE_DAMPING = 1.5
CARRIER_MASS = 0.05


@dataclass(frozen=True, slots=True)
class MotorBinding:
    joint_index: int
    positive_port: str
    negative_port: str


@dataclass(frozen=True, slots=True)
class ActuatorWork:
    positive_j: float
    negative_j: float
    absolute_j: float
    net_j: float


@dataclass(frozen=True, slots=True)
class SurfaceMaterial:
    lateral_friction: float
    spinning_friction: float
    rolling_friction: float
    restitution: float
    linear_damping: float
    angular_damping: float


@dataclass(frozen=True, slots=True)
class JointLimit:
    lower: float
    upper: float


@dataclass(frozen=True, slots=True)
class JointSpec:
    name: str
    axis: tuple[float, float, float]
    lower: float
    upper: float
    max_motor_torque: float
    passive_damping: float
    max_velocity: float


@dataclass(frozen=True, slots=True)
class SegmentSpec:
    mass: float
    size: tuple[float, float, float]
    origin: tuple[float, float, float]
    color: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class JointTopology:
    joint_name: str
    parent_link: str
    child_link: str
    origin: tuple[float, float, float]


BODY_MATERIAL = SurfaceMaterial(0.80, 0.02, 0.002, 0.02, 0.03, 0.05)
GROUND_MATERIAL = SurfaceMaterial(0.95, 0.03, 0.002, 0.0, 0.0, 0.0)
