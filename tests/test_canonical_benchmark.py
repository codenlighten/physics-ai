from physics_ai.canonical_benchmark import run_benchmark


def test_run_benchmark_outputs() -> None:
    results = run_benchmark(seed=1, universe_count=4)
    assert results
    for result in results:
        assert result.dynamics_type
        assert isinstance(result.passed, bool)
