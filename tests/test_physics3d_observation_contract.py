"""Tests for the migrated Physics3D coordinate declarations.

These assertions verify metadata only. They do not verify that a runtime emits
samples conforming to the declarations or that any physical simulation is valid.
"""

from dataclasses import replace

import pytest

from embodiment.physics3d.observation_contract import (
    PHYSICS3D_BODY_POSE_SEMANTICS,
    PHYSICS3D_JOINT_KINEMATICS_SEMANTICS,
    body_pose_semantics,
    joint_kinematics_semantics,
)
from embodiment.observation_family import (
    EMBODIMENT_BODY_POSE_FAMILY_V1,
    embodiment_body_pose_family_v1,
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


def test_body_pose_family_is_owner_authorized_and_revisioned() -> None:
    expected = {
        "family_id": "embodiment.body_pose",
        "semantic_revision": "v1",
        "authority": "embodiment",
        "epistemic_basis": "authoritative_state",
        "acquisition_basis": "embodiment_owner_state_projection",
        "subject_kind": "embodiment_body",
        "assertion": "current_adopted_base_body_pose",
        "value_structure": "position_and_orientation_as_one_claim",
        "position_unit": "m",
        "orientation_representation": "unit_quaternion_xyzw",
        "orientation_mapping": "body_frame_to_reference_frame",
        "orientation_convention": "right_handed_hamilton_q_v_q_conjugate",
        "reference_frame": "explicit_per_claim",
        "body_frame": "explicit_per_claim",
        "required_identity": "body_id+embodiment_episode_id+morphology_revision",
        "world_causal_tick_role": "correlation_context_only",
        "domain_time": "not_declared_by_this_family",
        "producer": "embodiment_owner_projection",
        "semantic_asserter": "embodiment_owner_boundary",
        "source_applicability": "adopted_body_episode_morphology_revision",
        "source_state_provenance": "sha256_of_canonical_embodiment_checkpoint_bytes_not_durability_claim",
        "physical_step_provenance": "physical_step_id+source_world_tick+environment_revision+solver_config_revision",
    }

    assert embodiment_body_pose_family_v1() == expected
    returned = embodiment_body_pose_family_v1()
    returned["authority"] = "world"
    assert embodiment_body_pose_family_v1() == expected
    assert EMBODIMENT_BODY_POSE_FAMILY_V1["authority"] == "embodiment"


def test_body_pose_family_matches_owner_projection_without_invented_domain_time() -> None:
    from embodiment.observation import BodyPoseSample
    from embodiment.physics3d.physical_transition import EmbodimentPhysicalState

    state = EmbodimentPhysicalState(
        world_id="world.owner-family",
        causal_tick=3,
        body_id="body.owner-family",
        embodiment_episode_id="episode.owner-family",
        morphology_revision="morphology.owner-family.v1",
        pose=BodyPoseSample(
            body_id="body.owner-family",
            reference_frame="frame.owner-family",
            body_frame="body.root",
            position_m=(1.0, 2.0, 3.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value="initial-state",
        ),
        linear_velocity_m_per_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )

    projection = state.body_pose_observation_projection()
    family = embodiment_body_pose_family_v1()

    assert family["authority"] == "embodiment"
    assert family["acquisition_basis"] == "embodiment_owner_state_projection"
    assert family["source_applicability"] == "adopted_body_episode_morphology_revision"
    assert projection.body_id and projection.embodiment_episode_id
    assert projection.morphology_revision
    assert projection.source_state_sha256 == state.checkpoint_digest
    assert projection.pose.position_m == (1.0, 2.0, 3.0)
    assert projection.pose.orientation_xyzw == (0.0, 0.0, 0.0, 1.0)
    assert projection.pose.reference_frame == "frame.owner-family"
    assert projection.pose.body_frame == "body.root"
    assert projection.world_id == "world.owner-family"
    assert projection.causal_tick == 3  # correlation only, not Embodiment domain time
    assert projection.physical_step_correlation is None


@pytest.mark.parametrize("digest", ["", "not-a-digest", "A" * 64])
def test_body_pose_projection_rejects_missing_or_malformed_source_provenance(
    digest: str,
) -> None:
    from embodiment.observation import BodyPoseSample
    from embodiment.physics3d.physical_transition import EmbodimentPhysicalState

    state = EmbodimentPhysicalState(
        world_id="world.owner-family",
        causal_tick=3,
        body_id="body.owner-family",
        embodiment_episode_id="episode.owner-family",
        morphology_revision="morphology.owner-family.v1",
        pose=BodyPoseSample(
            body_id="body.owner-family",
            reference_frame="frame.owner-family",
            body_frame="body.root",
            position_m=(1.0, 2.0, 3.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value="initial-state",
        ),
        linear_velocity_m_per_s=(0.0, 0.0, 0.0),
        angular_velocity_rad_per_s=(0.0, 0.0, 0.0),
    )
    projection = state.body_pose_observation_projection()

    with pytest.raises(ValueError, match="source_state_sha256"):
        replace(projection, source_state_sha256=digest)
