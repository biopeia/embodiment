"""Engine-neutral descriptions of articulated physical bodies.

This module describes body morphology and emits a URDF representation. It does
not instantiate a solver, advance causal time, or own runtime body state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from embodiment.physics3d.mechanics import (
    BODY_MATERIAL,
    CARRIER_MASS,
    MECHANICAL_LIMIT_GUARD,
    JointSpec,
    JointTopology,
    SegmentSpec,
    SurfaceMaterial,
)

NAME_PREFIX = "body."


@dataclass(frozen=True, slots=True)
class FixedLinkTopology:
    parent_link: str
    child_link: str
    origin: tuple[float, float, float]


@dataclass(frozen=True, slots=True)
class ArticulatedBodySpec:
    body_kind: str
    state_schema_version: int
    spawn_height: float
    base_link_name: str
    joint_specs: tuple[JointSpec, ...]
    joint_topology: tuple[JointTopology, ...]
    segments: Mapping[str, SegmentSpec]
    contact_link_names: tuple[str, ...]
    structural_neighbour_names: tuple[tuple[str, str], ...]
    fixed_link_topology: tuple[FixedLinkTopology, ...] = ()
    body_material: SurfaceMaterial = BODY_MATERIAL
    fixed_base: bool = False

    @property
    def motor_dof(self) -> int:
        return len(self.joint_specs)

    @property
    def somatic_region_count(self) -> int:
        return 1 + len(self.contact_link_names)

    @property
    def physical_receptor_count(self) -> int:
        return self.motor_dof * 2 + 10 + self.somatic_region_count * 2 + 1

    @property
    def total_receptor_count(self) -> int:
        return self.physical_receptor_count + 4

    @property
    def effector_count(self) -> int:
        return self.motor_dof * 2

    def physical_receptor_ids(self) -> tuple[str, ...]:
        return tuple(f"rec.{i}" for i in range(self.physical_receptor_count))

    def interoceptive_receptor_ids(self) -> tuple[str, ...]:
        return tuple(
            f"rec.{i}"
            for i in range(self.physical_receptor_count, self.total_receptor_count)
        )

    def receptor_ids(self) -> tuple[str, ...]:
        return tuple(f"rec.{i}" for i in range(self.total_receptor_count))

    def effector_ids(self) -> tuple[str, ...]:
        return tuple(f"eff.{i}" for i in range(self.effector_count))


def _fmt(values: Sequence[float]) -> str:
    return " ".join(f"{float(value):.10g}" for value in values)


def _box_inertia(mass: float, size: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = size
    return (
        mass * (y * y + z * z) / 12.0,
        mass * (x * x + z * z) / 12.0,
        mass * (x * x + y * y) / 12.0,
    )


def _segment_link_xml(name: str, segment: SegmentSpec) -> str:
    ixx, iyy, izz = _box_inertia(segment.mass, segment.size)
    return f"""
  <link name="{name}">
    <inertial>
      <origin xyz="{_fmt(segment.origin)}" rpy="0 0 0"/>
      <mass value="{segment.mass:.10g}"/>
      <inertia ixx="{ixx:.10g}" ixy="0" ixz="0" iyy="{iyy:.10g}" iyz="0" izz="{izz:.10g}"/>
    </inertial>
    <visual>
      <origin xyz="{_fmt(segment.origin)}" rpy="0 0 0"/>
      <geometry><box size="{_fmt(segment.size)}"/></geometry>
      <material name="{name}_material"><color rgba="{_fmt(segment.color)}"/></material>
    </visual>
    <collision>
      <origin xyz="{_fmt(segment.origin)}" rpy="0 0 0"/>
      <geometry><box size="{_fmt(segment.size)}"/></geometry>
    </collision>
  </link>"""


def _carrier_link_xml(name: str) -> str:
    return f"""
  <link name="{name}">
    <inertial>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <mass value="{CARRIER_MASS:.10g}"/>
      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
    </inertial>
  </link>"""


def _mechanical_joint_limits(spec: JointSpec) -> tuple[float, float]:
    span = spec.upper - spec.lower
    guard = min(MECHANICAL_LIMIT_GUARD, span * 0.1)
    return spec.lower + guard, spec.upper - guard


def build_articulated_urdf(spec: ArticulatedBodySpec) -> str:
    """Build a stable URDF description without loading an engine runtime."""
    if len(spec.joint_specs) != len(spec.joint_topology):
        raise ValueError("joint specs/topology length mismatch")
    if tuple(item.joint_name for item in spec.joint_topology) != tuple(
        item.name for item in spec.joint_specs
    ):
        raise ValueError("joint topology order must match joint specs")

    link_names = dict.fromkeys(
        (
            spec.base_link_name,
            *(item.child_link for item in spec.joint_topology),
            *(item.child_link for item in spec.fixed_link_topology),
        )
    )
    link_xml = [
        _segment_link_xml(name, spec.segments[name])
        if name in spec.segments
        else _carrier_link_xml(name)
        for name in link_names
    ]
    by_name = {item.name: item for item in spec.joint_specs}
    joint_xml: list[str] = []
    for topo in spec.joint_topology:
        joint = by_name[topo.joint_name]
        lower, upper = _mechanical_joint_limits(joint)
        joint_xml.append(
            f"""
  <joint name="{joint.name}" type="revolute">
    <parent link="{topo.parent_link}"/>
    <child link="{topo.child_link}"/>
    <origin xyz="{_fmt(topo.origin)}" rpy="0 0 0"/>
    <axis xyz="{_fmt(joint.axis)}"/>
    <limit lower="{lower:.12g}" upper="{upper:.12g}" effort="{joint.max_motor_torque:.12g}" velocity="{joint.max_velocity:.12g}"/>
    <dynamics damping="{joint.passive_damping:.12g}" friction="0"/>
  </joint>"""
        )
    for topo in spec.fixed_link_topology:
        joint_xml.append(
            f'''\n  <joint name="{topo.child_link}_fixed" type="fixed">
    <parent link="{topo.parent_link}"/>
    <child link="{topo.child_link}"/>
    <origin xyz="{_fmt(topo.origin)}" rpy="0 0 0"/>
  </joint>'''
        )
    return (
        '<?xml version="1.0"?>\n'
        f'<robot name="body_{spec.body_kind.replace("-", "_")}">'
        + "".join(link_xml)
        + "".join(joint_xml)
        + "\n</robot>\n"
    )
