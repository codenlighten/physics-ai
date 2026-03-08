from physics_ai.scoring import (
    dispersion_complexity,
    novelty_bonus,
    signature_from_observation,
    universe_score,
)


def test_dispersion_complexity_defaults() -> None:
    assert dispersion_complexity(None) == 0.0
    assert dispersion_complexity({"law_type": "wave"}) == 1.0


def test_universe_score_includes_particles() -> None:
    observation = {
        "particles": {"particle_count": 2},
        "resonance_strength": 0.5,
        "curvature_strength": 0.2,
        "dispersion": {"law_type": "wave"},
        "variance": 0.1,
        "temporal_energy_drift_ratio": 0.05,
    }
    score = universe_score(observation)
    assert score > 0.0


def test_universe_score_diversity_penalty() -> None:
    observation = {
        "particles": {"particle_count": 1},
        "resonance_strength": 0.2,
        "curvature_strength": 0.1,
        "dispersion": {"law_type": "wave"},
        "variance": 0.05,
        "temporal_energy_drift_ratio": 0.01,
    }
    signature = signature_from_observation(observation)
    base = universe_score(observation)
    adjusted = universe_score(observation, [signature])
    assert adjusted < base


def test_novelty_bonus_increases_with_distance() -> None:
    obs_a = {
        "particles": {"particle_count": 0},
        "resonance_strength": 0.1,
        "curvature_strength": 0.1,
        "dispersion": {"law_type": "wave"},
        "variance": 0.01,
        "temporal_energy_drift_ratio": 0.01,
    }
    obs_b = {
        "particles": {"particle_count": 4},
        "resonance_strength": 0.9,
        "curvature_strength": 0.6,
        "dispersion": {"law_type": "diffusion"},
        "variance": 0.5,
        "temporal_energy_drift_ratio": 0.3,
    }
    sig_a = signature_from_observation(obs_a)
    sig_b = signature_from_observation(obs_b)
    bonus = novelty_bonus(sig_b, [sig_a])
    assert bonus > 0.5
