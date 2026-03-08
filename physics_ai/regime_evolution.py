"""Detect regime merge/split events across generations."""

from __future__ import annotations

from typing import Dict, Iterable, List, Set

import pandas as pd


def _signature_tokens(signature: str) -> Set[str]:
    return {token for token in signature.split("_") if token}


def _similarity(a: str, b: str) -> float:
    tokens_a = _signature_tokens(a)
    tokens_b = _signature_tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def detect_regime_transitions(
    df: pd.DataFrame,
    generation_column: str = "generation",
    signature_column: str = "regime_signature",
    min_count: int = 3,
    min_similarity: float = 0.4,
) -> pd.DataFrame:
    """Return merge/split events based on regime signature overlap."""
    if generation_column not in df.columns or signature_column not in df.columns:
        return pd.DataFrame()
    data = df[[generation_column, signature_column]].dropna()
    if data.empty:
        return pd.DataFrame()

    counts = (
        data.groupby([generation_column, signature_column])
        .size()
        .reset_index(name="count")
    )
    generations = sorted(counts[generation_column].unique())
    events: List[Dict[str, object]] = []

    for idx in range(len(generations) - 1):
        gen = generations[idx]
        next_gen = generations[idx + 1]
        current = counts[counts[generation_column] == gen]
        nxt = counts[counts[generation_column] == next_gen]
        current_signatures = current[signature_column].tolist()
        next_signatures = nxt[signature_column].tolist()

        similarity_map: Dict[str, List[str]] = {sig: [] for sig in current_signatures}
        reverse_map: Dict[str, List[str]] = {sig: [] for sig in next_signatures}

        for sig in current_signatures:
            for nxt_sig in next_signatures:
                if _similarity(sig, nxt_sig) >= min_similarity:
                    similarity_map[sig].append(nxt_sig)
                    reverse_map[nxt_sig].append(sig)

        for sig, children in similarity_map.items():
            parent_count = int(current[current[signature_column] == sig]["count"].iloc[0])
            child_counts = nxt[nxt[signature_column].isin(children)]["count"].sum()
            if len(children) >= 2 and parent_count >= min_count and child_counts >= min_count:
                events.append({
                    "event": "split",
                    "generation": int(next_gen),
                    "parent_signatures": sig,
                    "child_signatures": ", ".join(sorted(children)),
                    "parent_count": parent_count,
                    "child_count": int(child_counts),
                })

        for sig, parents in reverse_map.items():
            child_count = int(nxt[nxt[signature_column] == sig]["count"].iloc[0])
            parent_counts = current[current[signature_column].isin(parents)]["count"].sum()
            if len(parents) >= 2 and child_count >= min_count and parent_counts >= min_count:
                events.append({
                    "event": "merge",
                    "generation": int(next_gen),
                    "parent_signatures": ", ".join(sorted(parents)),
                    "child_signatures": sig,
                    "parent_count": int(parent_counts),
                    "child_count": child_count,
                })

    if not events:
        return pd.DataFrame()
    return pd.DataFrame(events)
