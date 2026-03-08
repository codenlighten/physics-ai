"""Topological defect detection utilities."""

from __future__ import annotations

from typing import Dict, Any

import numpy as np


def _wrap_phase(delta: np.ndarray) -> np.ndarray:
    return (delta + np.pi) % (2 * np.pi) - np.pi


def vortex_count(field: np.ndarray, threshold: float = np.pi) -> int:
    if not np.iscomplexobj(field):
        return 0
    phase = np.angle(field)
    dpx = _wrap_phase(np.diff(phase, axis=0))
    dpy = _wrap_phase(np.diff(phase, axis=1))
    winding = dpx[:, :-1] + dpy[1:, :] - dpx[:, 1:] - dpy[:-1, :]
    return int(np.sum(np.abs(winding) > threshold))


def nodal_loop_count(field: np.ndarray) -> int:
    real_field = np.real(field)
    sign = np.sign(real_field)
    sign[sign == 0] = 1
    horizontal = np.sum(sign[:, :-1] * sign[:, 1:] < 0)
    vertical = np.sum(sign[:-1, :] * sign[1:, :] < 0)
    return int(horizontal + vertical)


def coherence_length(field: np.ndarray) -> float:
    values = np.real(field)
    fft = np.fft.fft2(values)
    power = np.abs(fft) ** 2
    corr = np.fft.ifft2(power).real
    corr /= np.max(corr) if np.max(corr) != 0 else 1.0
    center = corr[0]
    drop_idx = np.argmax(center < 0.5)
    if drop_idx == 0:
        drop_idx = len(center) - 1
    return float(drop_idx)


def defect_summary(field: np.ndarray) -> Dict[str, Any]:
    loops = nodal_loop_count(field)
    vortices = vortex_count(field)
    size = field.shape[0] * field.shape[1] if field.ndim >= 2 else 1
    return {
        "vortex_count": vortices,
        "nodal_loop_count": loops,
        "defect_density": float((loops + vortices) / size) if size else 0.0,
        "coherence_length": coherence_length(field),
    }
