from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.actuation_projection import project_motor_command


@dataclass(frozen=True)
class Channel:
    actuator_id: str
    available: bool = True
    command_min: float = 0.0
    command_max: float = 1.0


@dataclass(frozen=True)
class Surface:
    contract_fingerprint: str
    channels: tuple[Channel, ...]

    @property
    def actuator_ids(self):
        return tuple(channel.actuator_id for channel in self.channels)


@dataclass(frozen=True)
class Command:
    command_id: str = "command-1"
    commitment_id: str = "commitment-1"
    controller_id: str = "controller-1"
    competence_id: str | None = None
    surface_fingerprint: str = "surface-fp"
    channels: tuple[tuple[str, float], ...] = (("opaque-a", 0.4),)
    issued_at_tick: int = 7
    embodiment_id: str | None = "episode-1"


def inputs(command=Command(), surface=None, *, body_id="body-1", episode_id="episode-1"):
    surface = surface or Surface(
        "surface-fp", (Channel("opaque-a"), Channel("opaque-b", command_min=0.2))
    )
    pose = BodyPoseSample(
        body_id, "physics3d.world", "body.root", (0, 0, 0), (0, 0, 0, 1), "test", 1
    )
    checkpoint = SimpleNamespace(body_id=body_id, episode_id=episode_id)
    spec = SimpleNamespace(effector_ids=lambda: ("eff.0", "eff.1"))
    return command, surface, spec, pose, checkpoint


def project(values):
    command, surface, spec, pose, checkpoint = values
    return project_motor_command(
        command, surface, spec, body_pose=pose, embodiment_checkpoint=checkpoint,
        expected_embodiment_id="episode-1",
    )


def test_maps_in_surface_order_and_marks_omitted_port_zero():
    result = project(inputs())
    assert result.channels == (("eff.0", 0.4), ("eff.1", 0.0))
    assert result.zeroed_missing_effector_ids == ("eff.1",)
    assert result.body_id == "body-1"
    assert result.embodiment_id == "episode-1"
    assert result.issued_at_tick == 7


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda v: v[0].__class__(surface_fingerprint="wrong"), "different actuator surface"),
        (lambda v: Command(embodiment_id="other"), "different embodiment identity"),
        (lambda v: Command(channels=(("unknown", 0.2),)), "outside the current surface"),
    ],
)
def test_rejects_invalid_command_provenance_or_channels(change, message):
    values = list(inputs())
    if change.__code__.co_firstlineno:
        values[0] = change(values)
    with pytest.raises(ValueError, match=message):
        project(tuple(values))


def test_rejects_body_identity_mismatch():
    values = inputs(body_id="body-1", episode_id="episode-1")
    command, surface, spec, pose, checkpoint = values
    checkpoint.body_id = "body-2"
    with pytest.raises(ValueError, match="pose body identity"):
        project((command, surface, spec, pose, checkpoint))


def test_rejects_surface_cardinality_mismatch():
    values = inputs(surface=Surface("surface-fp", (Channel("opaque-a"),)))
    with pytest.raises(ValueError, match="exactly match"):
        project(values)


def test_rejects_unavailable_command_channel():
    values = inputs(surface=Surface("surface-fp", (Channel("opaque-a", available=False), Channel("opaque-b"))))
    with pytest.raises(ValueError, match="unavailable"):
        project(values)


def test_rejects_activation_outside_surface_command_range():
    values = inputs(
        command=Command(channels=(("opaque-a", 0.8),)),
        surface=Surface("surface-fp", (Channel("opaque-a", command_max=0.5), Channel("opaque-b"))),
    )
    with pytest.raises(ValueError, match="outside the actuator command range"):
        project(values)
