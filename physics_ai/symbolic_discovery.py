"""Symbolic law discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Iterable, Callable

import numpy as np
import sympy as sp


@dataclass
class SymbolicLaw:
    law: str
    confidence: float
    variables: List[str]
    constant: float
    error: float


def candidate_forms(templates: Iterable[str] | None = None) -> List[sp.Expr]:
    x, k = sp.symbols("x k")
    mapping = {
        "k*x": k * x,
        "k/x": k / x,
        "k*x**2": k * x ** 2,
        "k/x**2": k / (x ** 2),
        "k/sqrt(x)": k / sp.sqrt(x),
        "k*sqrt(x)": k * sp.sqrt(x),
        "k*log(x)": k * sp.log(x),
        "k*exp(x)": k * sp.exp(x),
    }
    if templates:
        return [mapping[t] for t in templates if t in mapping]
    return list(mapping.values())


def fit_constant(x: np.ndarray, y: np.ndarray, expr: sp.Expr) -> float:
    k = sp.symbols("k")
    f = sp.lambdify((k, sp.symbols("x")), expr, "numpy")
    if np.any(x == 0):
        x = x + 1e-8
    if expr.has(sp.sqrt(sp.symbols("x"))):
        base = np.sqrt(x)
        return float(np.mean(y / base))
    if expr.has(sp.symbols("x") ** 2):
        base = x ** 2
        return float(np.mean(y / base))
    if expr.has(1 / sp.symbols("x")):
        base = 1 / x
        return float(np.mean(y / base))
    return float(np.mean(y / x))


def predict(expr: sp.Expr, k_value: float, x: np.ndarray) -> np.ndarray:
    k, x_sym = sp.symbols("k x")
    f = sp.lambdify((k, x_sym), expr, "numpy")
    return f(k_value, x)


def mse(y_pred: np.ndarray, y_true: np.ndarray) -> float:
    return float(np.mean((y_pred - y_true) ** 2))


def discover_inverse_law(
    x: np.ndarray,
    y: np.ndarray,
    templates: Iterable[str] | None = None,
    on_result: Callable[[str, float], None] | None = None,
) -> SymbolicLaw | None:
    if len(x) == 0:
        return None
    best: SymbolicLaw | None = None
    for expr in candidate_forms(templates=templates):
        k_value = fit_constant(x, y, expr)
        preds = predict(expr, k_value, x)
        error = mse(preds, y)
        confidence = 1.0 / (1.0 + error)
        law = SymbolicLaw(
            law=str(sp.simplify(expr.subs({sp.symbols("k"): k_value}))),
            confidence=confidence,
            variables=["x"],
            constant=k_value,
            error=error,
        )
        if on_result:
            on_result(str(expr), error)
        if best is None or error < best.error:
            best = law
    return best


def discover_from_dataset(
    dataset: List[Dict[str, float]],
    templates: Iterable[str] | None = None,
    on_result: Callable[[str, float], None] | None = None,
) -> SymbolicLaw | None:
    x = np.array([d["wavelength"] for d in dataset], dtype=float)
    y = np.array([d["frequency"] for d in dataset], dtype=float)
    return discover_inverse_law(x, y, templates=templates, on_result=on_result)
