"""Generate and evaluate simple physics hypotheses."""

from __future__ import annotations

from typing import Dict, List, Any

import numpy as np


def fit_inverse_relationship(wavelengths: List[float], frequencies: List[float]) -> Dict[str, float]:
    x = 1.0 / np.array(wavelengths, dtype=float)
    y = np.array(frequencies, dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "equation": "f = a*(1/λ) + b",
        "slope": float(slope),
        "intercept": float(intercept),
        "r2": float(r2),
    }


def discover_inverse_law(dataset: List[Dict[str, Any]]) -> Dict[str, float]:
    wavelengths = np.array([d["wavelength"] for d in dataset], dtype=float)
    frequencies = np.array([d["frequency"] for d in dataset], dtype=float)

    k = float(np.mean(wavelengths * frequencies))
    predicted = k / wavelengths
    error = float(np.mean(np.abs(predicted - frequencies)))

    return {
        "equation": "f = k / λ",
        "k": k,
        "error": error,
    }


def score_hypothesis(law: Dict[str, float], dataset: List[Dict[str, Any]]) -> float:
    errors = []
    for item in dataset:
        predicted = law["k"] / item["wavelength"]
        errors.append(abs(predicted - item["frequency"]))
    return float(np.mean(errors)) if errors else float("inf")


def symmetry_hypotheses(features: Dict[str, Any]) -> List[str]:
    """Generate symmetry-based hypothesis strings."""
    hypotheses: List[str] = []
    if features.get("symmetry_group") == "SO2":
        hypotheses.append("angular_momentum_conserved")
    if str(features.get("symmetry_group", "")).startswith("D"):
        hypotheses.append("dihedral_symmetry_structures")
    return hypotheses


def harmonic_hypotheses(features: Dict[str, Any]) -> List[str]:
    """Generate hypotheses based on harmonic ratio detection."""
    hypotheses: List[str] = []
    if features.get("integer_harmonics"):
        hypotheses.append("standing_wave_resonance")
    if features.get("phi_harmonics"):
        hypotheses.append("golden_ratio_structure")
    return hypotheses
