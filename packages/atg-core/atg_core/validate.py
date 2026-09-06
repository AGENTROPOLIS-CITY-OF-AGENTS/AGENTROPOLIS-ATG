"""Deterministic validation of semantic preservation.

SOURCE -> canonical ATG -> TARGET -> reverse ATG -> compare. The comparison is
rule based and reproducible; it fails closed on material drift instead of
reporting a fluent-looking translation as correct.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .envelope import Contract, SemanticEnvelope, contract_signature
from .escalation import MATERIAL_EQUIVALENCE_THRESHOLD

#: Types that are the same behavioural class across dialects. The widening
#: itself is still recorded as a visible, non-material drift entry.
NUMERIC_TYPES = {"integer", "number", "float", "double", "int"}

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _snake(identifier: str) -> str:
    return _CAMEL_RE.sub("_", identifier).lower()


def _canonical_type(type_name: Optional[str]) -> str:
    name = (type_name or "unknown").strip()
    base = name[5:-1] if name.startswith("list<") and name.endswith(">") else name
    canonical = "numeric" if base in NUMERIC_TYPES else base
    return f"list<{canonical}>" if base != name else canonical


def canonical_contract_signature(contract: Contract) -> str:
    """Dialect-free contract signature: identifier casing and numeric width folded."""
    params = ",".join(
        f"{_snake(str(p.get('name')))}:{_canonical_type(p.get('type'))}"
        for p in contract.signature.get("params", [])
    )
    returns = _canonical_type(contract.signature.get("returns", "void"))
    errors = ",".join(sorted(contract.errors))
    return f"{contract.kind}:{_snake(contract.name)}({params})->{returns}!{errors}"


def canonical_behavior_signature(contract: Contract) -> Optional[str]:
    signature = contract.behavior.get("signature")
    if not signature:
        return None
    return re.sub(r"[A-Za-z_][A-Za-z0-9_]*", lambda m: _snake(m.group(0)), signature)


MATERIAL_KINDS = {
    "intent_changed",
    "contract_lost",
    "contract_changed",
    "error_surface_changed",
    "authority_lost",
    "jurisdiction_lost",
    "behavior_changed",
}


@dataclass
class Drift:
    kind: str
    detail: str
    material: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "detail": self.detail, "material": self.material}


@dataclass
class ValidationResult:
    passed: bool
    semantic_equivalence: float
    confidence: float
    drift: List[Drift] = field(default_factory=list)
    ambiguities: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    requires_escalation: bool = False

    @property
    def material_drift(self) -> List[Drift]:
        return [item for item in self.drift if item.material]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "semantic_equivalence": self.semantic_equivalence,
            "confidence": self.confidence,
            "drift": [item.to_dict() for item in self.drift],
            "ambiguities": self.ambiguities,
            "conflicts": self.conflicts,
            "requires_escalation": self.requires_escalation,
            "threshold": MATERIAL_EQUIVALENCE_THRESHOLD,
        }


def _concepts(envelope: SemanticEnvelope, include_authorities: bool = False) -> Set[str]:
    return {
        entity.concept
        for entity in envelope.entities
        if include_authorities or entity.type != "authority"
    }


def _authorities(envelope: SemanticEnvelope) -> Set[str]:
    return {entity.concept for entity in envelope.entities if entity.type == "authority"}


def _jaccard(left: Set[str], right: Set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def validate(source: SemanticEnvelope, reverse: SemanticEnvelope) -> ValidationResult:
    drift: List[Drift] = []

    if source.intent.act != reverse.intent.act:
        drift.append(
            Drift("intent_changed", f"{source.intent.act} -> {reverse.intent.act}", material=True)
        )

    source_concepts, reverse_concepts = _concepts(source), _concepts(reverse)
    lost = sorted(source_concepts - reverse_concepts)
    added = sorted(reverse_concepts - source_concepts)
    if lost:
        drift.append(Drift("concept_lost", ", ".join(lost)))
    if added:
        drift.append(Drift("concept_added", ", ".join(added)))

    source_contracts = {_snake(c.name): c for c in source.contracts}
    reverse_contracts = {_snake(c.name): c for c in reverse.contracts}
    for name, contract in source_contracts.items():
        counterpart = reverse_contracts.get(name)
        if counterpart is None:
            drift.append(Drift("contract_lost", name, material=True))
            continue
        if canonical_contract_signature(contract) != canonical_contract_signature(counterpart):
            drift.append(
                Drift(
                    "contract_changed",
                    f"{canonical_contract_signature(contract)} != {canonical_contract_signature(counterpart)}",
                    material=True,
                )
            )
        elif contract_signature(contract) != contract_signature(counterpart):
            drift.append(
                Drift(
                    "representation_widening",
                    f"{contract_signature(contract)} ~= {contract_signature(counterpart)}",
                )
            )
        if set(contract.errors) != set(counterpart.errors):
            drift.append(
                Drift(
                    "error_surface_changed",
                    f"{sorted(contract.errors)} != {sorted(counterpart.errors)}",
                    material=True,
                )
            )
        source_behavior = canonical_behavior_signature(contract)
        reverse_behavior = canonical_behavior_signature(counterpart)
        if source_behavior and reverse_behavior and source_behavior != reverse_behavior:
            drift.append(
                Drift("behavior_changed", f"{source_behavior} != {reverse_behavior}", material=True)
            )

    lost_authorities = sorted(_authorities(source) - _authorities(reverse))
    if lost_authorities:
        drift.append(Drift("authority_lost", ", ".join(lost_authorities), material=True))

    source_jurisdiction = source.source.context.jurisdiction if source.source else None
    reverse_context = (reverse.target or reverse.source).context if (reverse.target or reverse.source) else None
    reverse_jurisdiction = reverse_context.jurisdiction if reverse_context else None
    if source_jurisdiction and not reverse_jurisdiction:
        drift.append(Drift("jurisdiction_lost", str(source_jurisdiction), material=True))

    concept_score = _jaccard(source_concepts, reverse_concepts)
    if source_contracts or reverse_contracts:
        contract_score = _jaccard(
            {canonical_contract_signature(c) for c in source.contracts},
            {canonical_contract_signature(c) for c in reverse.contracts},
        )
        behavior_pairs = [
            (
                canonical_behavior_signature(source_contracts[name]),
                canonical_behavior_signature(reverse_contracts[name]),
            )
            for name in source_contracts
            if name in reverse_contracts
        ]
        behavior_score = (
            sum(1.0 for left, right in behavior_pairs if left == right) / len(behavior_pairs)
            if behavior_pairs
            else (0.0 if source_contracts else 1.0)
        )
        intent_score = 1.0 if source.intent.act == reverse.intent.act else 0.0
        equivalence = 0.2 * intent_score + 0.2 * concept_score + 0.3 * contract_score + 0.3 * behavior_score
    else:
        intent_score = 1.0 if source.intent.act == reverse.intent.act else 0.0
        equivalence = 0.4 * intent_score + 0.6 * concept_score

    ambiguities = [
        unknown.to_dict() if hasattr(unknown, "to_dict") else vars(unknown)
        for unknown in list(source.unknowns) + list(reverse.unknowns)
        if unknown.kind == "ambiguity"
    ]
    conflicts = [item.to_dict() for item in drift if item.material]

    equivalence = round(max(0.0, min(1.0, equivalence)), 3)
    material = bool(conflicts)
    blocking_unknowns = any(u.blocking for u in list(source.unknowns) + list(reverse.unknowns))
    passed = equivalence >= MATERIAL_EQUIVALENCE_THRESHOLD and not material and not blocking_unknowns

    return ValidationResult(
        passed=passed,
        semantic_equivalence=equivalence,
        confidence=round(min(source.confidence, reverse.confidence), 3),
        drift=drift,
        ambiguities=ambiguities,
        conflicts=conflicts,
        requires_escalation=not passed,
    )


def apply_validation(
    envelope: SemanticEnvelope, result: ValidationResult, roundtrip_score: Optional[float] = None
) -> SemanticEnvelope:
    envelope.semantic_equivalence = result.semantic_equivalence
    envelope.roundtrip_score = roundtrip_score
    envelope.confidence = min(envelope.confidence, result.confidence)
    if result.requires_escalation:
        envelope.requires_escalation = True
    return envelope
