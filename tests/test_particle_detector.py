import numpy as np

from physics_ai.particle_detector import energy_density, detect_peaks, particle_summary


def test_energy_density_shape() -> None:
    field = np.random.default_rng(0).random((6, 6))
    energy = energy_density(field)
    assert energy.shape == field.shape


def test_detect_peaks() -> None:
    field = np.zeros((5, 5))
    field[2, 2] = 10.0
    peaks = detect_peaks(field, threshold=0.5)
    assert peaks.shape[1] == 2


def test_particle_summary_outputs() -> None:
    frames = np.zeros((3, 5, 5))
    frames[:, 2, 2] = 1.0
    summary = particle_summary(frames, threshold=0.5)
    assert summary["particle_count"] >= 1
