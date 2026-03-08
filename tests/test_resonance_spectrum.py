import numpy as np

from physics_ai.resonant_spectrum import geometry_spectrum, resonance_strength, spectrum_summary


def test_resonance_spectrum_outputs() -> None:
    field = np.random.default_rng(0).random((8, 8))
    power = geometry_spectrum(field)
    assert power.shape == (8, 8)
    assert resonance_strength(power) >= 0
    result = spectrum_summary(field, k=3)
    assert "dominant_modes" in result
