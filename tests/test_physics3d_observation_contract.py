"""Tests for the migrated Physics3D coordinate declarations.

These assertions verify metadata only. They do not verify that a runtime emits
samples conforming to the declarations or that any physical simulation is valid.
"""

from embodiment.physics3d.observation_contract import (
    PHYSICS3D_BODY_POSE_SEMANTICS,
    PHYSICS3D_JOINT_KINEMATICS_SEMANTICS,
    body_pose_semantics,
    joint_kinematics_semantics,
)


def test_body_pose_semantics_are_canonical_and_copied() -> None:
    expected = {
        "position_unit": "m",
        "handedness": "right",
        "up_axis": "+z",
        "orientation": "xyzw",
        "reference_frame": "physics3d.world",
        "body_frame": "body.root",
        "contract_revision": "v1",
    }

    assert body_pose_semantics() == expected
    returned = body_pose_semantics()
    returned["position_unit"] = "cm"
    assert body_pose_semantics() == expected
    assert PHYSICS3D_BODY_POSE_SEMANTICS["position_unit"] == "m"


def test_joint_kinematics_semantics_are_canonical_and_copied() -> None:
    expected = {
        "joint_type": "revolute",
        "position_unit": "rad",
        "velocity_unit": "rad/s",
        "identity_scope": "body_local",
        "contract_revision": "v1",
    }

    assert joint_kinematics_semantics() == expected
    returned = joint_kinematics_semantics()
    returned["position_unit"] = "degree"
    assert joint_kinematics_semantics() == expected
    assert PHYSICS3D_JOINT_KINEMATICS_SEMANTICS["position_unit"] == "rad"
