import numpy as np

from physics_ai.field_dynamics import DiffusionConfig, WaveConfig, simulate_diffusion, simulate_wave


def test_wave_simulation_batch_shape() -> None:
    batch = np.zeros((3, 8, 8))
    frames = simulate_wave(batch, WaveConfig(steps=4))
    assert frames.shape == (4, 3, 8, 8)


def test_diffusion_batch_parity() -> None:
    single = np.random.default_rng(0).random((8, 8))
    batch = np.stack([single, single], axis=0)
    frames_single = simulate_diffusion(single, DiffusionConfig(steps=2))
    frames_batch = simulate_diffusion(batch, DiffusionConfig(steps=2))
    assert frames_batch.shape == (2, 2, 8, 8)
    np.testing.assert_allclose(frames_batch[:, 0], frames_single, atol=1e-6)
    np.testing.assert_allclose(frames_batch[:, 1], frames_single, atol=1e-6)
