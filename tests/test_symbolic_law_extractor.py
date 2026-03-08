import numpy as np
import pandas as pd

from physics_ai.symbolic_law_extractor import extract_symbolic_laws, operator_importance_summary


def test_extract_symbolic_laws_returns_equation() -> None:
    t = np.linspace(0, 2 * np.pi, 50)
    signal = np.sin(t)
    df = pd.DataFrame(
        {
            "regime_signature": ["test"],
            "temporal_signal": [signal.tolist()],
            "field": [np.array([[0.1, 0.2], [0.3, 0.4]])],
        }
    )
    laws = extract_symbolic_laws(df, max_per_regime=1, alpha=0.001)
    assert laws
    assert "dpsi/dt" in laws[0].equation
    assert laws[0].field_name == "psi"
    assert -1.0 <= laws[0].validation_score <= 1.0
    assert 0.0 <= laws[0].regime_match_score <= 1.0
    assert laws[0].coupled_match_score == 0.0
    summary = operator_importance_summary(laws)
    assert not summary.empty


def test_extract_symbolic_laws_multifield() -> None:
    t = np.linspace(0, 2 * np.pi, 60)
    psi_signal = np.sin(t)
    phi_signal = np.cos(t)
    df = pd.DataFrame(
        {
            "regime_signature": ["multi"],
            "temporal_signal_psi": [psi_signal.tolist()],
            "temporal_signal_phi": [phi_signal.tolist()],
            "field_psi": [np.array([[0.1, 0.2], [0.3, 0.4]])],
            "field_phi": [np.array([[0.2, 0.1], [0.0, -0.1]])],
            "psi_defect_density": [0.01],
            "phi_defect_density": [0.02],
        }
    )
    laws = extract_symbolic_laws(df, max_per_regime=1, alpha=0.001)
    fields = {law.field_name for law in laws}
    assert fields == {"psi", "phi"}
    coupled_scores = {law.coupled_match_score for law in laws}
    assert len(coupled_scores) == 1
