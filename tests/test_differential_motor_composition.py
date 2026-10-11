from types import SimpleNamespace

import pytest

from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.differential_motor_composition import (
    DifferentialMotorPair,
    EmbodimentDifferentialMotorBinding,
    compose_differential_motor_command,
)
from embodiment.physics3d.joint_torque import (
    EmbodimentJointTorqueBinding,
    JointTorqueChannelBinding,
    project_joint_torque_command,
)
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec


def morphology(revision: str = "morph-1") -> ActiveArticulatedMorphology:
    spec = ArticulatedBodySpec(
        body_kind="paired-motor-fixture", state_schema_version=1, spawn_height=0,
        base_link_name="root",
        joint_specs=(
            JointSpec("joint.left", (0, 1, 0), -1, 1, 2.0, 0.1, 2),
            JointSpec("joint.right", (1, 0, 0), -1, 1, 3.0, 0.1, 2),
        ),
        joint_topology=(
            JointTopology("joint.left", "root", "left", (0, 0, 0)),
            JointTopology("joint.right", "root", "right", (0, 0, 0)),
        ),
        segments={
            "root": SegmentSpec(1, (1, 1, 1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
            "left": SegmentSpec(1, (1, 1, 1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
            "right": SegmentSpec(1, (1, 1, 1), (0, 0, 0), (0.5, 0.5, 0.5, 1)),
        },
        contact_link_names=("left", "right"),
        structural_neighbour_names=(("root", "left"), ("root", "right")),
    )
    return ActiveArticulatedMorphology.from_spec(
        body_id="body-1", embodiment_episode_id="episode-1", morphology_revision=revision, spec=spec
    )


def command(channels=(), **changes):
    values = {
        "command_id": "command-1", "commitment_id": "commitment-1",
        "controller_id": "controller-1", "competence_id": None,
        "surface_fingerprint": "surface-1", "channels": tuple(channels),
        "issued_at_tick": 4, "embodiment_id": "episode-1",
    }
    values.update(changes)
    return SimpleNamespace(**values)


def mapping(morph=None):
    morph = morph or morphology()
    return EmbodimentDifferentialMotorBinding(
        "pair-binding-1", morph.body_id, morph.embodiment_episode_id,
        morph.morphology_revision, "surface-1",
        (
            DifferentialMotorPair("joint.left", "left+", "left-", 0.5),
            DifferentialMotorPair("joint.right", "right+", "right-", 0.25),
        ),
    )


def torque_binding(morph=None):
    morph = morph or morphology()
    return EmbodimentJointTorqueBinding(
        "torque-binding-1", morph.body_id, morph.embodiment_episode_id,
        morph.morphology_revision, "surface-1",
        (
            JointTorqueChannelBinding("joint.left.output", "joint.left", (0, 1, 0)),
            JointTorqueChannelBinding("joint.right.output", "joint.right", (1, 0, 0)),
        ),
    )


def project(command_value, morph=None, pair_binding=None, physical_binding=None):
    morph = morph or morphology()
    request = compose_differential_motor_command(
        command_value, pair_binding or mapping(morph), physical_binding or torque_binding(morph), morph
    )
    return request, project_joint_torque_command(request, physical_binding or torque_binding(morph), morph)


def test_composes_stable_differential_pair_to_typed_joint_torque_and_ignores_order():
    motor_command = command((("right-", 0.2), ("left+", 0.8), ("right+", 0.6), ("left-", 0.3)))
    request, result = project(motor_command)
    assert [(item.actuator_id, item.value, item.quantity, item.unit) for item in request.channels] == [
        ("joint.left.output", pytest.approx(0.5), "joint_torque", "N*m"),
        ("joint.right.output", pytest.approx(0.3), "joint_torque", "N*m"),
    ]
    assert [(item.joint_id, item.torque_nm) for item in result.channels] == [
        ("joint.left", pytest.approx(0.5)), ("joint.right", pytest.approx(0.3))
    ]
    permuted = command(tuple(reversed(motor_command.channels)))
    assert project(permuted) == (request, result)


def test_omitted_pair_is_no_command_but_explicit_zero_pair_is_neutral_request():
    omitted, omitted_candidate = project(command(()))
    assert omitted.channels == ()
    assert omitted_candidate.channels == ()

    explicit, explicit_candidate = project(command((("left+", 0.0), ("left-", 0.0))))
    assert [(c.value, c.unit) for c in explicit.channels] == [(0.0, "N*m")]
    assert [(c.torque_nm, c.neutral_nm) for c in explicit_candidate.channels] == [(0.0, 0.0)]


def test_equal_nonzero_pair_has_zero_net_physical_command_without_semantic_alias():
    request_value, candidate = project(command((("left+", 0.7), ("left-", 0.7))))
    assert request_value.channels[0].value == 0.0
    assert candidate.channels[0].torque_nm == 0.0
    # The emitted physical quantity is torque only; the source command remains distinct evidence.
    assert request_value.channels[0].quantity == "joint_torque"


def test_rejects_partial_pair_unknown_channels_bad_range_and_stale_binding():
    with pytest.raises(ValueError, match="incomplete differential pair"):
        project(command((("left+", 0.4),)))
    with pytest.raises(ValueError, match="outside the active differential binding"):
        project(command((("unbound", 0.4),)))
    with pytest.raises(ValueError, match="activation.*range"):
        project(command((("left+", 1.2), ("left-", 0.2))))
    baseline = mapping()
    over_scaled = EmbodimentDifferentialMotorBinding(
        baseline.binding_id, baseline.body_id, baseline.embodiment_episode_id,
        baseline.morphology_revision, baseline.source_surface_fingerprint,
        (DifferentialMotorPair("joint.left", "left+", "left-", 2.0), baseline.pairs[1]),
    )
    with pytest.raises(ValueError, match="mapped torque is outside"):
        project(command((("left+", 1.0), ("left-", 0.0))), pair_binding=over_scaled)
    with pytest.raises(ValueError, match="body, episode and morphology revision"):
        compose_differential_motor_command(
            command((("left+", 0.4), ("left-", 0.2))), mapping(morphology("old")),
            torque_binding(), morphology(),
        )


@pytest.mark.parametrize(
    ("body_id", "episode_id", "revision"),
    [("body-other", "episode-1", "morph-1"),
     ("body-1", "episode-other", "morph-1"),
     ("body-1", "episode-1", "morph-other")],
)
def test_rejects_binding_from_wrong_body_episode_or_morphology(body_id, episode_id, revision):
    active = morphology()
    stale = EmbodimentDifferentialMotorBinding(
        "stale-binding", body_id, episode_id, revision, "surface-1", mapping(active).pairs,
    )
    with pytest.raises(ValueError, match="body, episode and morphology revision"):
        compose_differential_motor_command(
            command((("left+", 0.4), ("left-", 0.2))), stale, torque_binding(active), active,
        )


def test_rejects_pair_mapping_not_matching_physical_binding():
    morph = morphology()
    wrong = EmbodimentJointTorqueBinding(
        "torque-binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("joint.left.output", "joint.left", (1, 0, 0)),
         JointTorqueChannelBinding("joint.right.output", "joint.right", (1, 0, 0))),
    )
    with pytest.raises(ValueError, match="axis differs"):
        compose_differential_motor_command(
            command((("left+", 0.4), ("left-", 0.2))), mapping(morph), wrong, morph
        )


def test_mapping_checkpoint_is_versioned_and_strict():
    original = mapping()
    assert EmbodimentDifferentialMotorBinding.from_bytes(original.to_bytes()) == original
    payload = original.to_checkpoint()
    payload["unknown"] = True
    import json

    with pytest.raises(ValueError, match="checkpoint fields"):
        EmbodimentDifferentialMotorBinding.from_bytes(json.dumps(payload).encode())


def test_mapping_checkpoint_rejects_duplicate_json_fields():
    with pytest.raises(ValueError, match="duplicate differential motor binding checkpoint field"):
        EmbodimentDifferentialMotorBinding.from_bytes(
            b'{"schema_version":1,"schema_version":1}'
        )
