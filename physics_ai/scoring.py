"""Interestingness scoring utilities for simulated universes."""

from __future__ import annotations

from typing import Dict, Any, Iterable, List


def dispersion_complexity(dispersion: Dict[str, Any] | None) -> float:
    if not dispersion:
        return 0.0
    law_type = dispersion.get("law_type", "unknown")
    if law_type == "wave":
        return 1.0
    if law_type == "diffusion":
        return 0.7
    if law_type == "flat":
        return 0.2
    return 0.5


def _base_score(observation: Dict[str, Any]) -> float:
    particles = observation.get("particles") or {}
    particle_count = float(particles.get("particle_count", 0.0))
    resonance_strength = float(observation.get("resonance_strength", 0.0))
    curvature_strength = float(observation.get("curvature_strength", 0.0))
    dispersion = observation.get("dispersion") or observation.get("dispersion_law")
    dispersion_score = dispersion_complexity(dispersion)
    energy_variance = float(observation.get("variance", 0.0))
    temporal_drift = float(observation.get("temporal_energy_drift_ratio", 0.0))

    score = 0.0
    score += 3.0 * particle_count
    score += 1.5 * resonance_strength
    score += 1.0 * curvature_strength
    score += 2.0 * dispersion_score
    score += 0.5 * energy_variance
    score += 1.0 * temporal_drift
    return float(score)


def signature_from_observation(observation: Dict[str, Any]) -> Dict[str, float | str]:
    particles = observation.get("particles") or {}
    dispersion = observation.get("dispersion") or observation.get("dispersion_law")
    cross_corr = observation.get("cross_field_corr")
    return {
        "particle_count": float(particles.get("particle_count", 0.0)),
        "resonance_strength": float(observation.get("resonance_strength", 0.0)),
        "curvature_strength": float(observation.get("curvature_strength", 0.0)),
        "variance": float(observation.get("variance", 0.0)),
        "temporal_drift": float(observation.get("temporal_energy_drift_ratio", 0.0)),
        "dispersion_type": str((dispersion or {}).get("law_type", "unknown")),
        "cross_field_corr": float(cross_corr) if cross_corr is not None else 0.0,
    }


def diversity_penalty(
    signature: Dict[str, float | str],
    reference_signatures: Iterable[Dict[str, float | str]],
) -> float:
    refs: List[Dict[str, float | str]] = list(reference_signatures)
    if not refs:
        return 0.0
    penalties = []
    for ref in refs:
        diff = 0.0
        diff += abs(float(signature.get("particle_count", 0.0)) - float(ref.get("particle_count", 0.0)))
        diff += abs(float(signature.get("resonance_strength", 0.0)) - float(ref.get("resonance_strength", 0.0)))
        diff += abs(float(signature.get("curvature_strength", 0.0)) - float(ref.get("curvature_strength", 0.0)))
        diff += abs(float(signature.get("variance", 0.0)) - float(ref.get("variance", 0.0)))
        diff += abs(float(signature.get("temporal_drift", 0.0)) - float(ref.get("temporal_drift", 0.0)))
        diff += abs(float(signature.get("cross_field_corr", 0.0)) - float(ref.get("cross_field_corr", 0.0)))
        if signature.get("dispersion_type") == ref.get("dispersion_type"):
            diff += 0.5
        penalties.append(1.0 / (1.0 + diff))
    return float(sum(penalties) / len(penalties))


def novelty_bonus(
    signature: Dict[str, float | str],
    reference_signatures: Iterable[Dict[str, float | str]],
) -> float:
    refs: List[Dict[str, float | str]] = list(reference_signatures)
    if not refs:
        return 0.0
    distances = []
    for ref in refs:
        diff = 0.0
        diff += abs(float(signature.get("particle_count", 0.0)) - float(ref.get("particle_count", 0.0)))
        diff += abs(float(signature.get("resonance_strength", 0.0)) - float(ref.get("resonance_strength", 0.0)))
        diff += abs(float(signature.get("curvature_strength", 0.0)) - float(ref.get("curvature_strength", 0.0)))
        diff += abs(float(signature.get("variance", 0.0)) - float(ref.get("variance", 0.0)))
        diff += abs(float(signature.get("temporal_drift", 0.0)) - float(ref.get("temporal_drift", 0.0)))
        diff += abs(float(signature.get("cross_field_corr", 0.0)) - float(ref.get("cross_field_corr", 0.0)))
        if signature.get("dispersion_type") != ref.get("dispersion_type"):
            diff += 0.5
        distances.append(diff)
    return float(sum(distances) / len(distances))


def universe_score(
    observation: Dict[str, Any],
    reference_signatures: Iterable[Dict[str, float | str]] | None = None,
) -> float:
    raw = _base_score(observation)
    if not reference_signatures:
        return raw
    signature = signature_from_observation(observation)
    penalty = diversity_penalty(signature, reference_signatures)
    bonus = novelty_bonus(signature, reference_signatures)
    return float(raw - penalty + 0.25 * bonus)
