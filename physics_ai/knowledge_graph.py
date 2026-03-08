"""Tiny in-memory concept graph with evidence tracking."""

from __future__ import annotations

from typing import Dict, List, Any


class ConceptGraph:
    def __init__(self) -> None:
        self.relations: List[Dict[str, Any]] = []

    def add_relation(
        self,
        subject: str,
        relation: str,
        details: Dict[str, Any],
        evidence: str | None = None,
    ) -> None:
        self.relations.append({
            "subject": subject,
            "relation": relation,
            "details": details,
            "evidence": [evidence] if evidence else [],
            "confidence": 1 if evidence else 0,
        })

    def add_evidence(self, index: int, evidence: str) -> None:
        if 0 <= index < len(self.relations):
            self.relations[index]["evidence"].append(evidence)
            self.relations[index]["confidence"] += 1

    def summary(self) -> str:
        return "\n".join(
            f"{rel['subject']} --{rel['relation']}--> {rel['details'].get('equation', '')}"
            for rel in self.relations
        )
