import numpy as np

from physics_ai.observer import observe_multifield


def test_observe_multifield_outputs_prefixed_metrics() -> None:
    psi = np.array([[1.0, 0.0], [0.0, -1.0]])
    phi = np.array([[0.5, -0.5], [0.5, -0.5]])
    metrics = observe_multifield({"psi": psi, "phi": phi})

    assert "psi_energy" in metrics
    assert "phi_energy" in metrics
    assert "cross_field_corr" in metrics
    assert metrics["variance"] >= 0.0
