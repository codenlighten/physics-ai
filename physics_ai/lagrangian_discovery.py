"""Lagrangian discovery utilities for scalar time series."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import sympy as sp


@dataclass
class LagrangianResult:
    lagrangian: str
    residual_mse: float
    residual_mean: float


def candidate_lagrangians() -> List[sp.Expr]:
    q, qd = sp.symbols("q qd")
    return [
        0.5 * qd ** 2,
        0.5 * qd ** 2 - 0.5 * q ** 2,
        0.5 * qd ** 2 - 0.25 * q ** 4,
        0.5 * qd ** 2 - sp.sin(q),
    ]


def _finite_derivatives(signal: np.ndarray, dt: float) -> tuple[np.ndarray, np.ndarray]:
    velocity = np.gradient(signal, dt)
    accel = np.gradient(velocity, dt)
    return velocity, accel


def _residual_for_lagrangian(
    lagrangian: sp.Expr,
    q_values: np.ndarray,
    qd_values: np.ndarray,
    qdd_values: np.ndarray,
) -> np.ndarray:
    q, qd = sp.symbols("q qd")
    d_ldq = sp.diff(lagrangian, q)
    d_ldqd = sp.diff(lagrangian, qd)
    f_dldq = sp.lambdify((q, qd), d_ldq, "numpy")
    f_dldqd = sp.lambdify((q, qd), d_ldqd, "numpy")

    dldq = f_dldq(q_values, qd_values)
    dldqd = f_dldqd(q_values, qd_values)
    ddt_dldqd = np.gradient(dldqd)
    return ddt_dldqd - dldq


def score_lagrangian(
    lagrangian: sp.Expr,
    signal: np.ndarray,
    dt: float = 1.0,
) -> LagrangianResult:
    qd, qdd = _finite_derivatives(signal, dt)
    residual = _residual_for_lagrangian(lagrangian, signal, qd, qdd)
    residual_mse = float(np.mean(residual ** 2))
    residual_mean = float(np.mean(residual))
    return LagrangianResult(
        lagrangian=str(sp.simplify(lagrangian)),
        residual_mse=residual_mse,
        residual_mean=residual_mean,
    )


def discover_lagrangian(
    signal: Iterable[float],
    dt: float = 1.0,
    candidates: Iterable[sp.Expr] | None = None,
) -> LagrangianResult | None:
    values = np.array(list(signal), dtype=float)
    if values.size < 4:
        return None
    best: LagrangianResult | None = None
    for lagrangian in candidates or candidate_lagrangians():
        result = score_lagrangian(lagrangian, values, dt=dt)
        if best is None or result.residual_mse < best.residual_mse:
            best = result
    return best
