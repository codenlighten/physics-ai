from physics_ai.neural_symbolic import (
    EQUATION_TEMPLATES,
    append_discovery_log,
    build_training_dataset,
    load_discovery_log,
    load_proposal_network,
    save_proposal_network,
    template_subset,
)


def test_template_subset() -> None:
    subset = template_subset([0, 2, 5])
    assert subset == [EQUATION_TEMPLATES[0], EQUATION_TEMPLATES[2], EQUATION_TEMPLATES[5]]


def test_discovery_log_roundtrip(tmp_path) -> None:
    log_path = tmp_path / "discovery.jsonl"
    append_discovery_log(str(log_path), [1.0, 2.0], EQUATION_TEMPLATES[1], 0.01)
    append_discovery_log(str(log_path), [3.0, 4.0], "unknown", 0.02)

    entries = load_discovery_log(str(log_path))
    assert len(entries) == 2

    features, labels = build_training_dataset(entries)
    assert features == [[1.0, 2.0]]
    assert labels == [1]


def test_proposal_persistence(tmp_path) -> None:
    torch = __import__("pytest").importorskip("torch")
    from physics_ai.neural_symbolic import ProposalConfig, build_proposal_network

    model = build_proposal_network(ProposalConfig(input_dim=2, hidden=4))
    for param in model.parameters():
        torch.nn.init.constant_(param, 0.5)

    path = tmp_path / "proposal.pt"
    save_proposal_network(model, str(path))

    new_model = build_proposal_network(ProposalConfig(input_dim=2, hidden=4))
    load_proposal_network(new_model, str(path))

    for p1, p2 in zip(model.parameters(), new_model.parameters()):
        assert torch.allclose(p1, p2)
