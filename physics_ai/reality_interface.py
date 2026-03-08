"""Reality interface for validating hypotheses against external datasets."""

from __future__ import annotations

import csv
from typing import Dict, List, Iterable


def load_wave_dataset(path: str) -> List[Dict[str, float]]:
    dataset: List[Dict[str, float]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if "frequency" in row and "wavelength" in row:
                dataset.append({
                    "frequency": float(row["frequency"]),
                    "wavelength": float(row["wavelength"]),
                })
    return dataset


def validate_inverse_law(law: Dict[str, float], dataset: Iterable[Dict[str, float]]) -> float:
    errors: List[float] = []
    for item in dataset:
        predicted = law["k"] / item["wavelength"]
        errors.append(abs(predicted - item["frequency"]))
    return sum(errors) / len(errors) if errors else float("inf")
