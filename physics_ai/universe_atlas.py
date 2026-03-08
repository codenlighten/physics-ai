"""Universe atlas utilities for embedding discovered physics regimes."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd
import numpy as np


def load_universe_shards(run_dir: str | Path) -> pd.DataFrame:
    run_path = Path(run_dir)
    shards = sorted(run_path.glob("universes_batch_*.parquet"))
    if not shards:
        raise FileNotFoundError("No universe shard parquet files found.")
    frames = [pd.read_parquet(path) for path in shards]
    return pd.concat(frames, ignore_index=True)


def _encode_categories(series: pd.Series) -> Tuple[pd.Series, List[str]]:
    categories = sorted({str(value) for value in series.dropna().unique()})
    mapping = {cat: idx for idx, cat in enumerate(categories)}
    encoded = series.fillna("unknown").map(lambda value: mapping.get(str(value), -1))
    return encoded.astype(float), categories


def build_feature_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    columns = [
        "score_raw",
        "score",
        "particle_count",
        "resonance_strength",
        "curvature_strength",
        "variance",
        "spectral_entropy",
        "energy_localization",
        "diversity_penalty",
        "novelty_bonus",
    ]
    features = []
    feature_names: List[str] = []
    for col in columns:
        if col in df.columns:
            features.append(df[col].fillna(0.0).to_numpy(dtype=float))
            feature_names.append(col)
    if "dispersion_type" in df.columns:
        encoded, categories = _encode_categories(df["dispersion_type"])
        features.append(encoded.to_numpy(dtype=float))
        feature_names.append("dispersion_type")
    if "phase" in df.columns:
        encoded, categories = _encode_categories(df["phase"])
        features.append(encoded.to_numpy(dtype=float))
        feature_names.append("phase")
    if not features:
        raise ValueError("No feature columns available for atlas embedding.")
    matrix = np.stack(features, axis=1)
    return matrix, feature_names


def embed_universes(
    df: pd.DataFrame,
    method: str = "umap",
    random_state: int = 42,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    perplexity: float = 10.0,
) -> pd.DataFrame:
    features, _ = build_feature_matrix(df)
    method_lower = method.lower()
    if method_lower == "umap":
        try:
            import umap  # type: ignore
        except ImportError as exc:
            raise RuntimeError("UMAP is not installed. Install umap-learn or use --method tsne.") from exc
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=random_state,
        )
        coords = reducer.fit_transform(features)
    elif method_lower == "tsne":
        from sklearn.manifold import TSNE

        reducer = TSNE(
            n_components=2,
            random_state=random_state,
            perplexity=perplexity,
            init="random",
            learning_rate="auto",
        )
        coords = reducer.fit_transform(features)
    else:
        raise ValueError("method must be 'umap' or 'tsne'")

    embedded = df.copy()
    embedded["atlas_x"] = coords[:, 0]
    embedded["atlas_y"] = coords[:, 1]
    return embedded


def save_atlas(df: pd.DataFrame, output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.suffix == ".parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path


def select_sparse_seeds(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    if "atlas_x" not in df.columns or "atlas_y" not in df.columns:
        raise ValueError("Atlas coordinates missing. Run embed_universes first.")
    coords = df[["atlas_x", "atlas_y"]].to_numpy(dtype=float)
    if coords.shape[0] <= k:
        return df
    distances = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
    distances[distances == 0] = np.inf
    min_dist = np.min(distances, axis=1)
    selected_idx = np.argsort(min_dist)[-k:]
    return df.iloc[selected_idx]
