import numpy as np

from physics_ai.spectral_lagrangian import (
    SpectralConfig,
    generate_modes,
    reconstruct_field,
    simulate_field_from_modes,
    simulate_modes,
)


def test_generate_modes_shape() -> None:
    modes = generate_modes(size=16, modes=3, seed=1)
    assert len(modes) == 3
    assert modes[0].shape == (16, 16)


def test_simulate_modes_history() -> None:
    history, omegas, velocities = simulate_modes(SpectralConfig(modes=4, steps=5, seed=2))
    assert history.shape == (5, 4)
    assert omegas.shape == (4,)
    assert velocities.shape == (4,)


def test_simulate_field_from_modes() -> None:
    frames, omegas, velocities = simulate_field_from_modes(12, SpectralConfig(modes=2, steps=3, seed=3))
    assert frames.shape == (3, 12, 12)
    assert np.all(np.isfinite(frames))
