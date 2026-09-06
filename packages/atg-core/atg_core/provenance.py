"""Provenance extraction and an in-process ledger.

Provenance is derived from the envelope itself, so it cannot drift from what
actually happened. The ledger is a pluggable store: any durable backend can be
substituted without changing the MCP contract.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .envelope import SemanticEnvelope
from .version import ATG_VERSION


def provenance_record(envelope: SemanticEnvelope, validation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Full lineage record for a transformed envelope."""
    source = envelope.source
    target = envelope.target
    source_context = source.context if source else None
    target_context = target.context if target else None

    return {
        "atg_version": ATG_VERSION,
        "message_id": envelope.message_id,
        "source": {
            "representation": (source.representation.to_dict() if source else None),
            "language": getattr(source_context, "language", None),
            "locale": getattr(source_context, "locale", None),
            "region": getattr(source_context, "region", None),
            "jurisdiction": getattr(source_context, "jurisdiction", None),
            "industry": getattr(source_context, "industry", None),
            "profession": getattr(source_context, "profession", None),
            "programming_language": getattr(source_context, "programming_language", None),
            "programming_dialect": getattr(source_context, "programming_dialect", None),
            "runtime": getattr(source_context, "runtime", None),
        },
        "target": {
            "representation": (target.representation.to_dict() if target else None),
            "language": getattr(target_context, "language", None),
            "locale": getattr(target_context, "locale", None),
            "region": getattr(target_context, "region", None),
            "jurisdiction": getattr(target_context, "jurisdiction", None),
            "programming_language": getattr(target_context, "programming_language", None),
            "programming_dialect": getattr(target_context, "programming_dialect", None),
            "runtime": getattr(target_context, "runtime", None),
        },
        "pack_versions": envelope.pack_versions(),
        "sources": [source.__dict__ for source in envelope.provenance.sources],
        "transformations": [t.__dict__ for t in envelope.provenance.transformations],
        "tools": sorted({t.tool for t in envelope.provenance.transformations}),
        "models": sorted(
            {
                note.split("model:", 1)[1].strip()
                for t in envelope.provenance.transformations
                for note in t.notes
                if note.startswith("model:")
            }
        ),
        "ambiguities": [
            {"id": u.id, "kind": u.kind, "question": u.question, "blocking": u.blocking}
            for u in envelope.unknowns
        ],
        "assumptions": [
            {"id": a.id, "statement": a.statement, "basis": a.basis, "impact": a.impact}
            for a in envelope.assumptions
        ],
        "lossy": envelope.is_lossy(),
        "confidence": envelope.confidence,
        "semantic_equivalence": envelope.semantic_equivalence,
        "roundtrip_score": envelope.roundtrip_score,
        "requires_escalation": envelope.requires_escalation,
        "validation": validation,
    }


class ProvenanceLedger:
    """Minimal in-process ledger; swap for a durable store via the same API."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}

    def record(self, envelope: SemanticEnvelope, validation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        entry = provenance_record(envelope, validation)
        self._records[envelope.message_id] = entry
        return entry

    def get(self, message_id: str) -> Optional[Dict[str, Any]]:
        return self._records.get(message_id)

    def all(self) -> List[Dict[str, Any]]:
        return list(self._records.values())

    def clear(self) -> None:
        self._records.clear()


LEDGER = ProvenanceLedger()
