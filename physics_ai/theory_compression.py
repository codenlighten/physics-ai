"""Rank candidate theories by error and complexity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class TheoryCandidate:
    name: str
    equation: str
    error: float


@dataclass
class TheoryScore:
    name: str
    equation: str
    error: float
    complexity: float
    score: float


def estimate_complexity(equation: str) -> float:
    return float(len(equation))


def rank_theories(
    candidates: Iterable[TheoryCandidate],
    complexity_weight: float = 0.01,
) -> List[TheoryScore]:
    scores: List[TheoryScore] = []
    for candidate in candidates:
        complexity = estimate_complexity(candidate.equation)
        score = float(candidate.error + complexity_weight * complexity)
        scores.append(
            TheoryScore(
                name=candidate.name,
                equation=candidate.equation,
                error=candidate.error,
                complexity=complexity,
                score=score,
            )
        )
    return sorted(scores, key=lambda item: item.score)
