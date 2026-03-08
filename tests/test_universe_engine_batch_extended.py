from physics_ai.experiment_planner import propose_experiment
from physics_ai.universe_engine import run_universe_batch


def _base_config(dynamics_type: str) -> dict:
    config = propose_experiment(seed=1, universe_type="random", dynamics_type=dynamics_type)
    config.update({
        "size": 16,
        "steps": 5,
        "wave_speed": 1.0,
        "wavelength": 8.0,
    })
    return config


def test_batch_reaction_diffusion() -> None:
    base = _base_config("reaction_diffusion")
    results = run_universe_batch(base, [1, 2])
    assert len(results) == 2
    for item in results:
        assert "energy" in item["observation"]


def test_batch_multi_field() -> None:
    base = _base_config("multi_field")
    results = run_universe_batch(base, [1, 2], store_fields=True)
    assert len(results) == 2
    for item in results:
        observation = item["observation"]
        assert "psi_energy" in observation
        assert "phi_energy" in observation
        assert "cross_field_corr" in observation
