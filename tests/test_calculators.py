"""Pure-function tests for the aerospace performance calculators (no deps/network)."""
import pytest

from app.tools.aviation import calculators as c


def test_pressure_altitude_standard():
    assert c.pressure_altitude(1000, 29.92) == 1000


def test_pressure_altitude_high_setting():
    assert c.pressure_altitude(0, 30.42) == -500


def test_density_altitude_at_isa():
    assert c.density_altitude(0, 15) == 0


def test_density_altitude_hot_and_high():
    assert abs(c.density_altitude(5000, 25) - 7364) < 5


def test_wind_components_direct_crosswind():
    r = c.wind_components(90, 10, 360)
    assert abs(r["headwind_kt"]) < 0.01
    assert abs(r["crosswind_kt"] - 10) < 0.01
    assert r["from_left"] is False  # wind from 090 onto runway 360 is from the right


def test_wind_components_direct_headwind():
    r = c.wind_components(360, 10, 360)
    assert abs(r["headwind_kt"] - 10) < 0.01
    assert r["crosswind_kt"] == 0


def test_weight_and_balance():
    r = c.weight_and_balance([200, 200], [36, 48])
    assert r["total_weight_lb"] == 400
    assert r["cg_in"] == 42


def test_weight_and_balance_mismatched_lengths():
    with pytest.raises(ValueError):
        c.weight_and_balance([100], [10, 20])


def test_ground_roll_density_altitude_correction():
    assert c.adjust_ground_roll(1000, 3000) == 1331
