from physics_ai.canonical_runner import run_canonical_suite


def test_run_canonical_suite_outputs() -> None:
    results = run_canonical_suite(seed=1, universe_count=4)
    assert len(results) == 4
    assert {result.dynamics_type for result in results} == {
        "oscillator",
        "diffusion",
        "wave",
        "schrodinger",
    }
    for result in results:
        assert result.equation is not None
