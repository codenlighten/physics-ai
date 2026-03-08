from physics_ai.knowledge_graph import ConceptGraph


def test_concept_graph_summary_stats() -> None:
    graph = ConceptGraph()
    graph.add_relation(
        "frequency",
        "inverse_law",
        {"equation": "omega = c/k"},
        object="omega = c/k",
        evidence="simulation",
    )
    graph.add_relation(
        "symmetry",
        "conserves",
        {"quantity": "energy"},
        object="energy",
    )
    graph.add_evidence(1, "noether")

    stats = graph.summary_stats()
    assert stats["nodes"] == 4
    assert stats["relations"] == 2
    assert stats["relation_counts"]["inverse_law"] == 1
    assert stats["relation_counts"]["conserves"] == 1
    assert stats["subject_counts"]["frequency"] == 1
    assert stats["subject_counts"]["symmetry"] == 1
    assert stats["object_counts"]["energy"] == 1
    assert stats["evidence_total"] == 2
    assert stats["average_confidence"] == 1.0


def test_concept_graph_nodes_includes_objects() -> None:
    graph = ConceptGraph()
    graph.add_relation("geometry", "resonance", {"modes": [1, 2, 3]}, object="modes")
    assert graph.nodes() == ["geometry", "modes"]
