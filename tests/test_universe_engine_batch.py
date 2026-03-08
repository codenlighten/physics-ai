from physics_ai.universe_engine import explore_universes


def test_explore_universes_batch_wave() -> None:
    dataset = explore_universes(
        2,
        seed=123,
        universe_type="random",
        dynamics_type="wave",
        batch_size=2,
    )
    assert len(dataset) == 2
    for item in dataset:
        assert "energy" in item["observation"]
