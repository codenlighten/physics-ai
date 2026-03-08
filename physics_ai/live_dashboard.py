"""Live physics map dashboard using Streamlit."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional
import ast

import pandas as pd

from .surprise_detector import annotate_surprise
from .universe_atlas import embed_universes, load_universe_shards


def build_live_atlas(run_dir: str | Path, method: str = "umap") -> pd.DataFrame:
    df = load_universe_shards(run_dir)
    return embed_universes(df, method=method)


def _normalize_terms(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(term) for term in value]
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(term) for term in parsed]
        except (ValueError, SyntaxError):
            return [value]
        return [value]
    return [str(value)]


def _term_frequency(df: pd.DataFrame) -> pd.DataFrame:
    if "wave_terms" not in df.columns:
        return pd.DataFrame()
    terms = df["wave_terms"].apply(_normalize_terms)
    exploded = df.copy()
    exploded["wave_terms"] = terms
    exploded = exploded.explode("wave_terms")
    exploded = exploded[exploded["wave_terms"].notna() & (exploded["wave_terms"] != "")]
    if exploded.empty:
        return pd.DataFrame()
    return exploded


def main() -> None:
    try:
        import streamlit as st
        import plotly.express as px
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Install streamlit and plotly to use the live dashboard.") from exc

    st.set_page_config(page_title="Physics Atlas", layout="wide")
    st.title("Live Physics Map")

    with st.sidebar:
        run_dir = st.text_input("Run directory", value="experiments")
        method = st.selectbox("Embedding method", ["umap", "tsne"], index=0)
        color_by = st.selectbox(
            "Color by",
            ["phase", "score", "defect_density", "novelty_bonus", "surprise"],
            index=0,
        )
        size_by = st.selectbox("Size by", ["score", "score_raw", "particle_count"], index=0)
        st.subheader("Surprise detector")
        score_threshold = st.number_input("Score threshold", min_value=0.0, value=8.0, step=0.1)
        novelty_threshold = st.number_input("Novelty threshold", min_value=0.0, value=1.0, step=0.1)
        distance_threshold = st.number_input("Atlas distance threshold", min_value=0.0, value=0.5, step=0.05)
        refresh = st.checkbox("Auto-refresh", value=False)
        refresh_rate = st.number_input("Refresh seconds", min_value=5, max_value=120, value=15)
        if refresh:
            st.autorefresh(interval=int(refresh_rate * 1000), key="atlas_refresh")

    run_path = Path(run_dir)
    if not run_path.is_dir():
        st.warning("Run directory not found.")
        return

    df = build_live_atlas(run_path, method=method)
    df = annotate_surprise(
        df,
        score_threshold=score_threshold,
        novelty_threshold=novelty_threshold,
        distance_threshold=distance_threshold,
    )

    if color_by not in df.columns:
        color_by = "score"
    if size_by not in df.columns:
        size_by = "score"

    tabs = st.tabs([
        "Universe Atlas",
        "Defect Topology",
        "Equation Evolution",
        "Phase Timeline",
        "Leaderboard",
        "Surprise Alerts",
    ])

    with tabs[0]:
        fig = px.scatter(
            df,
            x="atlas_x",
            y="atlas_y",
            color=color_by,
            size=size_by,
            hover_data=["universe_id", "phase", "score", "score_raw", "atlas_distance"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        if "defect_density" in df.columns:
            defect_fig = px.scatter(
                df,
                x="atlas_x",
                y="atlas_y",
                color="defect_density",
                size="vortex_count" if "vortex_count" in df.columns else size_by,
                hover_data=["universe_id", "phase", "defect_density", "vortex_count", "nodal_loop_count"],
                color_continuous_scale="Turbo",
            )
            st.plotly_chart(defect_fig, use_container_width=True)
            st.dataframe(
                df.sort_values("defect_density", ascending=False)
                .head(10)
                .loc[:, [
                    col
                    for col in [
                        "universe_id",
                        "phase",
                        "defect_density",
                        "vortex_count",
                        "nodal_loop_count",
                        "coherence_length",
                    ]
                    if col in df.columns
                ]]
            )
        else:
            st.info("Defect metrics not available in the current run.")

    with tabs[2]:
        term_data = _term_frequency(df)
        if term_data.empty:
            st.info("Equation term history not available yet.")
        else:
            if "generation" in term_data.columns and term_data["generation"].notna().any():
                term_counts = (
                    term_data.groupby(["generation", "wave_terms"]).size().reset_index(name="count")
                )
                term_fig = px.area(
                    term_counts,
                    x="generation",
                    y="count",
                    color="wave_terms",
                    line_group="wave_terms",
                )
                st.plotly_chart(term_fig, use_container_width=True)
            top_terms = (
                term_data["wave_terms"].value_counts().reset_index()
                .rename(columns={"index": "term", "wave_terms": "count"})
            )
            st.dataframe(top_terms.head(12))

    with tabs[3]:
        if "generation" in df.columns and df["generation"].notna().any() and "phase" in df.columns:
            phase_counts = (
                df.groupby(["generation", "phase"]).size().reset_index(name="count")
            )
            phase_fig = px.area(phase_counts, x="generation", y="count", color="phase")
            st.plotly_chart(phase_fig, use_container_width=True)
        elif "phase" in df.columns:
            phase_summary = df["phase"].value_counts().reset_index()
            phase_summary.columns = ["phase", "count"]
            phase_fig = px.bar(phase_summary, x="phase", y="count")
            st.plotly_chart(phase_fig, use_container_width=True)
        else:
            st.info("Phase distribution not available in the current run.")

    with tabs[4]:
        leaderboard_cols = [
            col
            for col in [
                "universe_id",
                "score",
                "phase",
                "defect_density",
                "novelty_bonus",
                "atlas_distance",
                "wave_terms",
            ]
            if col in df.columns
        ]
        leaderboard = df.sort_values("score", ascending=False).head(20)
        st.dataframe(leaderboard.loc[:, leaderboard_cols])

    with tabs[5]:
        surprises = df[df["surprise"]].sort_values("score", ascending=False)
        if surprises.empty:
            st.success("No surprise regimes detected with current thresholds.")
        else:
            for _, row in surprises.head(5).iterrows():
                label = (
                    f"🚨 NEW PHYSICS REGIME DETECTED · Universe {row.get('universe_id')} · "
                    f"Score {row.get('score', 0):.2f} · Phase {row.get('phase', 'unknown')}"
                )
                st.warning(label)
            st.dataframe(
                surprises.loc[:, leaderboard_cols].head(20)
                if leaderboard_cols
                else surprises.head(20)
            )

    if refresh:
        st.caption(f"Auto-refresh every {refresh_rate} seconds")


if __name__ == "__main__":
    main()
