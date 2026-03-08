"""Operator library for symbolic law extraction."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def _laplacian(field: np.ndarray) -> np.ndarray:
    return (
        -4 * field
        + np.roll(field, 1, axis=0)
        + np.roll(field, -1, axis=0)
        + np.roll(field, 1, axis=1)
        + np.roll(field, -1, axis=1)
    )


def build_operator_matrix(
    signal: List[float],
    field: np.ndarray | None = None,
    dt: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    if len(signal) < 3:
        return np.empty((0, 0)), np.empty((0,)), []
    data = np.array(signal, dtype=float)
    d_dt = np.gradient(data, dt)
    x = data
    features = [x, x ** 3, x ** 5]
    names = ["psi", "psi^3", "psi^5"]
    if field is not None:
        field = np.asarray(field, dtype=float)
        lap = _laplacian(field)
        bih = _laplacian(lap)
        nonlinear = np.mean(np.abs(field) ** 2 * field)
        lap_mean = float(np.mean(lap))
        bih_mean = float(np.mean(bih))
        features.extend([
            np.full_like(x, lap_mean),
            np.full_like(x, bih_mean),
            np.full_like(x, nonlinear),
        ])
        names.extend(["laplacian", "biharmonic", "abs(psi)^2 psi"])
    matrix = np.stack(features, axis=1)
    return matrix, d_dt, names


def build_coupled_operator_matrices(
    psi_signal: List[float],
    phi_signal: List[float],
    psi_field: np.ndarray | None = None,
    phi_field: np.ndarray | None = None,
    dt: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, List[str], np.ndarray, np.ndarray, List[str]]:
    if len(psi_signal) < 3 or len(phi_signal) < 3:
        empty = np.empty((0, 0))
        return empty, np.empty((0,)), [], empty, np.empty((0,)), []
    psi = np.array(psi_signal, dtype=float)
    phi = np.array(phi_signal, dtype=float)
    dpsi = np.gradient(psi, dt)
    dphi = np.gradient(phi, dt)

    features = [
        psi,
        psi ** 3,
        psi ** 5,
        phi,
        phi ** 3,
        psi * phi,
        (psi ** 2) * phi,
        (phi ** 2) * psi,
    ]
    names = [
        "psi",
        "psi^3",
        "psi^5",
        "phi",
        "phi^3",
        "psi*phi",
        "psi^2*phi",
        "phi^2*psi",
    ]
    if psi_field is not None:
        psi_field = np.asarray(psi_field, dtype=float)
        psi_lap = _laplacian(psi_field)
        psi_lap_mean = float(np.mean(psi_lap))
        features.append(np.full_like(psi, psi_lap_mean))
        names.append("laplacian_psi")
    if phi_field is not None:
        phi_field = np.asarray(phi_field, dtype=float)
        phi_lap = _laplacian(phi_field)
        phi_lap_mean = float(np.mean(phi_lap))
        features.append(np.full_like(phi, phi_lap_mean))
        names.append("laplacian_phi")

    matrix = np.stack(features, axis=1)
    return matrix, dpsi, names, matrix, dphi, names