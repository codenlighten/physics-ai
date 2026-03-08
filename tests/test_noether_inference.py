import numpy as np

from physics_ai.noether_inference import infer_noether, lagrangian_energy_drift
from physics_ai.observer import observe_temporal


def test_noether_energy_inference() -> None:
    frames = np.ones((5, 4, 4))
    temporal = observe_temporal(frames)
    observation = {"symmetry_group": "SO2", **temporal}
    results = infer_noether(observation, energy_threshold=0.01, momentum_threshold=0.5)
    assert any(result.conserved_quantity == "energy" for result in results)


def test_lagrangian_energy_drift() -> None:
    signal = [1.0, 0.8, 0.6, 0.4, 0.2]
    drift = lagrangian_energy_drift("0.5*qd**2 - 0.5*q**2", signal, dt=1.0)
    assert drift >= 0
