from physics_ai.distributed import DistributedConfig, run_distributed


def test_run_distributed_executes_small_batch(tmp_path) -> None:
    config = DistributedConfig(
        universe_count=2,
        batch_size=1,
        seed=42,
        dynamics_type="wave",
        checkpoint_dir=str(tmp_path),
    )
    results = run_distributed(config)
    assert len(results) == 2
    run_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert run_dirs
    run_dir = run_dirs[0]
    assert any(path.name.startswith("universes_batch") for path in run_dir.iterdir())
