"""Engine-neutral descriptions of articulated physical bodies.

This module describes body morphology and emits a URDF representation. It does
not instantiate a solver, advance causal time, or own runtime body state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math

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


def articulated_body_spec_payload(spec: ArticulatedBodySpec) -> dict[str, object]:
    """Return the complete, identity-stable representation of a body spec.

    This is an Embodiment checkpoint value, not an engine wire format. Mapping
    keys are sorted during encoding; sequences retain their declared order.
    """

    if not isinstance(spec, ArticulatedBodySpec):
        raise ValueError("articulated morphology must be an ArticulatedBodySpec")
    return {
        "schema_version": 1,
        "body_kind": spec.body_kind,
        "state_schema_version": spec.state_schema_version,
        "spawn_height": float(spec.spawn_height),
        "base_link_name": spec.base_link_name,
        "joint_specs": [
            {
                "name": item.name,
                "axis": [float(value) for value in item.axis],
                "lower": float(item.lower),
                "upper": float(item.upper),
                "max_motor_torque": float(item.max_motor_torque),
                "passive_damping": float(item.passive_damping),
                "max_velocity": float(item.max_velocity),
            }
            for item in spec.joint_specs
        ],
        "joint_topology": [
            {
                "joint_name": item.joint_name,
                "parent_link": item.parent_link,
                "child_link": item.child_link,
                "origin": [float(value) for value in item.origin],
            }
            for item in spec.joint_topology
        ],
        "segments": {
            name: {
                "mass": float(item.mass),
                "size": [float(value) for value in item.size],
                "origin": [float(value) for value in item.origin],
                "color": [float(value) for value in item.color],
            }
            for name, item in sorted(spec.segments.items())
        },
        "contact_link_names": list(spec.contact_link_names),
        "structural_neighbour_names": [list(item) for item in spec.structural_neighbour_names],
        "fixed_link_topology": [
            {
                "parent_link": item.parent_link,
                "child_link": item.child_link,
                "origin": [float(value) for value in item.origin],
            }
            for item in spec.fixed_link_topology
        ],
        "body_material": {
            "lateral_friction": float(spec.body_material.lateral_friction),
            "spinning_friction": float(spec.body_material.spinning_friction),
            "rolling_friction": float(spec.body_material.rolling_friction),
            "restitution": float(spec.body_material.restitution),
            "linear_damping": float(spec.body_material.linear_damping),
            "angular_damping": float(spec.body_material.angular_damping),
        },
        "fixed_base": spec.fixed_base,
    }


def articulated_body_spec_bytes(spec: ArticulatedBodySpec) -> bytes:
    """Encode every declared morphology field as deterministic strict JSON."""

    try:
        return json.dumps(
            articulated_body_spec_payload(spec),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("invalid articulated body specification") from exc


def articulated_body_spec_sha256(spec: ArticulatedBodySpec) -> str:
    return hashlib.sha256(articulated_body_spec_bytes(spec)).hexdigest()


def restore_articulated_body_spec(encoded: object) -> ArticulatedBodySpec:
    """Decode a closed-schema body specification from an owner checkpoint."""

    from embodiment.physics3d.mechanics import SurfaceMaterial

    if not isinstance(encoded, dict):
        raise ValueError("articulated body specification must be an object")
    expected = {
        "schema_version", "body_kind", "state_schema_version", "spawn_height",
        "base_link_name", "joint_specs", "joint_topology", "segments",
        "contact_link_names", "structural_neighbour_names", "fixed_link_topology",
        "body_material", "fixed_base",
    }
    if set(encoded) != expected or type(encoded["schema_version"]) is not int or encoded["schema_version"] != 1:
        raise ValueError("unsupported articulated body specification schema or fields")
    if type(encoded["state_schema_version"]) is not int or encoded["state_schema_version"] < 1:
        raise ValueError("state_schema_version must be a positive integer")
    if type(encoded["fixed_base"]) is not bool:
        raise ValueError("fixed_base must be boolean")
    body_kind = _spec_identity(encoded["body_kind"], "body_kind")
    base_link_name = _spec_identity(encoded["base_link_name"], "base_link_name")
    spawn_height = _spec_number(encoded["spawn_height"], "spawn_height")
    joint_specs = tuple(
        JointSpec(
            name=_spec_identity(item["name"], "joint name"),
            axis=_spec_vector(item["axis"], 3, "joint axis"),
            lower=_spec_number(item["lower"], "joint lower"),
            upper=_spec_number(item["upper"], "joint upper"),
            max_motor_torque=_spec_number(item["max_motor_torque"], "joint max_motor_torque"),
            passive_damping=_spec_number(item["passive_damping"], "joint passive_damping"),
            max_velocity=_spec_number(item["max_velocity"], "joint max_velocity"),
        )
        for item in _spec_array(encoded["joint_specs"], "joint_specs", {
            "name", "axis", "lower", "upper", "max_motor_torque", "passive_damping", "max_velocity",
        })
    )
    joint_topology = tuple(
        JointTopology(
            joint_name=_spec_identity(item["joint_name"], "joint_name"),
            parent_link=_spec_identity(item["parent_link"], "parent_link"),
            child_link=_spec_identity(item["child_link"], "child_link"),
            origin=_spec_vector(item["origin"], 3, "joint origin"),
        )
        for item in _spec_array(encoded["joint_topology"], "joint_topology", {
            "joint_name", "parent_link", "child_link", "origin",
        })
    )
    raw_segments = encoded["segments"]
    if not isinstance(raw_segments, dict) or not all(isinstance(key, str) for key in raw_segments):
        raise ValueError("segments must be an object keyed by stable link identity")
    segments = {}
    for name, item in raw_segments.items():
        if not isinstance(item, dict) or set(item) != {"mass", "size", "origin", "color"}:
            raise ValueError("invalid segment specification fields")
        identity = _spec_identity(name, "segment name")
        if identity in segments:
            raise ValueError("segment identities collide after normalization")
        segments[identity] = SegmentSpec(
            mass=_spec_number(item["mass"], "segment mass"),
            size=_spec_vector(item["size"], 3, "segment size"),
            origin=_spec_vector(item["origin"], 3, "segment origin"),
            color=_spec_vector(item["color"], 4, "segment color"),
        )
    contact = tuple(_spec_identity(value, "contact link") for value in _spec_string_array(encoded["contact_link_names"], "contact_link_names"))
    raw_neighbours = encoded["structural_neighbour_names"]
    if not isinstance(raw_neighbours, list):
        raise ValueError("structural_neighbour_names must be an array")
    neighbours = tuple(
        (_spec_identity(item[0], "neighbour link"), _spec_identity(item[1], "neighbour link"))
        for item in raw_neighbours
        if isinstance(item, list) and len(item) == 2
    )
    if len(neighbours) != len(raw_neighbours):
        raise ValueError("each structural neighbour relation must contain two identities")
    fixed_topology = tuple(
        FixedLinkTopology(
            parent_link=_spec_identity(item["parent_link"], "fixed parent link"),
            child_link=_spec_identity(item["child_link"], "fixed child link"),
            origin=_spec_vector(item["origin"], 3, "fixed link origin"),
        )
        for item in _spec_array(encoded["fixed_link_topology"], "fixed_link_topology", {
            "parent_link", "child_link", "origin",
        })
    )
    material = encoded["body_material"]
    material_keys = {
        "lateral_friction", "spinning_friction", "rolling_friction", "restitution",
        "linear_damping", "angular_damping",
    }
    if not isinstance(material, dict) or set(material) != material_keys:
        raise ValueError("invalid body material specification fields")
    return ArticulatedBodySpec(
        body_kind=body_kind,
        state_schema_version=encoded["state_schema_version"],
        spawn_height=spawn_height,
        base_link_name=base_link_name,
        joint_specs=joint_specs,
        joint_topology=joint_topology,
        segments=segments,
        contact_link_names=contact,
        structural_neighbour_names=neighbours,
        fixed_link_topology=fixed_topology,
        body_material=SurfaceMaterial(**{
            key: _spec_number(material[key], f"body_material.{key}") for key in material_keys
        }),
        fixed_base=encoded["fixed_base"],
    )


def _spec_identity(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty identity")
    return value.strip()


def _spec_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _spec_vector(value: object, length: int, label: str) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must contain exactly {length} values")
    return tuple(_spec_number(item, label) for item in value)


def _spec_array(value: object, label: str, keys: set[str]) -> list[dict[str, object]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) or set(item) != keys for item in value):
        raise ValueError(f"invalid {label} schema")
    return value


def _spec_string_array(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be an array of identities")
    return value


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
