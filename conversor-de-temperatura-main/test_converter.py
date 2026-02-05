import math
import pytest
from converter import (
    c_to_f, f_to_c, c_to_k, k_to_c, f_to_k, k_to_f,
    converter, TemperaturaInvalida
)

def approx(a, b, tol=1e-9):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)

def test_round_trips():
    assert approx(f_to_c(c_to_f(0)), 0)
    assert approx(k_to_c(c_to_k(25)), 25)

def test_known_values():
    assert approx(c_to_f(0), 32)
    assert approx(c_to_f(100), 212)
    assert approx(c_to_k(0), 273.15)
    assert approx(k_to_f(273.15), 32)

def test_router():
    assert approx(converter(0, "C", "F"), 32)
    assert approx(converter(32, "F", "C"), 0)
    assert approx(converter(0, "C", "C"), 0)

def test_absolute_zero_validation():
    with pytest.raises(TemperaturaInvalida):
        converter(-273.151, "C", "K")
    with pytest.raises(TemperaturaInvalida):
        converter(-459.671, "F", "C")
    with pytest.raises(TemperaturaInvalida):
        converter(-1e-12, "K", "C")
