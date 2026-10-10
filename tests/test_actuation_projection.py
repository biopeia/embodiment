from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.actuator_binding import ActuatorChannelBinding, EmbodimentActuatorBinding
from embodiment.physics3d.actuation_projection import project_motor_command


@dataclass(frozen=True)
class Effector:
    effector_id: str
    quantity: str = "normalized_command"
    unit: str = "1"
    minimum: float = 0.0
    neutral: float = 0.0
    maximum: float = 1.0
    saturation: str = "reject"


@dataclass(frozen=True)
class Morphology:
    body_id: str = "body-1"
    embodiment_episode_id: str = "episode-1"
    morphology_revision: str = "morphology-r1"
    effectors: tuple[Effector, ...] = (
        Effector("elbow.flexor", minimum=0.2, neutral=0.4),
        Effector("wrist.rotator"),
    )


@dataclass(frozen=True)
class Command:
    command_id: str = "command-1"
    commitment_id: str = "commitment-1"
    controller_id: str = "controller-1"
    competence_id: str | None = None
    surface_fingerprint: str = "organism-surface-fp"
    channels: tuple[tuple[str, float], ...] = (("actuator-a", 0.5),)
    issued_at_tick: int = 7
    embodiment_id: str | None = "episode-1"


def make_binding(morphology: Morphology = Morphology(), *, channels=None):
    if channels is None:
        channels = (
            ActuatorChannelBinding("actuator-a", "elbow.flexor", "normalized_activation", "normalized_command", "1", 0.2, 0.4, 1.0, "reject"),
            ActuatorChannelBinding("actuator-b", "wrist.rotator", "normalized_activation", "normalized_command", "1", 0.0, 0.0, 1.0, "reject"),
        )
    return EmbodimentActuatorBinding(
        "binding-1", morphology.body_id, morphology.embodiment_episode_id,
        morphology.morphology_revision, "organism-surface-fp", tuple(channels),
    )


def inputs(command=None, binding=None, morphology=Morphology()):
    binding = binding or make_binding(morphology)
    command = command or Command(surface_fingerprint=binding.source_surface_fingerprint)
    if not command.surface_fingerprint:
        command = replace(command, surface_fingerprint=binding.source_surface_fingerprint)
    pose = BodyPoseSample(
        morphology.body_id, "physics3d.world", "body.root", (0, 0, 0), (0, 0, 0, 1), "test", 1
    )
    checkpoint = SimpleNamespace(body_id=morphology.body_id, episode_id=morphology.embodiment_episode_id)
    return command, binding, morphology, pose, checkpoint


def project(values):
    command, binding, morphology, pose, checkpoint = values
    return project_motor_command(
        command, binding, morphology, body_pose=pose,
        embodiment_checkpoint=checkpoint, command_kind="normalized_activation",
    )


def test_binding_checkpoint_restores_identical_identity_and_projection():
    values = inputs()
    binding = values[1]
    restored = EmbodimentActuatorBinding.from_bytes(binding.to_bytes())
    assert restored == binding
    assert restored.binding_id == binding.binding_id
    assert restored.fingerprint == binding.fingerprint
    assert project((values[0], restored, *values[2:])) == project(values)


def test_restore_rejects_unknown_fields_or_tampered_content():
    binding = make_binding()
    unknown = binding.to_checkpoint() | {"future": "ignored?"}
    with pytest.raises(ValueError, match="checkpoint fields"):
        EmbodimentActuatorBinding.restore(unknown)
    tampered = binding.to_checkpoint()
    tampered["body_id"] = "other"
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        EmbodimentActuatorBinding.restore(tampered)


def test_maps_by_stable_effector_id_and_omission_means_no_command():
    base = inputs()
    command, binding, morphology, pose, checkpoint = base
    permuted = EmbodimentActuatorBinding(
        binding.binding_id, binding.body_id, binding.embodiment_episode_id,
        binding.morphology_revision, binding.source_surface_fingerprint,
        tuple(reversed(binding.channels)),
    )
    assert permuted.fingerprint == binding.fingerprint
    result = project((command, permuted, morphology, pose, checkpoint))
    assert tuple((item.effector_id, item.value) for item in result.channels) == (("elbow.flexor", 0.5),)
    channel = result.channels[0]
    assert (channel.body_id, channel.embodiment_episode_id, channel.morphology_revision) == (
        "body-1", "episode-1", "morphology-r1"
    )
    assert result.binding_id == "binding-1"
    assert result.binding_fingerprint == binding.fingerprint
    assert result.surface_fingerprint == binding.source_surface_fingerprint
    assert (channel.command_kind, channel.quantity, channel.unit) == (
        "normalized_activation", "normalized_command", "1"
    )
    assert (channel.minimum, channel.neutral, channel.maximum) == (0.2, 0.4, 1.0)


def test_omitted_command_is_not_replaced_by_zero_or_neutral():
    values = inputs(Command(channels=()))
    assert project(values).channels == ()


@pytest.mark.parametrize(
    "binding,morphology,message",
    [
        (make_binding(Morphology(body_id="other")), Morphology(), "different body identity"),
        (make_binding(Morphology(embodiment_episode_id="other")), Morphology(), "different embodiment episode"),
        (make_binding(Morphology(morphology_revision="old")), Morphology(), "different morphology revision"),
    ],
)
def test_rejects_binding_body_episode_or_morphology_mismatch(binding, morphology, message):
    with pytest.raises(ValueError, match=message):
        project(inputs(binding=binding, morphology=morphology))


def test_rejects_command_binding_or_episode_mismatch():
    binding = make_binding()
    with pytest.raises(ValueError, match="different actuator surface"):
        project(inputs(Command(surface_fingerprint="wrong"), binding))
    with pytest.raises(ValueError, match="different embodiment episode"):
        project(inputs(Command(embodiment_id="other", surface_fingerprint=binding.source_surface_fingerprint), binding))


def test_rejects_checkpoint_or_pose_that_does_not_match_active_morphology():
    command, binding, morphology, pose, checkpoint = inputs()
    checkpoint.body_id = "other"
    with pytest.raises(ValueError, match="checkpoint body identity"):
        project((command, binding, morphology, pose, checkpoint))
    wrong_pose = BodyPoseSample("other", "physics3d.world", "body.root", (0, 0, 0), (0, 0, 0, 1), "test", 1)
    with pytest.raises(ValueError, match="pose body identity"):
        project((command, binding, morphology, wrong_pose, inputs()[4]))


def test_rejects_missing_binding_coverage_and_out_of_range_values():
    morphology = Morphology()
    incomplete = make_binding(morphology, channels=make_binding().channels[:1])
    with pytest.raises(ValueError, match="cover every active"):
        project(inputs(binding=incomplete, morphology=morphology))
    binding = make_binding()
    out_of_range = Command(surface_fingerprint=binding.source_surface_fingerprint, channels=(("actuator-a", 0.1),))
    with pytest.raises(ValueError, match="outside the declared effector range"):
        project(inputs(out_of_range, binding))


def test_rejects_unavailable_unknown_or_duplicate_command_channel():
    morphology = Morphology()
    channels = list(make_binding().channels)
    channels[0] = ActuatorChannelBinding("actuator-a", "elbow.flexor", "normalized_activation", "normalized_command", "1", 0.2, 0.4, 1.0, "reject", available=False)
    unavailable = make_binding(morphology, channels=channels)
    with pytest.raises(ValueError, match="unavailable"):
        project(inputs(binding=unavailable))
    binding = make_binding()
    with pytest.raises(ValueError, match="outside the current binding"):
        project(inputs(Command(surface_fingerprint=binding.source_surface_fingerprint, channels=(("unknown", 0.3),)), binding))
    with pytest.raises(ValueError, match="channels must be unique"):
        project(inputs(Command(surface_fingerprint=binding.source_surface_fingerprint, channels=(("actuator-a", 0.3), ("actuator-a", 0.4))), binding))


def test_binding_rejects_duplicate_channel_identity_and_invalid_contract():
    channel = make_binding().channels[0]
    with pytest.raises(ValueError, match="actuator ids must be unique"):
        EmbodimentActuatorBinding(
            "b", "body-1", "episode-1", "morphology-r1", "source-surface", (channel, channel)
        )
    with pytest.raises(ValueError, match="minimum <= neutral"):
        ActuatorChannelBinding("a", "e", "kind", "quantity", "unit", 2, 1, 3, "reject")
