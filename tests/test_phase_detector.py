from physics_ai.phase_detector import detect_phase


def test_detect_phase_particle_system() -> None:
    observation = {
        "particles": {"particle_count": 3},
        "spectral_entropy": 0.4,
        "energy_localization": 0.5,
        "temporal_energy_drift_ratio": 0.1,
        "resonance_strength": 0.2,
        "defect_density": 0.05,
    }
    phase = detect_phase(observation)
    assert phase["phase"] == "PARTICLE_SYSTEM"


def test_detect_phase_turbulent() -> None:
    observation = {
        "particles": {"particle_count": 0},
        "spectral_entropy": 0.9,
        "energy_localization": 0.1,
        "temporal_energy_drift_ratio": 0.6,
        "resonance_strength": 0.1,
    }
    phase = detect_phase(observation)
    assert phase["phase"] == "TURBULENT_FIELD"


def test_detect_phase_soliton_regime() -> None:
    observation = {
        "particles": {"particle_count": 3},
        "spectral_entropy": 0.2,
        "energy_localization": 0.7,
        "temporal_energy_drift_ratio": 0.1,
        "resonance_strength": 0.4,
        "defect_density": 0.02,
        "vortex_count": 2,
        "particle_score": 1.4,
    }
    phase = detect_phase(observation)
    assert phase["phase"] == "SOLITON_REGIME"


def test_detect_phase_vortex_particle_regime() -> None:
    observation = {
        "particles": {"particle_count": 1},
        "spectral_entropy": 0.4,
        "energy_localization": 0.3,
        "temporal_energy_drift_ratio": 0.2,
        "resonance_strength": 0.2,
        "defect_density": 0.05,
        "vortex_count": 3,
        "particle_score": 0.8,
    }
    phase = detect_phase(observation)
    assert phase["phase"] == "VORTEX_PARTICLE_REGIME"
