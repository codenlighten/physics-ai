"""Gauge symmetry discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np


@dataclass
class GaugeResult:
    global_phase_invariant: bool
    local_phase_invariant: bool
    global_delta: float
    local_delta: float


def phase_transform(field: np.ndarray, theta: np.ndarray | float) -> np.ndarray:
    return field * np.exp(1j * theta)


def action_proxy(field: np.ndarray) -> float:
    magnitudes = np.abs(field)
    return float(np.sum(magnitudes ** 2))


def gauge_invariance(frames: np.ndarray, epsilon: float = 1e-3) -> GaugeResult:
    if frames.size == 0:
        return GaugeResult(False, False, 1.0, 1.0)
    base_action = action_proxy(frames[-1])
    theta = np.random.default_rng(0).uniform(0, 2 * np.pi)
    global_action = action_proxy(phase_transform(frames[-1], theta))
    global_delta = abs(global_action - base_action) / (abs(base_action) + 1e-8)

    local_theta = np.random.default_rng(1).uniform(0, 2 * np.pi, size=frames[-1].shape)
    local_action = action_proxy(phase_transform(frames[-1], local_theta))
    local_delta = abs(local_action - base_action) / (abs(base_action) + 1e-8)

    return GaugeResult(
        global_phase_invariant=global_delta < epsilon,
        local_phase_invariant=local_delta < epsilon,
        global_delta=float(global_delta),
        local_delta=float(local_delta),
    )


def gauge_summary(result: GaugeResult) -> Dict[str, Any]:
    return {
        "global_phase_invariant": result.global_phase_invariant,
        "local_phase_invariant": result.local_phase_invariant,
        "global_delta": result.global_delta,
        "local_delta": result.local_delta,
    }
