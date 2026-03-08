"""Equation library mutation utilities for adaptive law evolution."""

from __future__ import annotations

from typing import Dict, List

import numpy as np

TERM_LIBRARY = ["laplacian", "nonlinear", "biharmonic"]


def default_terms() -> List[str]:
    return ["laplacian"]


def mutate_terms(rng: np.random.Generator, terms: List[str], p_toggle: float = 0.2) -> List[str]:
    active = set(terms)
    for term in TERM_LIBRARY:
        if rng.random() < p_toggle:
            if term in active:
                active.remove(term)
            else:
                active.add(term)
    if "laplacian" not in active:
        active.add("laplacian")
    return sorted(active)


def apply_terms(config: Dict[str, float], terms: List[str]) -> Dict[str, float]:
    updated = dict(config)
    if "nonlinear" not in terms:
        updated["wave_nonlinear"] = 0.0
    if "biharmonic" not in terms:
        updated["wave_biharmonic"] = 0.0
    return updated
