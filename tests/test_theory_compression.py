from physics_ai.theory_compression import TheoryCandidate, rank_theories


def test_rank_theories_prefers_lower_score() -> None:
    candidates = [
        TheoryCandidate(name="a", equation="x", error=0.2),
        TheoryCandidate(name="b", equation="x + y", error=0.1),
    ]
    scores = rank_theories(candidates, complexity_weight=0.0)
    assert scores[0].name == "b"
