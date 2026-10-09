from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from embodiment.observation import BodyPoseSample
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
class Channel:
    actuator_id: str
    effector_id: str
    command_kind: str = "normalized_activation"
    quantity: str = "normalized_command"
    unit: str = "1"
    minimum: float = 0.0
    neutral: float = 0.0
    maximum: float = 1.0
    saturation: str = "reject"
    available: bool = True


@dataclass(frozen=True)
class Surface:
    contract_fingerprint: str
    morphology_revision: str
    channels: tuple[Channel, ...]


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
    surface_fingerprint: str = "surface-fp"
    channels: tuple[tuple[str, float], ...] = (("actuator-a", 0.5),)
    issued_at_tick: int = 7
    embodiment_id: str | None = "episode-1"


def inputs(command=Command(), surface=None, morphology=Morphology()):
    if surface is None:
        surface = Surface(
            "surface-fp",
            "morphology-r1",
            (
                Channel("actuator-a", "elbow.flexor", minimum=0.2, neutral=0.4),
                Channel("actuator-b", "wrist.rotator"),
            ),
        )
    pose = BodyPoseSample(
        morphology.body_id, "physics3d.world", "body.root", (0, 0, 0), (0, 0, 0, 1), "test", 1
    )
    checkpoint = SimpleNamespace(
        body_id=morphology.body_id, episode_id=morphology.embodiment_episode_id
    )
    return command, surface, morphology, pose, checkpoint


def project(values):
    command, surface, morphology, pose, checkpoint = values
    return project_motor_command(
        command,
        surface,
        morphology,
        body_pose=pose,
        embodiment_checkpoint=checkpoint,
        command_kind="normalized_activation",
    )


def test_maps_by_stable_effector_id_and_omission_means_no_command():
    # Deliberately reverse the surface order: identifiers, not ordinal position,
    # associate the command with its morphology effector.
    base = inputs()
    command, surface, morphology, pose, checkpoint = base
    reversed_surface = Surface(
        surface.contract_fingerprint,
        surface.morphology_revision,
        tuple(reversed(surface.channels)),
    )
    result = project((command, reversed_surface, morphology, pose, checkpoint))
    assert tuple(
        (item.effector_id, item.value) for item in result.channels
    ) == (("elbow.flexor", 0.5),)
    channel = result.channels[0]
    assert channel.body_id == "body-1"
    assert channel.embodiment_episode_id == "episode-1"
    assert channel.morphology_revision == "morphology-r1"
    assert channel.command_kind == "normalized_activation"
    assert channel.quantity == "normalized_command"
    assert channel.unit == "1"
    assert (channel.minimum, channel.neutral, channel.maximum) == (0.2, 0.4, 1.0)
    assert result.body_id == "body-1"
    assert result.embodiment_episode_id == "episode-1"
    assert result.morphology_revision == "morphology-r1"
    assert result.command_kind == "normalized_activation"
    assert result.issued_at_tick == 7


@pytest.mark.parametrize(
    "command, surface, morphology, message",
    [
        (Command(surface_fingerprint="wrong"), None, None, "different actuator surface"),
        (Command(embodiment_id="other"), None, None, "different embodiment episode"),
        (Command(channels=(("unknown", 0.3),)), None, None, "outside the current surface"),
    ],
)
def test_rejects_provenance_revision_or_unknown_channel(command, surface, morphology, message):
    values = inputs(command, surface, Morphology() if morphology is None else morphology)
    with pytest.raises(ValueError, match=message):
        project(values)


def test_rejects_checkpoint_or_pose_that_does_not_match_active_morphology():
    command, surface, morphology, pose, checkpoint = inputs()
    checkpoint.body_id = "other"
    with pytest.raises(ValueError, match="checkpoint body identity"):
        project((command, surface, morphology, pose, checkpoint))


def test_rejects_checkpoint_episode_mismatch():
    command, surface, morphology, pose, checkpoint = inputs()
    checkpoint.episode_id = "other"
    with pytest.raises(ValueError, match="checkpoint episode identity"):
        project((command, surface, morphology, pose, checkpoint))


def test_rejects_surface_revision_or_effector_contract_mismatch():
    command, surface, morphology, pose, checkpoint = inputs()
    stale = Surface(surface.contract_fingerprint, "morphology-old", surface.channels)
    with pytest.raises(ValueError, match="different morphology revision"):
        project((command, stale, morphology, pose, checkpoint))

    changed = Surface(
        surface.contract_fingerprint,
        surface.morphology_revision,
        (Channel("actuator-a", "elbow.flexor", maximum=0.8), surface.channels[1]),
    )
    with pytest.raises(ValueError, match="contract differs"):
        project((command, changed, morphology, pose, checkpoint))


def test_rejects_duplicate_surface_effector_and_missing_surface_coverage():
    command, surface, morphology, pose, checkpoint = inputs()
    duplicate = Surface(
        surface.contract_fingerprint,
        surface.morphology_revision,
        (surface.channels[0], Channel("actuator-c", "elbow.flexor")),
    )
    with pytest.raises(ValueError, match="effector ids must be unique"):
        project((command, duplicate, morphology, pose, checkpoint))

    missing = Surface(surface.contract_fingerprint, surface.morphology_revision, surface.channels[:1])
    with pytest.raises(ValueError, match="cover every active"):
        project((command, missing, morphology, pose, checkpoint))


def test_omitted_command_is_not_replaced_by_zero_or_neutral():
    values = inputs(Command(channels=()))
    result = project(values)
    assert result.channels == ()


def test_rejects_unavailable_channel_command_and_out_of_range_value_without_saturation():
    command, surface, morphology, pose, checkpoint = inputs()
    unavailable = Surface(
        surface.contract_fingerprint,
        surface.morphology_revision,
        (Channel("actuator-a", "elbow.flexor", minimum=0.2, neutral=0.4, available=False),
         surface.channels[1]),
    )
    with pytest.raises(ValueError, match="unavailable"):
        project((command, unavailable, morphology, pose, checkpoint))

    out_of_range = Command(channels=(("actuator-a", 0.1),))
    with pytest.raises(ValueError, match="outside the declared effector range"):
        project((out_of_range, surface, morphology, pose, checkpoint))


def test_rejects_wrong_command_kind_and_non_finite_values():
    command, surface, morphology, pose, checkpoint = inputs()
    wrong_kind = Surface(
        surface.contract_fingerprint,
        surface.morphology_revision,
        (Channel("actuator-a", "elbow.flexor", command_kind="force"), surface.channels[1]),
    )
    with pytest.raises(ValueError, match="command_kind"):
        project((command, wrong_kind, morphology, pose, checkpoint))

    with pytest.raises(ValueError, match="must be finite"):
        project((Command(channels=(("actuator-a", float("nan")),)), surface, morphology, pose, checkpoint))


def test_rejects_duplicate_command_channels():
    with pytest.raises(ValueError, match="channels must be unique"):
        project(inputs(Command(channels=(("actuator-a", 0.3), ("actuator-a", 0.5)))))
