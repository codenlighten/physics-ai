from physics_ai.evolutionary_search import EvolutionConfig, run_evolution


def test_run_evolution_generates_results(tmp_path) -> None:
    config = EvolutionConfig(
        generations=2,
        population_size=4,
        elite_count=2,
        seed=123,
        dynamics_type="wave",
        checkpoint_dir=str(tmp_path),
    )
    results = run_evolution(config)
    assert len(results) == 8


def test_run_evolution_cmaes_strategy(tmp_path) -> None:
    config = EvolutionConfig(
        generations=1,
        population_size=3,
        elite_count=1,
        seed=321,
        dynamics_type="wave",
        mutation_strategy="cmaes",
        sigma=0.4,
        checkpoint_dir=str(tmp_path),
    )
    results = run_evolution(config)
    assert len(results) == 3


def test_run_evolution_phase_target(tmp_path) -> None:
    config = EvolutionConfig(
        generations=1,
        population_size=2,
        elite_count=1,
        seed=777,
        dynamics_type="wave",
        target_phase="LINEAR_WAVE",
        phase_bonus=1.0,
        checkpoint_dir=str(tmp_path),
    )
    results = run_evolution(config)
    assert len(results) == 2
    assert "phase_bonus" in results[0]["observation"]


def test_run_evolution_atlas_guided(tmp_path) -> None:
    config = EvolutionConfig(
        generations=1,
        population_size=3,
        elite_count=1,
        seed=555,
        dynamics_type="wave",
        atlas_guided=True,
        atlas_method="tsne",
        atlas_seed_count=2,
        checkpoint_dir=str(tmp_path),
    )
    results = run_evolution(config)
    assert len(results) == 3
