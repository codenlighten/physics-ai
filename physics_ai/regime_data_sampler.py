"""Sampling helpers for symbolic law extraction."""

from __future__ import annotations

from typing import List

import pandas as pd


def sample_regime_observations(
    df: pd.DataFrame,
    regime_column: str = "regime_signature",
    score_column: str = "score",
    max_per_regime: int = 5,
) -> pd.DataFrame:
    if regime_column not in df.columns:
        return df.head(max_per_regime)
    if score_column not in df.columns:
        sampled = df.groupby(regime_column).head(max_per_regime)
    else:
        sampled = (
            df.sort_values(score_column, ascending=False)
            .groupby(regime_column)
            .head(max_per_regime)
        )
    return sampled.reset_index(drop=True)