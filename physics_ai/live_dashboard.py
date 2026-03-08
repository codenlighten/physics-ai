"""Live physics map dashboard using Streamlit."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, List, Set, Tuple
import json
import ast

import pandas as pd
import numpy as np

from .behavior_clustering import cluster_behavior
from .ratio_analyzer import analyze_ratios
from .regime_clustering import cluster_atlas
from .regime_evolution import detect_regime_transitions
from .regime_summarizer import summarize_behavior_clusters
from .symbolic_law_extractor import (
    extract_symbolic_laws,
    laws_to_dataframe,
    operator_importance_summary,
)
from .surprise_detector import annotate_surprise
from .universe_atlas import embed_universes, load_universe_shards
from .visualization import plot_field, plot_temporal_signal
from .law_validator import coupled_field_validation_score, simulate_coupled_law


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


def _signature_tokens(signature: str | None) -> Set[str]:
    if not signature:
        return set()
    return {token.strip() for token in signature.split("+") if token.strip()}


def _build_graph_layout(relations: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    nodes = pd.Series(pd.concat([relations["subject"], relations["object"]]).dropna().unique())
    if nodes.empty:
        return pd.DataFrame(), pd.DataFrame()
    angles = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
    node_df = pd.DataFrame({
        "node": nodes.values,
        "x": np.cos(angles),
        "y": np.sin(angles),
    })
    node_lookup = node_df.set_index("node")
    edge_rows = []
    for _, row in relations.iterrows():
        subject = row.get("subject")
        obj = row.get("object")
        if subject not in node_lookup.index or obj not in node_lookup.index:
            continue
        edge_rows.append({
            "x0": node_lookup.loc[subject, "x"],
            "y0": node_lookup.loc[subject, "y"],
            "x1": node_lookup.loc[obj, "x"],
            "y1": node_lookup.loc[obj, "y"],
            "relation": row.get("relation"),
            "subject": subject,
            "object": obj,
        })
    edge_df = pd.DataFrame(edge_rows)
    return node_df, edge_df


def _graph_degrees(edges: pd.DataFrame) -> dict[str, int]:
    degrees: dict[str, int] = {}
    for _, row in edges.iterrows():
        degrees[str(row["subject"])] = degrees.get(str(row["subject"]), 0) + 1
        degrees[str(row["object"])] = degrees.get(str(row["object"]), 0) + 1
    return degrees


def _cluster_signatures(signatures: List[str], threshold: float = 0.5) -> pd.DataFrame:
    clusters: List[Set[str]] = []
    cluster_labels: List[int] = []
    for sig in signatures:
        tokens = _signature_tokens(sig)
        assigned = False
        for idx, cluster in enumerate(clusters):
            union = tokens | cluster
            intersection = tokens & cluster
            similarity = len(intersection) / len(union) if union else 0.0
            if similarity >= threshold:
                clusters[idx] = union
                cluster_labels.append(idx)
                assigned = True
                break
        if not assigned:
            clusters.append(set(tokens))
            cluster_labels.append(len(clusters) - 1)
    return pd.DataFrame({
        "law_signature": signatures,
        "signature_cluster": cluster_labels,
    })


def _family_from_signature(signature: str) -> str:
    tokens = _signature_tokens(signature)
    if {"psi*phi", "psi^2*phi", "phi^2*psi"} & tokens:
        return "reaction-diffusion"
    if "psi^5" in tokens or "phi^3" in tokens:
        return "ginsburg-landau"
    if "biharmonic" in tokens:
        return "swift-hohenberg"
    if "laplacian" in tokens or "laplacian_psi" in tokens:
        return "nonlinear-wave"
    return "other"


def main() -> None:
    try:
        import streamlit as st
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError("Install streamlit and plotly to use the live dashboard.") from exc

    st.set_page_config(page_title="Physics Atlas", layout="wide")
    st.title("Live Physics Map")

    with st.sidebar:
        run_dir = st.text_input("Run directory", value="experiments")
        method = st.selectbox("Embedding method", ["umap", "tsne"], index=0)
        color_by = st.selectbox(
            "Color by",
            [
                "phase",
                "score",
                "defect_density",
                "novelty_bonus",
                "local_density",
                "density_score",
                "density_surprise",
                "cluster_id",
                "cluster_probability",
                "cluster_outlier",
                "behavior_cluster_id",
                "behavior_cluster_probability",
                "behavior_cluster_outlier",
                "surprise",
            ],
            index=0,
        )
        size_by = st.selectbox("Size by", ["score", "score_raw", "particle_count"], index=0)
        view_mode = st.selectbox(
            "View mode",
            ["Structural Regimes", "Behavioral Regimes", "Comparison"],
            index=0,
        )
        st.subheader("Surprise detector")
        score_threshold = st.number_input("Score threshold", min_value=0.0, value=8.0, step=0.1)
        novelty_threshold = st.number_input("Novelty threshold", min_value=0.0, value=1.0, step=0.1)
        distance_threshold = st.number_input("Atlas distance threshold", min_value=0.0, value=0.5, step=0.05)
        density_mode = st.selectbox("Density threshold mode", ["Percentile", "Fixed value"], index=0)
        density_percentile = st.slider("Density percentile", min_value=1, max_value=50, value=10)
        density_threshold = None
        if density_mode == "Fixed value":
            density_threshold = st.number_input("Density threshold", min_value=0.0, value=0.15, step=0.01)
        density_k = st.slider("Density k-neighbors", min_value=3, max_value=25, value=10)
        st.subheader("Regime clustering")
        min_cluster_size = st.slider("Min cluster size", min_value=5, max_value=50, value=15)
        min_samples = st.slider("Min samples", min_value=2, max_value=25, value=5)
        cluster_probability_threshold = st.slider(
            "Cluster probability threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
        )
        show_noise_only = st.checkbox("Show only outlier regimes", value=False)
        st.subheader("Behavioral clustering")
        behavior_min_cluster_size = st.slider(
            "Behavior min cluster size",
            min_value=5,
            max_value=50,
            value=15,
        )
        behavior_min_samples = st.slider(
            "Behavior min samples",
            min_value=2,
            max_value=25,
            value=5,
        )
        behavior_probability_threshold = st.slider(
            "Behavior cluster probability",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
        )
        refresh = st.checkbox("Auto-refresh", value=False)
        refresh_rate = st.number_input("Refresh seconds", min_value=5, max_value=120, value=15)
        if refresh:
            st.autorefresh(interval=int(refresh_rate * 1000), key="atlas_refresh")

    run_path = Path(run_dir)
    if not run_path.is_dir():
        st.warning("Run directory not found.")
        return

    df = build_live_atlas(run_path, method=method)
    df, _ = cluster_atlas(
        df,
        min_cluster_size=int(min_cluster_size),
        min_samples=int(min_samples),
    )
    df = annotate_surprise(
        df,
        score_threshold=score_threshold,
        novelty_threshold=novelty_threshold,
        distance_threshold=distance_threshold,
        density_threshold=density_threshold,
        density_percentile=float(density_percentile),
        density_k=int(density_k),
        cluster_probability_threshold=float(cluster_probability_threshold),
    )
    df, _ = cluster_behavior(
        df,
        min_cluster_size=int(behavior_min_cluster_size),
        min_samples=int(behavior_min_samples),
        probability_threshold=float(behavior_probability_threshold),
    )
    summary_df = summarize_behavior_clusters(df)
    if not summary_df.empty:
        signature_map = dict(zip(summary_df["cluster_id"], summary_df["regime_signature"]))
        df["regime_signature"] = df["behavior_cluster_id"].map(signature_map).fillna("unknown")
    df, ratio_df, ratio_clusters = analyze_ratios(df)
    law_results = extract_symbolic_laws(df)
    law_df = laws_to_dataframe(law_results)
    if not law_df.empty and "law_signature" in law_df.columns:
        law_df["law_family"] = law_df["law_signature"].apply(_family_from_signature)
    if not law_df.empty:
        family_lookup = law_df.drop_duplicates("regime").set_index("regime")["law_family"].to_dict()
        df["law_family"] = df["regime_signature"].map(family_lookup)
    operator_df = operator_importance_summary(law_results)

    plot_df = df
    if show_noise_only and "cluster_outlier" in df.columns:
        plot_df = df[df["cluster_outlier"]]

    if color_by not in df.columns:
        color_by = "score"
    if size_by not in df.columns:
        size_by = "score"

    tabs = st.tabs([
        "Universe Atlas",
        "Defect Topology",
        "Equation Evolution",
        "Phase Timeline",
        "Regime Timeline",
        "Regime Evolution",
        "Leaderboard",
        "Regime Summaries",
        "Resonance Ratios",
        "Law Discovery",
        "Regime Explorer",
        "Regime Compare",
        "Atlas Statistics",
        "Symmetry",
        "Model Registry",
        "Knowledge Graph",
        "Surprise Alerts",
    ])

    with tabs[0]:
        if view_mode == "Comparison":
            left, right = st.columns(2)
            with left:
                fig_left = px.scatter(
                    plot_df,
                    x="atlas_x",
                    y="atlas_y",
                    color="cluster_id" if "cluster_id" in plot_df.columns else color_by,
                    size=size_by,
                    hover_data=[
                        "universe_id",
                        "phase",
                        "score",
                        "cluster_id",
                        "cluster_probability",
                    ],
                )
                st.plotly_chart(fig_left, use_container_width=True)
            with right:
                fig_right = px.scatter(
                    plot_df,
                    x="atlas_x",
                    y="atlas_y",
                    color="behavior_cluster_id" if "behavior_cluster_id" in plot_df.columns else color_by,
                    size=size_by,
                    hover_data=[
                        "universe_id",
                        "phase",
                        "score",
                        "behavior_cluster_id",
                        "behavior_cluster_probability",
                    ],
                )
                st.plotly_chart(fig_right, use_container_width=True)
        else:
            fig = px.scatter(
                plot_df,
                x="atlas_x",
                y="atlas_y",
                color=color_by,
                size=size_by,
                hover_data=[
                    "universe_id",
                    "phase",
                    "score",
                    "score_raw",
                    "atlas_distance",
                    "local_density",
                    "density_score",
                    "density_surprise",
                    "cluster_id",
                    "cluster_probability",
                    "cluster_size",
                    "behavior_cluster_id",
                    "behavior_cluster_probability",
                ],
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
        timeline_mode = st.selectbox(
            "Timeline mode",
            ["Structural Regimes", "Behavioral Regimes"],
            index=1,
        )
        if "generation" not in df.columns or df["generation"].notna().sum() == 0:
            st.info("Generation data is not available for timeline views.")
        else:
            if timeline_mode == "Structural Regimes":
                cluster_col = "cluster_id"
            else:
                cluster_col = "behavior_cluster_id"
            if cluster_col not in df.columns:
                st.info("Cluster data missing for selected timeline view.")
            else:
                timeline = (
                    df[df[cluster_col] >= 0]
                    .groupby(["generation", cluster_col])
                    .size()
                    .reset_index(name="count")
                )
                if timeline.empty:
                    st.info("No clustered regimes available for timeline plotting.")
                else:
                    fig = px.area(
                        timeline,
                        x="generation",
                        y="count",
                        color=cluster_col,
                    )
                    st.plotly_chart(fig, use_container_width=True)

    with tabs[5]:
        transitions = detect_regime_transitions(df)
        if transitions.empty:
            st.info("No regime merge/split events detected yet.")
        else:
            st.dataframe(transitions)

    with tabs[6]:
        leaderboard_cols = [
            col
            for col in [
                "universe_id",
                "score",
                "phase",
                "defect_density",
                "novelty_bonus",
                "atlas_distance",
                "local_density",
                "density_score",
                "cluster_id",
                "cluster_probability",
                "cluster_size",
                "behavior_cluster_id",
                "behavior_cluster_probability",
                "behavior_cluster_size",
                "wave_terms",
            ]
            if col in df.columns
        ]
        leaderboard = df.sort_values("score", ascending=False).head(20)
        st.dataframe(leaderboard.loc[:, leaderboard_cols])

    with tabs[7]:
        if summary_df.empty:
            st.info("Behavioral regime summaries are not available yet.")
        else:
            st.dataframe(summary_df)
            for _, row in summary_df.head(6).iterrows():
                st.markdown(
                    f"**Behavior Cluster {row['cluster_id']} · {row['label']}**  \
Size: {row['size']} · Mean prob: {row['mean_probability']:.2f}  \
Descriptors: {row['descriptors']}  \
Signature: {row['regime_signature']}"
                )

    with tabs[8]:
        if ratio_df.empty:
            st.info("No resonance ratios available yet.")
        else:
            ratio_fig = px.histogram(ratio_df, x="ratio", nbins=40, color="ratio_cluster_id")
            st.plotly_chart(ratio_fig, use_container_width=True)
            if not ratio_clusters.empty:
                st.dataframe(ratio_clusters)
            if "regime_signature" in df.columns:
                ratio_by_regime = (
                    ratio_df.merge(df[["universe_id", "regime_signature"]], on="universe_id", how="left")
                    .groupby(["regime_signature", "ratio_cluster_id"])
                    .size()
                    .reset_index(name="count")
                    .sort_values("count", ascending=False)
                    .head(20)
                )
                st.dataframe(ratio_by_regime)

    with tabs[9]:
        if law_df.empty:
            st.info("Symbolic law extraction needs temporal signals to run.")
        else:
            st.dataframe(law_df)
            if not operator_df.empty:
                st.subheader("Operator importance")
                st.dataframe(operator_df)
            if "law_class" in law_df.columns:
                st.subheader("Universality classes")
                class_counts = law_df["law_class"].value_counts().reset_index()
                class_counts.columns = ["law_class", "count"]
                st.dataframe(class_counts)
            for _, row in law_df.head(6).iterrows():
                coupled_score = row.get("law_coupled_match_score", 0.0)
                st.markdown(
                    f"**Regime {row['regime']}**  \
Field: {row.get('law_field', 'psi')} · Equation: {row['law_equation']}  \
Fit: {row['law_fit_score']:.3f} · Validation: {row['law_validation_score']:.3f} · "
                    f"Regime match: {row.get('law_regime_match_score', 0.0):.3f} · "
                    f"Coupled match: {coupled_score:.3f} · "
                    f"Family: {row.get('law_family', 'other')}"
                )

    with tabs[12]:
        if df.empty:
            st.info("Atlas statistics require completed runs.")
        else:
            st.subheader("Long-run atlas statistics")
            if not operator_df.empty:
                st.markdown("**Most common operators**")
                st.dataframe(operator_df)
            if "law_class" in law_df.columns and not law_df.empty:
                st.markdown("**Most stable universality classes**")
                class_counts = law_df["law_class"].value_counts().reset_index()
                class_counts.columns = ["law_class", "count"]
                st.dataframe(class_counts)
            if "law_signature" in law_df.columns and "law_validation_score" in law_df.columns:
                stability = (
                    law_df.dropna(subset=["law_signature"]).groupby("law_signature")[
                        "law_validation_score"
                    ].mean().reset_index(name="mean_validation")
                )
                if not stability.empty:
                    st.markdown("**Operator signature stability**")
                    st.dataframe(stability.sort_values("mean_validation", ascending=False).head(15))
            if {
                "law_validation_score",
                "novelty_bonus",
                "cross_field_corr",
            }.issubset(df.columns):
                st.markdown("**Stability vs novelty**")
                scatter = df.dropna(subset=["law_validation_score", "novelty_bonus"]).copy()
                if not scatter.empty:
                    scatter_fig = px.scatter(
                        scatter,
                        x="novelty_bonus",
                        y="law_validation_score",
                        color="cross_field_corr" if "cross_field_corr" in scatter.columns else None,
                        hover_data=["universe_id", "regime_signature"],
                    )
                    st.plotly_chart(scatter_fig, use_container_width=True)
            if "law_signature" in law_df.columns and "law_validation_score" in law_df.columns:
                st.markdown("**Stability heatmap (operator pairs)**")
                signatures = law_df["law_signature"].dropna().tolist()
                operators = sorted({
                    token
                    for sig in signatures
                    for token in _signature_tokens(sig)
                })
                operators = operators[:10]
                if operators:
                    heatmap = pd.DataFrame(
                        np.nan,
                        index=operators,
                        columns=operators,
                    )
                    for _, row in law_df.iterrows():
                        sig = row.get("law_signature")
                        if not sig:
                            continue
                        tokens = _signature_tokens(sig)
                        score = row.get("law_validation_score")
                        if score is None:
                            continue
                        for op_i in operators:
                            if op_i not in tokens:
                                continue
                            for op_j in operators:
                                if op_j not in tokens:
                                    continue
                                current = heatmap.loc[op_i, op_j]
                                if np.isnan(current):
                                    heatmap.loc[op_i, op_j] = float(score)
                                else:
                                    heatmap.loc[op_i, op_j] = 0.5 * (current + float(score))
                    fig = px.imshow(
                        heatmap.astype(float),
                        aspect="auto",
                        color_continuous_scale="Viridis",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            if "law_family" in law_df.columns and "law_signature" in law_df.columns:
                st.markdown("**Family stability heatmap**")
                operators = sorted({
                    token
                    for sig in law_df["law_signature"].dropna().tolist()
                    for token in _signature_tokens(sig)
                })[:8]
                families = sorted(law_df["law_family"].dropna().unique())
                if operators and families:
                    fam_heatmap = pd.DataFrame(np.nan, index=families, columns=operators)
                    for _, row in law_df.iterrows():
                        sig = row.get("law_signature")
                        family = row.get("law_family")
                        score = row.get("law_validation_score")
                        if not sig or family is None or score is None:
                            continue
                        tokens = _signature_tokens(sig)
                        for op in operators:
                            if op not in tokens:
                                continue
                            current = fam_heatmap.loc[family, op]
                            if np.isnan(current):
                                fam_heatmap.loc[family, op] = float(score)
                            else:
                                fam_heatmap.loc[family, op] = 0.5 * (current + float(score))
                    fam_fig = px.imshow(
                        fam_heatmap.astype(float),
                        aspect="auto",
                        color_continuous_scale="Cividis",
                    )
                    st.plotly_chart(fam_fig, use_container_width=True)
                    st.markdown("**Family operator-pair stability**")
                    pair_ops = operators[:6]
                    if len(pair_ops) >= 2:
                        pair_rows = []
                        for family in families:
                            for op_i in pair_ops:
                                for op_j in pair_ops:
                                    scores = []
                                    for _, row in law_df.iterrows():
                                        if row.get("law_family") != family:
                                            continue
                                        sig = row.get("law_signature")
                                        if not sig:
                                            continue
                                        tokens = _signature_tokens(sig)
                                        if op_i in tokens and op_j in tokens:
                                            score = row.get("law_validation_score")
                                            if score is not None:
                                                scores.append(float(score))
                                    if scores:
                                        pair_rows.append({
                                            "family": family,
                                            "pair": f"{op_i}+{op_j}",
                                            "mean_validation": float(np.mean(scores)),
                                        })
                        if pair_rows:
                            pair_df = pd.DataFrame(pair_rows)
                            pair_fig = px.imshow(
                                pair_df.pivot(index="family", columns="pair", values="mean_validation"),
                                aspect="auto",
                                color_continuous_scale="Plasma",
                            )
                            st.plotly_chart(pair_fig, use_container_width=True)
            if "law_signature" in law_df.columns and not law_df.empty:
                st.markdown("**Signature clusters**")
                signatures = law_df["law_signature"].dropna().tolist()
                if signatures:
                    clustered = _cluster_signatures(signatures)
                    summary = (
                        clustered.groupby("signature_cluster")["law_signature"]
                        .apply(lambda vals: ", ".join(sorted(set(vals))[:5]))
                        .reset_index(name="examples")
                    )
                    summary["cluster_size"] = clustered.groupby("signature_cluster").size().values
                    st.dataframe(summary.sort_values("cluster_size", ascending=False))
            if "law_signature" in law_df.columns and not law_df.empty:
                st.markdown("**Signature families**")
                family_df = law_df.dropna(subset=["law_signature"]).copy()
                family_df["family"] = family_df["law_signature"].apply(_family_from_signature)
                family_counts = family_df["family"].value_counts().reset_index()
                family_counts.columns = ["family", "count"]
                st.dataframe(family_counts)
                if law_results:
                    st.markdown("**Operator trends by family**")
                    trend_rows = []
                    for family in family_df["family"].unique():
                        family_laws = [
                            law
                            for law in law_results
                            if _family_from_signature(law.law_signature or "") == family
                        ]
                        if not family_laws:
                            continue
                        fam_importance = operator_importance_summary(family_laws)
                        if fam_importance.empty:
                            continue
                        top = fam_importance.iloc[0]
                        trend_rows.append({
                            "family": family,
                            "top_operator": top["operator"],
                            "frequency": top["frequency"],
                            "share": top["share"],
                        })
                    if trend_rows:
                        st.dataframe(pd.DataFrame(trend_rows))
                if {"law_validation_score"}.issubset(law_df.columns):
                    st.markdown("**Family stability vs novelty**")
                    joined = family_df.merge(
                        df[["regime_signature", "novelty_bonus"]],
                        left_on="regime",
                        right_on="regime_signature",
                        how="left",
                    )
                    joined = joined.dropna(subset=["law_validation_score"])
                    if not joined.empty:
                        summary = (
                            joined.groupby("family")
                            .agg(
                                mean_validation=("law_validation_score", "mean"),
                                mean_novelty=("novelty_bonus", "mean"),
                                count=("family", "size"),
                                p25_validation=("law_validation_score", lambda s: float(np.percentile(s, 25))),
                                p75_validation=("law_validation_score", lambda s: float(np.percentile(s, 75))),
                            )
                            .reset_index()
                        )
                        summary["validation_err"] = summary["p75_validation"] - summary["p25_validation"]
                        fig = px.scatter(
                            summary,
                            x="mean_novelty",
                            y="mean_validation",
                            size="count",
                            color="family",
                            hover_data=["count"],
                            error_y="validation_err",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown("**Family novelty-stability frontier**")
                        frontier = summary.sort_values("mean_validation", ascending=False)
                        st.dataframe(frontier)
            if "generation" in df.columns and df["generation"].notna().any():
                st.markdown("**Operator drift over generations**")
                if "law_signature" in law_df.columns:
                    exploded = law_df.dropna(subset=["law_signature"]).copy()
                    exploded["operators"] = exploded["law_signature"].apply(
                        lambda sig: list(_signature_tokens(sig))
                    )
                    exploded = exploded.explode("operators")
                    if "generation" in df.columns:
                        exploded = exploded.merge(
                            df[["regime_signature", "generation"]],
                            left_on="regime",
                            right_on="regime_signature",
                            how="left",
                        )
                        drift = (
                            exploded.dropna(subset=["generation"])
                            .groupby(["generation", "operators"])
                            .size()
                            .reset_index(name="count")
                        )
                        if not drift.empty:
                            drift_fig = px.line(
                                drift,
                                x="generation",
                                y="count",
                                color="operators",
                            )
                            st.plotly_chart(drift_fig, use_container_width=True)
                st.markdown("**Family drift over generations**")
                family_drift = law_df.dropna(subset=["law_family"]).merge(
                    df[["regime_signature", "generation"]],
                    left_on="regime",
                    right_on="regime_signature",
                    how="left",
                )
                family_drift = family_drift.dropna(subset=["generation"])
                if not family_drift.empty:
                    counts = (
                        family_drift.groupby(["generation", "law_family"])
                        .size()
                        .reset_index(name="count")
                    )
                    drift_fig = px.line(
                        counts,
                        x="generation",
                        y="count",
                        color="law_family",
                    )
                    st.plotly_chart(drift_fig, use_container_width=True)
                st.markdown("**Family validation trend**")
                if not family_drift.empty and "law_validation_score" in law_df.columns:
                    family_validation = (
                        family_drift.groupby(["generation", "law_family"])["law_validation_score"]
                        .mean()
                        .reset_index(name="mean_validation")
                    )
                    if not family_validation.empty:
                        val_fig = px.line(
                            family_validation,
                            x="generation",
                            y="mean_validation",
                            color="law_family",
                        )
                        st.plotly_chart(val_fig, use_container_width=True)
                st.markdown("**Family novelty trend**")
                if "novelty_bonus" in df.columns and not family_drift.empty:
                    family_novelty = family_drift.merge(
                        df[["regime_signature", "novelty_bonus"]],
                        on="regime_signature",
                        how="left",
                    )
                    family_novelty = family_novelty.dropna(subset=["novelty_bonus"])
                    if not family_novelty.empty:
                        novelty_stats = (
                            family_novelty.groupby(["generation", "law_family"])["novelty_bonus"]
                            .mean()
                            .reset_index(name="mean_novelty")
                        )
                        novelty_fig = px.line(
                            novelty_stats,
                            x="generation",
                            y="mean_novelty",
                            color="law_family",
                        )
                        st.plotly_chart(novelty_fig, use_container_width=True)
                st.markdown("**Validation score trend**")
                if "law_validation_score" in law_df.columns:
                    trend = law_df.merge(
                        df[["regime_signature", "generation"]],
                        left_on="regime",
                        right_on="regime_signature",
                        how="left",
                    )
                    trend = trend.dropna(subset=["generation", "law_validation_score"])
                    if not trend.empty:
                        trend_stats = (
                            trend.groupby("generation")["law_validation_score"]
                            .mean()
                            .reset_index(name="mean_validation")
                        )
                        trend_fig = px.line(
                            trend_stats,
                            x="generation",
                            y="mean_validation",
                        )
                        st.plotly_chart(trend_fig, use_container_width=True)
                st.markdown("**Novelty-stability frontier**")
                if "novelty_bonus" in df.columns and "law_validation_score" in law_df.columns:
                    frontier = law_df.merge(
                        df[["regime_signature", "generation", "novelty_bonus"]],
                        left_on="regime",
                        right_on="regime_signature",
                        how="left",
                    )
                    frontier = frontier.dropna(subset=["generation", "law_validation_score", "novelty_bonus"])
                    if not frontier.empty:
                        frontier_stats = (
                            frontier.groupby("generation")
                            .agg(
                                max_validation=("law_validation_score", "max"),
                                mean_novelty=("novelty_bonus", "mean"),
                            )
                            .reset_index()
                        )
                        frontier_fig = px.line(
                            frontier_stats,
                            x="generation",
                            y="max_validation",
                            markers=True,
                        )
                        st.plotly_chart(frontier_fig, use_container_width=True)
            if "generation" in df.columns and df["generation"].notna().any():
                st.markdown("**Discovery evolution**")
                generation_stats = (
                    df.groupby("generation")["regime_signature"]
                    .nunique()
                    .reset_index(name="unique_regimes")
                )
                st.plotly_chart(
                    px.line(generation_stats, x="generation", y="unique_regimes"),
                    use_container_width=True,
                )
            metrics = [
                "law_validation_score",
                "law_coupled_match_score",
                "score",
                "novelty_bonus",
                "cross_field_corr",
            ]
            available = [metric for metric in metrics if metric in df.columns]
            if available:
                st.markdown("**Top regimes by key metrics**")
                top = df.sort_values(available[0], ascending=False).head(15)
                st.dataframe(top.loc[:, ["universe_id", "regime_signature"] + available])
            if "law_signature" in law_df.columns and not law_df.empty:
                st.markdown("**Rare operator signatures**")
                signature_counts = law_df["law_signature"].value_counts().reset_index()
                signature_counts.columns = ["law_signature", "count"]
                rare = signature_counts.sort_values("count", ascending=True).head(10)
                st.dataframe(rare)

    with tabs[13]:
        st.subheader("Symmetry + conservation")
        symmetry_cols = [
            "translation_invariance",
            "scale_invariance",
            "phase_invariance",
            "rotation_score",
            "reflection_score",
            "so2_score",
        ]
        available = [col for col in symmetry_cols if col in df.columns]
        if not available:
            st.info("No symmetry metrics recorded in this run.")
        else:
            st.markdown("**Symmetry metric distributions**")
            for col in available:
                fig = px.histogram(df.dropna(subset=[col]), x=col, nbins=30)
                fig.update_layout(title=col)
                st.plotly_chart(fig, use_container_width=True)
            if "symmetry_group" in df.columns:
                st.markdown("**Symmetry group counts**")
                group_counts = df["symmetry_group"].value_counts().reset_index()
                group_counts.columns = ["symmetry_group", "count"]
                st.dataframe(group_counts)
            st.markdown("**Top symmetry regimes**")
            score_cols = [col for col in available if col in df.columns]
            if score_cols:
                top = df.sort_values(score_cols[0], ascending=False).head(15)
                st.dataframe(top.loc[:, ["universe_id"] + score_cols])
            if "generation" in df.columns:
                st.markdown("**Symmetry trends by generation**")
                trend = (
                    df.groupby("generation")[available]
                    .mean()
                    .reset_index()
                    .melt(id_vars="generation", var_name="metric", value_name="mean_value")
                )
                if not trend.empty:
                    fig = px.line(trend, x="generation", y="mean_value", color="metric")
                    st.plotly_chart(fig, use_container_width=True)

    with tabs[14]:
        st.subheader("Model registry")
        registry_root = Path("models")
        if not registry_root.exists():
            st.info("No model registry directory found. Train a PLL-M model to populate it.")
        else:
            runs = sorted(
                [path for path in registry_root.iterdir() if path.is_dir() and path.name.startswith("run-")],
                reverse=True,
            )
            if not runs:
                st.info("No registry runs available yet.")
            else:
                run_rows = []
                for run in runs:
                    metadata_path = run / "metadata.json"
                    config_path = run / "configs" / "train_config.json"
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
                    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
                    training = metadata.get("training", {}) if isinstance(metadata, dict) else {}
                    dataset = metadata.get("dataset", {}) if isinstance(metadata, dict) else {}
                    tags = metadata.get("tags", []) if isinstance(metadata, dict) else []
                    run_rows.append({
                        "run_id": run.name,
                        "records": dataset.get("record_count"),
                        "operator_vocab": training.get("operator_vocab"),
                        "device": training.get("device"),
                        "model_type": config.get("model_type"),
                        "model_dim": config.get("model_dim"),
                        "tags": tags,
                    })
                runs_df = pd.DataFrame(run_rows)
                search = st.text_input("Filter run id", value="")
                model_types = sorted(runs_df["model_type"].dropna().unique().tolist())
                selected_types = st.multiselect("Model types", model_types, default=model_types)
                tag_options = sorted({tag for tags in runs_df["tags"].dropna() for tag in tags})
                selected_tags = st.multiselect("Tags", tag_options, default=tag_options)
                filtered = runs_df.copy()
                if search:
                    filtered = filtered[filtered["run_id"].str.contains(search, case=False, na=False)]
                if selected_types:
                    filtered = filtered[filtered["model_type"].isin(selected_types)]
                if selected_tags:
                    filtered = filtered[filtered["tags"].apply(lambda tags: bool(set(tags or []) & set(selected_tags)))]
                if "tags" in filtered.columns:
                    filtered = filtered.copy()
                    filtered["tags"] = filtered["tags"].apply(lambda tags: ", ".join(tags) if tags else "")

                st.markdown("**Registry summary**")
                st.dataframe(filtered if not filtered.empty else runs_df)

                summary_source = filtered if not filtered.empty else runs_df
                if not summary_source.empty:
                    st.markdown("**Registry stats**")
                    if summary_source["model_type"].notna().any():
                        type_counts = summary_source["model_type"].value_counts().reset_index()
                        type_counts.columns = ["model_type", "count"]
                        st.plotly_chart(
                            px.bar(type_counts, x="model_type", y="count", title="Models by type"),
                            use_container_width=True,
                        )
                    if summary_source["device"].notna().any():
                        device_counts = summary_source["device"].value_counts().reset_index()
                        device_counts.columns = ["device", "count"]
                        st.plotly_chart(
                            px.bar(device_counts, x="device", y="count", title="Models by device"),
                            use_container_width=True,
                        )
                    if summary_source["records"].notna().any():
                        st.plotly_chart(
                            px.histogram(summary_source.dropna(subset=["records"]), x="records", nbins=20),
                            use_container_width=True,
                        )

                run_labels = (filtered["run_id"].tolist() if not filtered.empty else runs_df["run_id"].tolist())
                selected = st.selectbox("Select registry run", run_labels)
                selected_path = registry_root / selected
                metadata_path = selected_path / "metadata.json"
                config_path = selected_path / "configs" / "train_config.json"
                provenance_path = selected_path / "provenance.json"

                if metadata_path.exists():
                    metadata = pd.read_json(metadata_path)
                    if isinstance(metadata, pd.Series):
                        metadata = metadata.to_frame().T
                    st.markdown("**Run metadata**")
                    st.dataframe(metadata)
                if config_path.exists():
                    config = pd.read_json(config_path)
                    if isinstance(config, pd.Series):
                        config = config.to_frame().T
                    st.markdown("**Training config**")
                    st.dataframe(config)
                if provenance_path.exists():
                    provenance = pd.read_json(provenance_path)
                    if isinstance(provenance, pd.Series):
                        provenance = provenance.to_frame().T
                    st.markdown("**Artifacts**")
                    st.dataframe(provenance)

                artifacts_dir = selected_path / "artifacts"
                if artifacts_dir.exists():
                    cards = sorted(artifacts_dir.glob("*.md"))
                    if cards:
                        card_choice = st.selectbox("Model cards", [card.name for card in cards])
                        card_path = artifacts_dir / card_choice
                        st.markdown(card_path.read_text(encoding="utf-8"))

    with tabs[15]:
        st.subheader("Knowledge Graph")
        summary_path = run_path / "graph_summary.json"
        relations_path = run_path / "graph_relations.json"
        if not summary_path.exists() and not relations_path.exists():
            st.info("Graph artifacts not found in this run.")
        else:
            if summary_path.exists():
                summary = pd.read_json(summary_path)
                if isinstance(summary, pd.Series):
                    summary = summary.to_frame().T
                st.markdown("**Graph summary**")
                st.dataframe(summary)
            if relations_path.exists():
                relations = pd.read_json(relations_path)
                if relations.empty:
                    st.info("No graph relations recorded.")
                else:
                    st.markdown("**Relations**")
                    focus_node = "All"
                    if "subject" in relations.columns or "object" in relations.columns:
                        nodes = pd.Series(
                            pd.concat([
                                relations.get("subject", pd.Series(dtype=str)),
                                relations.get("object", pd.Series(dtype=str)),
                            ])
                        ).dropna().unique().tolist()
                        if nodes:
                            focus_node = st.selectbox(
                                "Focus node",
                                ["All"] + sorted(nodes),
                            )
                    relation_types = ["All"] + sorted(relations["relation"].dropna().unique().tolist())
                    selected_relation = st.selectbox("Filter by relation", relation_types)
                    if selected_relation != "All":
                        relations = relations[relations["relation"] == selected_relation]
                    subject_types = ["All"] + sorted(relations["subject"].dropna().unique().tolist())
                    selected_subject = st.selectbox("Filter by subject", subject_types)
                    if selected_subject != "All":
                        relations = relations[relations["subject"] == selected_subject]
                    if focus_node != "All":
                        relations = relations[
                            (relations.get("subject") == focus_node)
                            | (relations.get("object") == focus_node)
                        ]
                    if "object" in relations.columns and relations["object"].notna().any():
                        st.markdown("**Graph view**")
                        nodes_df, edges_df = _build_graph_layout(relations)
                        if not nodes_df.empty:
                            degrees = _graph_degrees(edges_df)
                            nodes_df = nodes_df.assign(
                                degree=nodes_df["node"].map(lambda node: degrees.get(str(node), 0)),
                            )
                            color_map = {
                                relation: px.colors.qualitative.Plotly[idx % len(px.colors.qualitative.Plotly)]
                                for idx, relation in enumerate(sorted(edges_df["relation"].dropna().unique()))
                            }
                            edge_traces = []
                            for relation, group in edges_df.groupby("relation"):
                                edge_x = []
                                edge_y = []
                                edge_text = []
                                if "confidence" in relations.columns:
                                    confidence_mean = float(
                                        relations.loc[relations["relation"] == relation, "confidence"]
                                        .dropna()
                                        .mean()
                                        if not relations.loc[relations["relation"] == relation, "confidence"].dropna().empty
                                        else 0.0
                                    )
                                else:
                                    confidence_mean = float(len(group))
                                line_width = 1 + min(4.0, confidence_mean * 0.5)
                                for _, edge in group.iterrows():
                                    edge_x += [edge["x0"], edge["x1"], None]
                                    edge_y += [edge["y0"], edge["y1"], None]
                                    confidence = None
                                    if "confidence" in relations.columns:
                                        confidence_match = relations.loc[
                                            (relations["subject"] == edge["subject"])
                                            & (relations["object"] == edge["object"])
                                            & (relations["relation"] == relation),
                                            "confidence",
                                        ]
                                        if not confidence_match.empty:
                                            confidence = confidence_match.iloc[0]
                                    confidence_text = f"<br>Confidence: {confidence}" if confidence is not None else ""
                                    edge_text += [
                                        f"{edge['subject']} → {edge['object']}<br>{relation}{confidence_text}",
                                        f"{edge['subject']} → {edge['object']}<br>{relation}{confidence_text}",
                                        None,
                                    ]
                                edge_traces.append(
                                    go.Scatter(
                                        x=edge_x,
                                        y=edge_y,
                                        line=dict(width=line_width, color=color_map.get(relation, "#888")),
                                        hoverinfo="text",
                                        text=edge_text,
                                        mode="lines",
                                        name=str(relation),
                                    )
                                )
                            node_sizes = 12 + nodes_df["degree"].fillna(0).astype(float) * 2
                            node_trace = go.Scatter(
                                x=nodes_df["x"],
                                y=nodes_df["y"],
                                mode="markers+text",
                                text=nodes_df["node"],
                                textposition="bottom center",
                                marker=dict(size=node_sizes, color="#3b82f6"),
                                hoverinfo="text",
                                hovertext=nodes_df.apply(
                                    lambda row: f"{row['node']}<br>Degree: {int(row['degree'])}",
                                    axis=1,
                                ),
                            )
                            fig = go.Figure(data=edge_traces + [node_trace])
                            fig.update_layout(
                                showlegend=True,
                                margin=dict(l=10, r=10, t=10, b=10),
                                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(relations)

    with tabs[16]:
        surprises = df[df["density_surprise"]].sort_values("score", ascending=False)
        if surprises.empty:
            st.success("No surprise regimes detected with current thresholds.")
        else:
            for _, row in surprises.head(5).iterrows():
                label = (
                    f"🚨 NEW PHYSICS REGIME DETECTED · Universe {row.get('universe_id')} · "
                    f"Score {row.get('score', 0):.2f} · Phase {row.get('phase', 'unknown')}"
                )
                st.warning(label)
                detail = (
                    f"Novelty {row.get('novelty_bonus', 0):.2f} · "
                    f"Density {row.get('local_density', 0):.2f} · "
                    f"Cluster prob {row.get('cluster_probability', 0):.2f} · "
                    f"Behavior prob {row.get('behavior_cluster_probability', 0):.2f} · "
                    f"Defect {row.get('defect_density', 0):.2f} · "
                    f"Terms {row.get('wave_terms', [])}"
                )
                st.caption(detail)
            st.dataframe(
                surprises.loc[:, leaderboard_cols].head(20)
                if leaderboard_cols
                else surprises.head(20)
            )
    with tabs[10]:
        if df.empty:
            st.info("No universes available for exploration.")
        else:
            st.subheader("Regime Explorer")
            selectable = df.copy()
            selectable["display"] = selectable.apply(
                lambda row: f"Universe {row['universe_id']} · {row.get('regime_signature', 'unknown')}",
                axis=1,
            )
            selection = st.selectbox(
                "Select universe",
                selectable["display"].tolist(),
            )
            selected_row = selectable[selectable["display"] == selection].iloc[0]
            universe_id = selected_row["universe_id"]
            regime_signature = selected_row.get("regime_signature", "unknown")
            family_label = selected_row.get("law_family", "unknown")
            st.caption(f"Universe {universe_id} · Regime {regime_signature} · Family {family_label}")
            if not summary_df.empty:
                summary_match = summary_df[summary_df["regime_signature"] == regime_signature]
                if not summary_match.empty:
                    descriptor = summary_match.iloc[0].get("descriptors")
                    if descriptor:
                        st.caption(f"Descriptors: {descriptor}")

            psi_field = selected_row.get("field_psi")
            phi_field = selected_row.get("field_phi")
            if psi_field is not None:
                st.pyplot(plot_field(np.array(psi_field), title="Psi field"))
            if phi_field is not None:
                st.pyplot(plot_field(np.array(phi_field), title="Phi field"))

            psi_signal = selected_row.get("temporal_signal_psi")
            phi_signal = selected_row.get("temporal_signal_phi")
            if psi_signal:
                st.pyplot(plot_temporal_signal(psi_signal, title="Psi temporal signal"))
            if phi_signal:
                st.pyplot(plot_temporal_signal(phi_signal, title="Phi temporal signal"))

            if law_results:
                regime_laws = [law for law in law_results if law.regime == str(regime_signature)]
                if regime_laws:
                    st.subheader("Inferred laws")
                    for law in regime_laws:
                        family = _family_from_signature(law.law_signature or "")
                        st.markdown(
                            f"**{law.field_name}**: {law.equation}  \
Fit {law.fit_score:.3f} · Validation {law.validation_score:.3f} · Family {family}"
                        )
                    st.subheader("Operator importance")
                    importance = operator_importance_summary(regime_laws)
                    if not importance.empty:
                        st.dataframe(importance)
                    if "law_family" in law_df.columns:
                        st.subheader("Family operator trends")
                        family_laws = [
                            law
                            for law in law_results
                            if _family_from_signature(law.law_signature or "") == family_label
                        ]
                        if family_laws:
                            fam_importance = operator_importance_summary(family_laws)
                            if not fam_importance.empty:
                                st.dataframe(fam_importance)
                if psi_field is not None and phi_field is not None:
                    psi_law = next((law for law in regime_laws if law.field_name == "psi"), None)
                    phi_law = next((law for law in regime_laws if law.field_name == "phi"), None)
                    if psi_law and phi_law:
                        if st.button("Replay coupled validation"):
                            score, _ = coupled_field_validation_score(
                                np.array(psi_field),
                                np.array(phi_field),
                                np.array(psi_law.coefficients, dtype=float),
                                np.array(phi_law.coefficients, dtype=float),
                                psi_law.terms,
                                {
                                    "psi_defect_density": selected_row.get("psi_defect_density"),
                                    "phi_defect_density": selected_row.get("phi_defect_density"),
                                    "psi_spectral_entropy": selected_row.get("psi_spectral_entropy"),
                                    "phi_spectral_entropy": selected_row.get("phi_spectral_entropy"),
                                    "psi_vortex_count": selected_row.get("psi_vortex_count"),
                                    "phi_vortex_count": selected_row.get("phi_vortex_count"),
                                    "cross_field_corr": selected_row.get("cross_field_corr"),
                                    "cross_field_temporal_corr": selected_row.get("cross_field_temporal_corr"),
                                },
                            )
                            st.success(f"Coupled validation score: {score:.3f}")
                        if st.button("Show replay fields"):
                            replay_frames = simulate_coupled_law(
                                np.array(psi_field),
                                np.array(phi_field),
                                np.array(psi_law.coefficients, dtype=float),
                                np.array(phi_law.coefficients, dtype=float),
                                psi_law.terms,
                            )
                            replay_psi = replay_frames[-1, 0]
                            replay_phi = replay_frames[-1, 1]
                            cols = st.columns(2)
                            with cols[0]:
                                st.pyplot(plot_field(replay_psi, title="Replayed Psi"))
                            with cols[1]:
                                st.pyplot(plot_field(replay_phi, title="Replayed Phi"))

    with tabs[11]:
        if df.empty:
            st.info("No universes available for comparison.")
        else:
            st.subheader("Regime Comparison")
            selectable = df.copy()
            selectable["display"] = selectable.apply(
                lambda row: f"Universe {row['universe_id']} · {row.get('regime_signature', 'unknown')}",
                axis=1,
            )
            left_choice = st.selectbox("Left universe", selectable["display"].tolist(), key="left")
            right_choice = st.selectbox("Right universe", selectable["display"].tolist(), key="right")
            left_row = selectable[selectable["display"] == left_choice].iloc[0]
            right_row = selectable[selectable["display"] == right_choice].iloc[0]
            st.caption(
                f"Left: Universe {left_row['universe_id']} · {left_row.get('regime_signature', 'unknown')}"
                f" | Right: Universe {right_row['universe_id']} · {right_row.get('regime_signature', 'unknown')}"
            )
            metrics = [
                "score",
                "defect_density",
                "psi_defect_density",
                "phi_defect_density",
                "psi_spectral_entropy",
                "phi_spectral_entropy",
                "cross_field_corr",
                "cross_field_temporal_corr",
            ]
            compare_rows = []
            for key in metrics:
                if key in left_row.index or key in right_row.index:
                    compare_rows.append({
                        "metric": key,
                        "left": left_row.get(key),
                        "right": right_row.get(key),
                    })
            if compare_rows:
                st.dataframe(pd.DataFrame(compare_rows))
            if law_results:
                left_laws = [law for law in law_results if law.regime == str(left_row.get("regime_signature"))]
                right_laws = [law for law in law_results if law.regime == str(right_row.get("regime_signature"))]
                cols = st.columns(2)
                with cols[0]:
                    st.subheader("Left laws")
                    for law in left_laws:
                        st.markdown(f"**{law.field_name}**: {law.equation}")
                with cols[1]:
                    st.subheader("Right laws")
                    for law in right_laws:
                        st.markdown(f"**{law.field_name}**: {law.equation}")
                st.subheader("Operator signature diff")
                diff_rows = []
                for field in {law.field_name for law in left_laws + right_laws}:
                    left_sig = next((law.law_signature for law in left_laws if law.field_name == field), "")
                    right_sig = next((law.law_signature for law in right_laws if law.field_name == field), "")
                    left_ops = set(filter(None, [part.strip() for part in left_sig.split("+")]))
                    right_ops = set(filter(None, [part.strip() for part in right_sig.split("+")]))
                    diff_rows.append({
                        "field": field,
                        "left_signature": left_sig,
                        "right_signature": right_sig,
                        "added_ops": ", ".join(sorted(right_ops - left_ops)),
                        "removed_ops": ", ".join(sorted(left_ops - right_ops)),
                    })
                if diff_rows:
                    st.dataframe(pd.DataFrame(diff_rows))

    if refresh:
        st.caption(f"Auto-refresh every {refresh_rate} seconds")


if __name__ == "__main__":
    main()
