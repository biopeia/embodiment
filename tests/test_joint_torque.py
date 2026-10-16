import json
import math

import pytest

from embodiment.physics3d.articulated_state import ActiveArticulatedMorphology
from embodiment.physics3d.articulated_spec import ArticulatedBodySpec
from embodiment.physics3d.joint_torque import (
    EmbodimentJointTorqueBinding,
    JointTorqueChannelBinding,
    JointTorqueInputChannel,
    JointTorqueRequest,
    NoActuationProjection,
    project_no_actuation,
    project_joint_torque_command,
)
from embodiment.physics3d.mechanics import JointSpec, JointTopology, SegmentSpec


def morphology(revision: str = "morph-1") -> ActiveArticulatedMorphology:
    spec = ArticulatedBodySpec(
        body_kind="joint-torque-fixture", state_schema_version=1, spawn_height=0,
        base_link_name="root",
        joint_specs=(
            JointSpec("joint.left", (0.0, 1.0, 0.0), -1, 1, 2.0, 0.1, 2),
            JointSpec("joint.right", (1.0, 0.0, 0.0), -1, 1, 3.0, 0.1, 2),
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


def binding(morph: ActiveArticulatedMorphology | None = None) -> EmbodimentJointTorqueBinding:
    morph = morph or morphology()
    return EmbodimentJointTorqueBinding(
        "binding-1", morph.body_id, morph.embodiment_episode_id, morph.morphology_revision,
        "surface-1", (
            JointTorqueChannelBinding("motor-left", "joint.left", (0, 1, 0)),
            JointTorqueChannelBinding("motor-right", "joint.right", (1, 0, 0)),
        ),
    )


def request(channels=None, **changes) -> JointTorqueRequest:
    values = {
        "command_id": "cmd-1", "commitment_id": "commit-1", "controller_id": "controller-1",
        "competence_id": None, "surface_fingerprint": "surface-1",
        "channels": (JointTorqueInputChannel("motor-left", 1.5, "joint_torque", "N*m"),),
        "issued_at_tick": 3, "embodiment_id": "episode-1",
    }
    if channels is not None:
        values["channels"] = channels
    values.update(changes)
    return JointTorqueRequest(**values)


def test_projects_explicit_sparse_joint_torque_and_is_order_independent():
    morph = morphology()
    current = binding(morph)
    command = request((
        JointTorqueInputChannel("motor-left", 1.5, "joint_torque", "N*m"),
        JointTorqueInputChannel("motor-right", -2.0, "joint_torque", "N*m"),
    ))
    result = project_joint_torque_command(command, current, morph)
    permuted = EmbodimentJointTorqueBinding(
        current.binding_id, current.body_id, current.embodiment_episode_id, current.morphology_revision,
        current.source_surface_fingerprint, tuple(reversed(current.channels)),
    )
    assert result == project_joint_torque_command(command, permuted, morph)
    assert [(c.joint_id, c.torque_nm, c.unit) for c in result.channels] == [
        ("joint.left", 1.5, "N*m"), ("joint.right", -2.0, "N*m")
    ]
    first = result.channels[0]
    assert first.axis == (0.0, 1.0, 0.0)
    assert first.axis_frame_id == "joint-frame:joint.left@morph-1"
    assert (first.joint_parent_link_id, first.joint_child_link_id) == ("root", "left")
    assert first.positive_direction == "right_hand_about_declared_axis"
    assert (first.quantity, first.unit) == ("joint_torque", "N*m")
    assert (first.minimum_nm, first.neutral_nm, first.maximum_nm) == (-2, 0, 2)


def test_omitted_channel_remains_no_command():
    assert project_joint_torque_command(request(channels=()), binding(), morphology()).channels == ()


def test_projects_explicit_no_actuation_against_active_morphology():
    active = morphology()
    projection = project_no_actuation(binding(active), active, issued_at_tick=1224)
    assert projection == NoActuationProjection(
        "binding-1", binding(active).fingerprint, "body-1", "episode-1", "morph-1", 1224
    )


def test_no_actuation_rejects_stale_incomplete_or_invalid_projection():
    with pytest.raises(ValueError, match="body, episode and morphology revision"):
        project_no_actuation(binding(), morphology("morph-old"), issued_at_tick=1)
    incomplete = EmbodimentJointTorqueBinding(
        "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("motor-left", "joint.left", (0, 1, 0)),),
    )
    with pytest.raises(ValueError, match="cover every active joint"):
        project_no_actuation(incomplete, morphology(), issued_at_tick=1)
    with pytest.raises(ValueError, match="non-negative causal tick"):
        project_no_actuation(binding(), morphology(), issued_at_tick=-1)
    with pytest.raises(ValueError, match="non-negative causal tick"):
        NoActuationProjection("binding", "fingerprint", "body", "episode", "morph", -1)


def test_binding_checkpoint_is_strict_and_roundtrips():
    original = binding()
    assert EmbodimentJointTorqueBinding.from_bytes(original.to_bytes()) == original
    for mutation, message in [
        (lambda p: p.update(unknown=1), "checkpoint fields"),
        (lambda p: p.update(schema_version=2), "checkpoint fields"),
        (lambda p: p.update(fingerprint="0" * 64), "fingerprint mismatch"),
    ]:
        payload = original.to_checkpoint()
        mutation(payload)
        with pytest.raises(ValueError, match=message):
            EmbodimentJointTorqueBinding.from_bytes(json.dumps(payload).encode())


def test_rejects_stale_revision_axis_and_unrecognized_joint():
    with pytest.raises(ValueError, match="body, episode and morphology revision"):
        project_joint_torque_command(request(), binding(), morphology("morph-old"))
    stale_axis = EmbodimentJointTorqueBinding(
        "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("motor-left", "joint.left", (1, 0, 0)),
         JointTorqueChannelBinding("motor-right", "joint.right", (1, 0, 0))),
    )
    with pytest.raises(ValueError, match="axis differs"):
        project_joint_torque_command(request(), stale_axis, morphology())
    unknown_joint = EmbodimentJointTorqueBinding(
        "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("motor-left", "missing", (0, 1, 0)),
         JointTorqueChannelBinding("motor-right", "joint.right", (1, 0, 0))),
    )
    with pytest.raises(ValueError, match="outside active morphology"):
        project_joint_torque_command(request(), unknown_joint, morphology())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 2.01, -2.01, True])
def test_rejects_nonfinite_or_out_of_range_torque(value):
    if isinstance(value, bool) or not math.isfinite(value):
        with pytest.raises(ValueError):
            JointTorqueInputChannel("motor-left", value, "joint_torque", "N*m")
    else:
        channel = JointTorqueInputChannel("motor-left", value, "joint_torque", "N*m")
        with pytest.raises(ValueError):
            project_joint_torque_command(request((channel,)), binding(), morphology())


@pytest.mark.parametrize(("quantity", "unit"), [("force", "N"), ("joint_torque", "Nm")])
def test_rejects_misdeclared_physical_semantics(quantity, unit):
    with pytest.raises(ValueError, match="quantity|unit"):
        JointTorqueInputChannel("motor-left", 1.0, quantity, unit)


def test_rejects_untyped_command_without_relabeling_values():
    with pytest.raises(ValueError, match="explicitly typed"):
        project_joint_torque_command(object(), binding(), morphology())  # type: ignore[arg-type]


def test_rejects_duplicate_binding_identity_and_incomplete_joint_coverage():
    with pytest.raises(ValueError, match="joint ids must be unique"):
        EmbodimentJointTorqueBinding(
            "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
            (JointTorqueChannelBinding("motor-left", "joint.left", (0, 1, 0)),
             JointTorqueChannelBinding("motor-right", "joint.left", (0, 1, 0))),
        )
    incomplete = EmbodimentJointTorqueBinding(
        "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("motor-left", "joint.left", (0, 1, 0)),),
    )
    with pytest.raises(ValueError, match="cover every active joint"):
        project_joint_torque_command(request(), incomplete, morphology())


def test_rejects_stale_episode_and_surface():
    with pytest.raises(ValueError, match="different embodiment episode"):
        project_joint_torque_command(request(embodiment_id="episode-old"), binding(), morphology())
    with pytest.raises(ValueError, match="different actuator surface"):
        project_joint_torque_command(request(surface_fingerprint="old"), binding(), morphology())


def test_rejects_binding_for_wrong_body_and_unavailable_actuator():
    wrong_body = EmbodimentJointTorqueBinding(
        "binding-1", "body-other", "episode-1", "morph-1", "surface-1", binding().channels,
    )
    with pytest.raises(ValueError, match="body, episode and morphology revision"):
        project_joint_torque_command(request(), wrong_body, morphology())
    unavailable = EmbodimentJointTorqueBinding(
        "binding-1", "body-1", "episode-1", "morph-1", "surface-1",
        (JointTorqueChannelBinding("motor-left", "joint.left", (0, 1, 0), available=False),
         JointTorqueChannelBinding("motor-right", "joint.right", (1, 0, 0))),
    )
    with pytest.raises(ValueError, match="unavailable actuator"):
        project_joint_torque_command(request(), unavailable, morphology())
