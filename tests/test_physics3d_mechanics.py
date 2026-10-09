from dataclasses import FrozenInstanceError

import pytest

from embodiment.physics3d.mechanics import (
    BODY_MATERIAL,
    CARRIER_MASS,
    GROUND_MATERIAL,
    JointSpec,
    MotorBinding,
    SegmentSpec,
)


def test_physical_specifications_are_immutable_value_objects() -> None:
    joint = JointSpec("joint.0", (0.0, 0.0, 1.0), -1.0, 1.0, 2.0, 0.1, 3.0)
    segment = SegmentSpec(1.0, (0.1, 0.2, 0.3), (0.0, 0.0, 0.0), (0.2, 0.3, 0.4, 1.0))
    binding = MotorBinding(0, "eff.0", "eff.1")

    assert joint.name == "joint.0"
    assert segment.mass == 1.0
    assert binding.joint_index == 0
    with pytest.raises(FrozenInstanceError):
        joint.name = "renamed"  # type: ignore[misc]


def test_material_and_carrier_constants_are_physical_parameters() -> None:
    assert BODY_MATERIAL.lateral_friction > 0
    assert GROUND_MATERIAL.lateral_friction > BODY_MATERIAL.lateral_friction
    assert CARRIER_MASS > 0
