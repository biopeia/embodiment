"""Bounded tests for the extracted body-pose value contract."""

from __future__ import annotations

import pytest

from embodiment.observation import BodyPoseSample


def _sample(**overrides: object) -> BodyPoseSample:
    values: dict[str, object] = {
        "body_id": "body.1",
        "reference_frame": "physics3d.world",
        "body_frame": "body.root",
        "position_m": (0.0, 0.0, 0.0),
        "orientation_xyzw": (0.0, 0.0, 0.0, 1.0),
        "sample_kind": "physics_step",
        "sample_value": 1,
    }
    values.update(overrides)
    return BodyPoseSample(**values)  # type: ignore[arg-type]


def test_body_pose_value_retains_frame_label_without_world_identity() -> None:
    sample = _sample()

    assert sample.reference_frame == "physics3d.world"
    assert sample.body_frame == "body.root"
    assert not hasattr(sample, "world_id")


def test_body_pose_sample_rejects_non_unit_quaternion() -> None:
    with pytest.raises(ValueError, match="unit quaternion"):
        _sample(orientation_xyzw=(0.0, 0.0, 0.0, 2.0))


def test_body_pose_sample_rejects_non_finite_sample_time() -> None:
    with pytest.raises(ValueError, match="sample_time_s"):
        _sample(sample_time_s=float("nan"))


def test_body_pose_sample_normalizes_numeric_coordinates() -> None:
    sample = _sample(position_m=(1, 2, 3))

    assert sample.position_m == (1.0, 2.0, 3.0)
