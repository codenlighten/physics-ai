import numpy as np

from physics_ai.universe_engine import run_universe


def test_run_universe_multifield_outputs() -> None:
    config = {
        "size": 16,
        "steps": 10,
        "wave_speed": 1.0,
        "wavelength": 8.0,
        "amplitude": 1.0,
        "pulse_position": 8,
        "boundary": "torus",
        "universe_type": "random",
        "dynamics_type": "multi_field",
        "store_field": True,
        "diffusion_psi": 0.1,
        "diffusion_phi": 0.08,
        "coupling_linear": 0.4,
        "coupling_quadratic": 0.2,
        "coupling_cross": 0.15,
        "psi_cubic": 0.1,
        "phi_cubic": 0.1,
        "psi_decay": 0.05,
        "phi_decay": 0.05,
        "dt": 0.05,
        "seed": 1,
    }
    result = run_universe(config)
    obs = result["observation"]
    assert "field_psi" in obs
    assert "field_phi" in obs
    assert "psi_temporal_signal" in obs or "temporal_signal_psi" in obs
    assert "phi_temporal_signal" in obs or "temporal_signal_phi" in obs
    assert "cross_field_corr" in obs
    assert np.asarray(obs["field_psi"]).shape == (16, 16)
