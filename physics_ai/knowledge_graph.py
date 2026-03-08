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
        object: str | None = None,
        evidence: str | None = None,
    ) -> None:
        self.relations.append({
            "subject": subject,
            "relation": relation,
            "details": details,
            "object": object,
            "evidence": [evidence] if evidence else [],
            "confidence": 1 if evidence else 0,
        })

    def add_evidence(self, index: int, evidence: str) -> None:
        if 0 <= index < len(self.relations):
            self.relations[index]["evidence"].append(evidence)
            self.relations[index]["confidence"] += 1

    def nodes(self) -> List[str]:
        nodes: set[str] = set()
        for rel in self.relations:
            subject = rel.get("subject")
            if subject:
                nodes.add(str(subject))
            obj = rel.get("object")
            if obj:
                nodes.add(str(obj))
        return sorted(nodes)

    def summary_stats(self) -> Dict[str, Any]:
        relation_counts: Dict[str, int] = {}
        subject_counts: Dict[str, int] = {}
        object_counts: Dict[str, int] = {}
        evidence_total = 0
        confidence_total = 0
        for rel in self.relations:
            rel_type = str(rel.get("relation"))
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
            subject = rel.get("subject")
            if subject:
                subject_counts[str(subject)] = subject_counts.get(str(subject), 0) + 1
            obj = rel.get("object")
            if obj:
                object_counts[str(obj)] = object_counts.get(str(obj), 0) + 1
            evidence_total += len(rel.get("evidence", []))
            confidence_total += int(rel.get("confidence", 0))
        total_relations = len(self.relations)
        return {
            "nodes": len(self.nodes()),
            "relations": total_relations,
            "relation_counts": relation_counts,
            "subject_counts": subject_counts,
            "object_counts": object_counts,
            "evidence_total": evidence_total,
            "average_confidence": (confidence_total / total_relations) if total_relations else 0.0,
        }

    def summary(self) -> str:
        return "\n".join(
            f"{rel['subject']} --{rel['relation']}--> {rel.get('object') or rel['details'].get('equation', '')}"
            for rel in self.relations
        )
