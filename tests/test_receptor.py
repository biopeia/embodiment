from dataclasses import dataclass, replace
import math

import pytest

from embodiment.observation import BodyPoseSample
from embodiment.physics3d.physical_transition import EmbodimentPhysicalState
from embodiment.physics3d.receptor import (
    EmbodimentReceptor,
    project_receptor_sample_point,
    receptors_by_id,
)


@dataclass(frozen=True)
class WorldStep:
    world_id: str = "world.1"
    source_causal_tick: int = 4
    physical_step_id: str = "step.5"
    body_id: str = "body.1"
    embodiment_episode_id: str = "episode.2"
    morphology_revision: str = "morph.3"


def _state(**changes: object) -> EmbodimentPhysicalState:
    values: dict[str, object] = {
        "world_id": "world.1",
        "causal_tick": 4,
        "body_id": "body.1",
        "embodiment_episode_id": "episode.2",
        "morphology_revision": "morph.3",
        "pose": BodyPoseSample(
            body_id="body.1",
            reference_frame="world.frame",
            body_frame="body.root",
            position_m=(2.0, 3.0, 4.0),
            orientation_xyzw=(0.0, 0.0, 0.0, 1.0),
            sample_kind="initial",
            sample_value=4,
        ),
        "linear_velocity_m_per_s": (0.0, 0.0, 0.0),
        "angular_velocity_rad_per_s": (0.0, 0.0, 0.0),
    }
    values.update(changes)
    return EmbodimentPhysicalState(**values)  # type: ignore[arg-type]


def _receptor(**changes: object) -> EmbodimentReceptor:
    values: dict[str, object] = {
        "receptor_id": "receptor.alpha",
        "body_id": "body.1",
        "embodiment_episode_id": "episode.2",
        "morphology_revision": "morph.3",
        "body_frame": "body.root",
        "position_in_body_frame_m": (1.0, 0.0, 0.0),
    }
    values.update(changes)
    return EmbodimentReceptor(**values)  # type: ignore[arg-type]


def test_receptor_identity_and_sample_point_are_stable_under_collection_permutation() -> None:
    first = _receptor()
    second = _receptor(receptor_id="receptor.beta", position_in_body_frame_m=(0.0, 1.0, 0.0))

    indexed_a = receptors_by_id((first, second))
    indexed_b = receptors_by_id((second, first))
    assert indexed_a.keys() == indexed_b.keys()
    assert indexed_a["receptor.alpha"] == indexed_b["receptor.alpha"]

    projected_a = project_receptor_sample_point(indexed_a["receptor.alpha"], _state(), WorldStep())
    projected_b = project_receptor_sample_point(indexed_b["receptor.alpha"], _state(), WorldStep())
    assert projected_a == projected_b
    assert projected_a.receptor_id == "receptor.alpha"
    assert projected_a.position_m == (3.0, 3.0, 4.0)
    assert projected_a.frame_id == "world.frame"
    assert (projected_a.world_id, projected_a.source_causal_tick, projected_a.physical_step_id) == (
        "world.1", 4, "step.5"
    )


def test_receptor_local_offset_is_rotated_into_reference_frame() -> None:
    half = math.sqrt(0.5)
    pose = BodyPoseSample(
        body_id="body.1",
        reference_frame="world.frame",
        body_frame="body.root",
        position_m=(2.0, 3.0, 4.0),
        orientation_xyzw=(0.0, 0.0, half, half),
        sample_kind="initial",
        sample_value=4,
    )
    projected = project_receptor_sample_point(_receptor(), _state(pose=pose), WorldStep())
    assert projected.position_m == pytest.approx((2.0, 4.0, 4.0))


@pytest.mark.parametrize(
    "changes",
    [
        {"body_id": "body.other"},
        {"embodiment_episode_id": "episode.other"},
        {"morphology_revision": "morph.old"},
    ],
)
def test_receptor_rejects_stale_or_mismatched_body_binding(changes: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="identity or morphology"):
        project_receptor_sample_point(_receptor(**changes), _state(), WorldStep())


def test_receptor_rejects_wrong_source_cut_or_attachment_frame() -> None:
    with pytest.raises(ValueError, match="source state"):
        project_receptor_sample_point(
            _receptor(), _state(causal_tick=5), WorldStep(source_causal_tick=4)
        )
    with pytest.raises(ValueError, match="attachment frame"):
        project_receptor_sample_point(
            _receptor(body_frame="body.other"), _state(), WorldStep()
        )


def test_receptor_descriptors_reject_duplicate_identity_and_nonfinite_location() -> None:
    with pytest.raises(ValueError, match="unique"):
        receptors_by_id((_receptor(), _receptor()))
    with pytest.raises(ValueError, match="finite metre"):
        _receptor(position_in_body_frame_m=(float("nan"), 0.0, 0.0))
