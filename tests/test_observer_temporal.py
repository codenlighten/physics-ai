import numpy as np

from physics_ai.observer import observe_temporal


def test_observe_temporal_energy_drift() -> None:
    frames = np.zeros((3, 4, 4))
    frames[0] = 1.0
    frames[1] = 0.5
    frames[2] = 0.25
    metrics = observe_temporal(frames)
    assert metrics["temporal_energy_start"] > metrics["temporal_energy_end"]
    assert metrics["temporal_energy_drift_ratio"] >= 0
    assert metrics["temporal_momentum_drift_ratio"] >= 0
    assert isinstance(metrics["temporal_fft"], list)
