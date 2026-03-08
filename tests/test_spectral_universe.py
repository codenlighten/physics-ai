import numpy as np

from physics_ai.spectral_universe import (
    HarmonicConfig,
    PhiConfig,
    SpectralConfig,
    generate_harmonic_field,
    generate_phi_field,
    generate_spectral_field,
    generate_universe_field,
)


def test_generate_spectral_field_shape() -> None:
    field = generate_spectral_field(SpectralConfig(size=32, modes=3, seed=1))
    assert field.shape == (32, 32)
    assert np.any(field != 0)


def test_generate_harmonic_field_shape() -> None:
    field = generate_harmonic_field(HarmonicConfig(size=24, base=2.0, harmonics=4))
    assert field.shape == (24, 24)
    assert np.any(field != 0)


def test_generate_phi_field_shape() -> None:
    field = generate_phi_field(PhiConfig(size=20))
    assert field.shape == (20, 20)
    assert np.any(field != 0)


def test_generate_universe_field_random() -> None:
    field = generate_universe_field("random", size=16, seed=2)
    assert field.shape == (16, 16)
    assert np.all(field >= 0)
