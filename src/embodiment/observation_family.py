"""Embodiment-owned semantic-family declarations for passive projections.

These declarations describe meaning and are independent of Observation's
record model, transport, or delivery. They do not authorize publication.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping


EMBODIMENT_BODY_POSE_FAMILY_V1: Mapping[str, str] = MappingProxyType(
    {
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
)


def embodiment_body_pose_family_v1() -> dict[str, str]:
    """Return the Embodiment-approved BodyPose family declaration."""

    return dict(EMBODIMENT_BODY_POSE_FAMILY_V1)


__all__ = [
    "EMBODIMENT_BODY_POSE_FAMILY_V1",
    "embodiment_body_pose_family_v1",
]
