import numpy as np

from physics_ai.seed_perturbations import apply_seed_perturbations


def test_apply_seed_perturbations_changes_field() -> None:
    rng = np.random.default_rng(0)
    field = np.zeros((16, 16))
    updated = apply_seed_perturbations(
        field.copy(),
        rng,
        seed_count=2,
        seed_types=["gaussian"],
        amplitude_range=(1.0, 1.0),
        radius_range=(2.0, 2.0),
    )
    assert np.any(updated != 0.0)
