"""SOURCE -> ATG -> TARGET -> reverse ATG -> compare."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

from .context import ContextVector
from .envelope import Representation, SemanticEnvelope, Transformation, new_id
from .escalation import escalate_for_equivalence
from .normalize import normalize
from .packs import PackRegistry
from .parse import parse
from .translate import translate_code, translate_human
from .validate import ValidationResult, apply_validation, validate


@dataclass
class RoundtripResult:
    source_envelope: SemanticEnvelope
    target_envelope: SemanticEnvelope
    reverse_envelope: SemanticEnvelope
    rendered: str
    validation: ValidationResult
    roundtrip_score: float = 0.0
    notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.validation.passed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rendered": self.rendered,
            "roundtrip_score": self.roundtrip_score,
            "passed": self.passed,
            "validation": self.validation.to_dict(),
            "source_envelope": self.source_envelope.to_dict(),
            "target_envelope": self.target_envelope.to_dict(),
            "reverse_envelope": self.reverse_envelope.to_dict(),
            "notes": self.notes,
        }


def roundtrip(
    content: str,
    source: Representation,
    target: Representation,
    source_context: Optional[ContextVector] = None,
    target_context: Optional[ContextVector] = None,
    registry: Optional[PackRegistry] = None,
    pack_ids: Optional[Sequence[str]] = None,
) -> RoundtripResult:
    registry = registry or PackRegistry.load_default()
    source_context = source_context or ContextVector()
    target_context = target_context or source_context

    forward = normalize(
        parse(content, source, source_context, registry=registry, pack_ids=pack_ids),
        registry=registry,
    )

    if target.kind == "code":
        rendered, target_envelope = translate_code(forward, target, registry=registry)
    elif target.kind == "human_text":
        target_envelope = translate_human(forward, target_context, registry=registry)
        rendered = target_envelope.rendered or ""
    else:
        raise ValueError(f"roundtrip does not support target kind '{target.kind}'")

    reverse_context = (target_envelope.target.context if target_envelope.target else target_context)
    if rendered:
        reverse = normalize(
            parse(rendered, target, reverse_context, registry=registry, pack_ids=pack_ids),
            registry=registry,
        )
    else:
        reverse = SemanticEnvelope(source=target_envelope.target)
        reverse.confidence = 0.0

    result = validate(forward, reverse)
    score = round(
        result.semantic_equivalence * (0.5 if not rendered else 1.0),
        3,
    )
    apply_validation(target_envelope, result, roundtrip_score=score)
    escalate_for_equivalence(
        target_envelope,
        result.semantic_equivalence,
        [item.detail for item in result.material_drift],
    )
    target_envelope.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.roundtrip",
            source=source.label(),
            target=target.label(),
            rule_ids=["atg.roundtrip.v1"],
            pack_versions=registry.versions(),
            lossy=not result.passed,
            notes=[f"{item.kind}: {item.detail}" for item in result.drift],
            confidence=result.confidence,
        )
    )
    return RoundtripResult(
        source_envelope=forward,
        target_envelope=target_envelope,
        reverse_envelope=reverse,
        rendered=rendered,
        validation=result,
        roundtrip_score=score,
    )
