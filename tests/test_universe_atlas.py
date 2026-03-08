import pandas as pd

from physics_ai.universe_atlas import build_feature_matrix, embed_universes
from physics_ai.universe_atlas import select_sparse_seeds


def test_build_feature_matrix() -> None:
    df = pd.DataFrame(
        {
            "score": [1.0, 2.0],
            "score_raw": [1.2, 2.1],
            "particle_count": [0, 2],
            "resonance_strength": [0.1, 0.4],
            "variance": [0.05, 0.2],
            "dispersion_type": ["wave", "diffusion"],
            "phase": ["LINEAR_WAVE", "TURBULENT_FIELD"],
        }
    )
    matrix, names = build_feature_matrix(df)
    assert matrix.shape[0] == 2
    assert len(names) >= 5


def test_embed_universes_tsne() -> None:
    df = pd.DataFrame(
        {
            "score": [1.0, 2.0, 3.0],
            "score_raw": [1.1, 2.1, 3.1],
            "particle_count": [0, 1, 2],
            "resonance_strength": [0.1, 0.4, 0.6],
            "variance": [0.05, 0.2, 0.3],
            "dispersion_type": ["wave", "diffusion", "wave"],
            "phase": ["LINEAR_WAVE", "TURBULENT_FIELD", "SOLITON_FIELD"],
        }
    )
    embedded = embed_universes(df, method="tsne", perplexity=2.0)
    assert "atlas_x" in embedded.columns
    assert "atlas_y" in embedded.columns


def test_select_sparse_seeds() -> None:
    df = pd.DataFrame(
        {
            "atlas_x": [0.0, 0.1, 2.0, 3.0],
            "atlas_y": [0.0, 0.1, 2.0, 3.0],
        }
    )
    seeds = select_sparse_seeds(df, k=2)
    assert len(seeds) == 2
