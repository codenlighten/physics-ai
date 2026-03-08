from physics_ai.main_loop import run_experiment


def test_run_experiment_discovers_inverse_relation() -> None:
    results = run_experiment(universe_count=12, seed=42, generations=5)
    law = results["inverse_law"]
    assert law["k"] > 0
    assert law["error"] < 5.0
    assert results["best_hypothesis"].score < 5.0
