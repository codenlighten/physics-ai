"""Evolutionary hypothesis search helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class Hypothesis:
    equation: str
    params: Dict[str, float]
    score: float = float("inf")


def evaluate(hypothesis: Hypothesis, dataset: List[Dict[str, float]]) -> float:
    errors: List[float] = []
    for item in dataset:
        x = item["wavelength"]
        y = item["frequency"]
        k = hypothesis.params["k"]

        if hypothesis.equation == "k/x":
            pred = k / x
        elif hypothesis.equation == "k*x":
            pred = k * x
        elif hypothesis.equation == "k/x^2":
            pred = k / (x ** 2)
        elif hypothesis.equation == "k*sqrt(x)":
            pred = k * np.sqrt(x)
        elif hypothesis.equation == "k*log(x)":
            pred = k * np.log(x)
        else:
            continue
        errors.append(abs(pred - y))

    hypothesis.score = float(np.mean(errors)) if errors else float("inf")
    return hypothesis.score


def initialize_population(seed: int | None = None) -> List[Hypothesis]:
    rng = np.random.default_rng(seed)
    equations = ["k/x", "k*x", "k/x^2", "k*log(x)", "k*sqrt(x)"]
    return [Hypothesis(eq, {"k": float(rng.uniform(0.5, 2.0))}) for eq in equations]


def select_best(population: List[Hypothesis], count: int = 3) -> List[Hypothesis]:
    return sorted(population, key=lambda h: h.score)[:count]


def mutate(hypothesis: Hypothesis, seed: int | None = None) -> Hypothesis:
    rng = np.random.default_rng(seed)
    new_k = hypothesis.params["k"] * (1 + float(rng.normal(0, 0.05)))
    return Hypothesis(hypothesis.equation, {"k": new_k})


def evolve(population: List[Hypothesis], dataset: List[Dict[str, float]], generations: int = 10) -> Hypothesis:
    for _ in range(generations):
        for hyp in population:
            evaluate(hyp, dataset)
        survivors = select_best(population)
        new_population = survivors.copy()
        while len(new_population) < len(population):
            parent = np.random.choice(survivors)
            new_population.append(mutate(parent))
        population = new_population
    return min(population, key=lambda h: h.score)
