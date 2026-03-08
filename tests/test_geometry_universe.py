import numpy as np

from physics_ai.geometry_universe import GeometryConfig, metric_field, simulate_geometry


def test_metric_field_identity() -> None:
    metric = metric_field(4)
    assert metric.shape == (4, 4, 2, 2)
    assert np.allclose(metric[:, :, 0, 0], 1.0)
    assert np.allclose(metric[:, :, 1, 1], 1.0)


def test_simulate_geometry_outputs() -> None:
    result = simulate_geometry(GeometryConfig(size=8, steps=5, seed=1))
    assert result["rho"].shape == (8, 8)
    assert result["trajectory"].shape[0] == 5
    assert result["curvature_strength"] >= 0
