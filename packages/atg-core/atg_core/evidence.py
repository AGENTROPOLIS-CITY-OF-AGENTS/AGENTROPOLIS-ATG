"""Evidence packets.

Frontier reasoning should receive canonical meaning, not raw context. An
evidence packet is a bounded, provenance-carrying reduction of a large source
document: claims keep pointers back to the spans they came from, and anything
dropped is counted rather than silently discarded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .context import ContextVector
from .envelope import ProvenanceSource, Representation, SemanticEnvelope, Transformation, new_id
from .normalize import normalize
from .packs import PackRegistry
from .parse import digest, parse

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class EvidenceClaim:
    id: str
    concept: str
    statement: str
    source_span: List[int]
    pack: str = ""
    pack_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "concept": self.concept,
            "statement": self.statement,
            "source_span": self.source_span,
            "pack": self.pack,
            "pack_version": self.pack_version,
        }


@dataclass
class EvidencePacket:
    envelope: SemanticEnvelope
    claims: List[EvidenceClaim] = field(default_factory=list)
    open_questions: List[Dict[str, Any]] = field(default_factory=list)
    source_chars: int = 0
    packet_chars: int = 0
    dropped_sentences: int = 0

    @property
    def reduction_ratio(self) -> float:
        if not self.source_chars:
            return 0.0
        return round(1.0 - (self.packet_chars / self.source_chars), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atg_version": self.envelope.atg_version,
            "message_id": self.envelope.message_id,
            "intent": self.envelope.intent.act,
            "context": (self.envelope.source.context.to_dict() if self.envelope.source else {}),
            "claims": [claim.to_dict() for claim in self.claims],
            "constraints": [
                {"kind": c.kind, "expression": c.expression, "origin": c.origin}
                for c in self.envelope.constraints
            ],
            "open_questions": self.open_questions,
            "pack_versions": self.envelope.pack_versions(),
            "confidence": self.envelope.confidence,
            "requires_escalation": self.envelope.requires_escalation,
            "reduction": {
                "source_chars": self.source_chars,
                "packet_chars": self.packet_chars,
                "ratio": self.reduction_ratio,
                "dropped_sentences": self.dropped_sentences,
            },
            "provenance": {
                "sources": [s.__dict__ for s in self.envelope.provenance.sources],
                "transformations": [t.__dict__ for t in self.envelope.provenance.transformations],
            },
        }


def build_evidence_packet(
    content: str,
    context: Optional[ContextVector] = None,
    registry: Optional[PackRegistry] = None,
    pack_ids: Optional[Sequence[str]] = None,
    max_claims: int = 24,
) -> EvidencePacket:
    """Reduce a large raw document to a canonical ATG evidence packet."""
    registry = registry or PackRegistry.load_default()
    representation = Representation(kind="human_text", name="document", version="1")
    envelope = normalize(
        parse(content, representation, context, registry=registry, pack_ids=pack_ids),
        registry=registry,
    )
    envelope.rendered = None

    sentences = [s.strip() for s in _SENTENCE_RE.split(content) if s.strip()]
    lowered = [s.lower() for s in sentences]
    claims: List[EvidenceClaim] = []
    used_sentences = set()

    for entity in envelope.entities:
        if entity.type == "authority" or len(claims) >= max_claims:
            continue
        surface = (entity.surface or "").lower()
        index = next((i for i, text in enumerate(lowered) if surface and surface in text), None)
        if index is None:
            continue
        used_sentences.add(index)
        start = content.lower().find(sentences[index].lower())
        claims.append(
            EvidenceClaim(
                id=new_id("clm"),
                concept=entity.concept,
                statement=sentences[index],
                source_span=[start, start + len(sentences[index])],
                pack=str(entity.attributes.get("pack", "")),
                pack_version=str(entity.attributes.get("pack_version", "")),
            )
        )

    packet_chars = sum(len(claim.statement) for claim in claims)
    envelope.add_source(
        ProvenanceSource(
            id=new_id("src"),
            kind="document",
            reference="evidence_packet.input",
            version="1",
            digest=digest(content),
        )
    )
    envelope.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.evidence.reduce",
            source="human_text/document",
            target="atg.evidence_packet",
            rule_ids=["atg.evidence.v1"],
            pack_versions=registry.versions(),
            lossy=True,
            notes=[f"reduced {len(content)} chars to {packet_chars} chars across {len(claims)} claims"],
            confidence=envelope.confidence,
        )
    )
    return EvidencePacket(
        envelope=envelope,
        claims=claims,
        open_questions=[
            {"id": u.id, "question": u.question, "blocking": u.blocking, "candidates": u.candidates}
            for u in envelope.unknowns
        ],
        source_chars=len(content),
        packet_chars=packet_chars,
        dropped_sentences=len(sentences) - len(used_sentences),
    )
