import numpy as np

from physics_ai.field_dynamics import (
    DiffusionConfig,
    ReactionDiffusionConfig,
    WaveConfig,
    OscillatorConfig,
    SchrodingerConfig,
    laplacian,
    simulate_diffusion,
    simulate_oscillator,
    simulate_reaction_diffusion,
    simulate_schrodinger,
    simulate_wave,
)


def test_laplacian_shape() -> None:
    field = np.random.default_rng(0).random((10, 10))
    lap = laplacian(field)
    assert lap.shape == field.shape


def test_simulate_wave_frames() -> None:
    field = np.random.default_rng(1).random((8, 8))
    frames = simulate_wave(field, WaveConfig(steps=5, wave_speed=1.0, dt=0.1))
    assert frames.shape == (5, 8, 8)


def test_simulate_wave_with_nonlinear_terms() -> None:
    field = np.random.default_rng(6).random((6, 6))
    frames = simulate_wave(
        field,
        WaveConfig(steps=3, wave_speed=1.0, dt=0.1, nonlinear_coeff=0.2, biharmonic_coeff=0.1),
    )
    assert frames.shape == (3, 6, 6)


def test_simulate_wave_batch_frames() -> None:
    field = np.random.default_rng(5).random((3, 6, 6))
    frames = simulate_wave(field, WaveConfig(steps=4, wave_speed=1.0, dt=0.1))
    assert frames.shape == (4, 3, 6, 6)


def test_simulate_diffusion_frames() -> None:
    field = np.random.default_rng(2).random((6, 6))
    frames = simulate_diffusion(field, DiffusionConfig(steps=4, diffusion=0.2))
    assert frames.shape == (4, 6, 6)


def test_simulate_reaction_diffusion() -> None:
    rng = np.random.default_rng(3)
    field_a = rng.random((6, 6))
    field_b = rng.random((6, 6))
    out_a, out_b = simulate_reaction_diffusion(
        field_a,
        field_b,
        ReactionDiffusionConfig(steps=3),
    )
    assert out_a.shape == field_a.shape
    assert out_b.shape == field_b.shape


def test_simulate_oscillator() -> None:
    series = simulate_oscillator(OscillatorConfig(steps=10, k=1.0, dt=0.1, q0=1.0))
    assert series.shape == (10,)


def test_simulate_schrodinger() -> None:
    field = np.random.default_rng(4).random((6, 6))
    frames = simulate_schrodinger(field, SchrodingerConfig(steps=3, dt=0.1))
    assert frames.shape == (3, 6, 6)
    assert np.iscomplexobj(frames)
