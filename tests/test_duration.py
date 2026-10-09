from __future__ import annotations

import math

import pytest

from embodiment.duration import PhysicalDuration


@pytest.mark.parametrize("value", [0, 0.0, 0.016, 12])
def test_physical_duration_accepts_plain_non_negative_numeric_seconds(value):
    duration = PhysicalDuration(value)

    assert isinstance(duration, float)
    assert float(duration) == float(value)


def test_physical_duration_accepts_its_own_type():
    duration = PhysicalDuration(0.5)

    assert PhysicalDuration(duration) == duration


@pytest.mark.parametrize("value", [-0.1, -1, float("nan"), float("inf"), -float("inf")])
def test_physical_duration_rejects_negative_or_non_finite_values(value):
    with pytest.raises(ValueError):
        PhysicalDuration(value)


@pytest.mark.parametrize("value", [True, False, "1.0", None, object()])
def test_physical_duration_rejects_non_plain_numeric_values(value):
    with pytest.raises(TypeError, match="plain numeric duration"):
        PhysicalDuration(value)  # type: ignore[arg-type]


class FloatSubclass(float):
    pass


class IntSubclass(int):
    pass


@pytest.mark.parametrize("value", [FloatSubclass(1.0), IntSubclass(1)])
def test_physical_duration_rejects_other_numeric_subclasses(value):
    with pytest.raises(TypeError, match="plain numeric duration"):
        PhysicalDuration(value)


def test_physical_duration_repr_is_explicit():
    assert repr(PhysicalDuration(0.016)) == "PhysicalDuration(0.016)"
