"""Phase classification utilities for universe observations."""

from __future__ import annotations

from typing import Dict, Any


def detect_phase(observation: Dict[str, Any]) -> Dict[str, Any]:
    particle_count = float((observation.get("particles") or {}).get("particle_count", 0.0))
    spectral_entropy = float(observation.get("spectral_entropy", 0.0))
    energy_localization = float(observation.get("energy_localization", 0.0))
    temporal_drift = float(observation.get("temporal_energy_drift_ratio", 0.0))
    resonance_strength = float(observation.get("resonance_strength", 0.0))
    defect_density = float(observation.get("defect_density", 0.0))
    vortex_count = float(observation.get("vortex_count", 0.0))
    particle_score = float(observation.get("particle_score", 0.0))

    phase = "LINEAR_WAVE"
    confidence = 0.4

    if particle_score > 1.2 and particle_count >= 2:
        phase = "SOLITON_REGIME"
        confidence = min(0.92, 0.6 + 0.05 * particle_score)
    elif particle_score > 0.6 and particle_count >= 1 and temporal_drift < 0.3:
        phase = "VORTEX_PARTICLE_REGIME" if vortex_count > 0 else "PARTICLE_SYSTEM"
        confidence = min(0.9, 0.55 + 0.1 * particle_score)
    elif particle_count >= 2 and temporal_drift < 0.3 and (defect_density > 0.01 or vortex_count > 0):
        phase = "PARTICLE_SYSTEM"
        confidence = min(0.9, 0.5 + 0.1 * particle_count)
    elif spectral_entropy > 0.75 and temporal_drift > 0.4:
        phase = "TURBULENT_FIELD"
        confidence = min(0.9, 0.5 + spectral_entropy)
    elif energy_localization > 0.6 and resonance_strength > 0.1:
        phase = "SOLITON_FIELD"
        confidence = min(0.85, 0.5 + energy_localization)
    elif resonance_strength > 0.3 and spectral_entropy < 0.5:
        phase = "RESONANT_STANDING_WAVE"
        confidence = min(0.8, 0.5 + resonance_strength)

    return {"phase": phase, "phase_confidence": float(confidence)}
