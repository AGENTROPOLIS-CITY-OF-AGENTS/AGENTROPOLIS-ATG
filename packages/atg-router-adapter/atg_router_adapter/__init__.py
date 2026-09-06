"""Intelligence Router adapter interface.

The router answers "who should reason about this". ATG supplies the evidence:
domain, jurisdiction, escalation state, confidence and the size of the reduced
evidence packet. Routing policy stays outside ATG and outside any vendor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from atg_core import SemanticEnvelope

ADAPTER_VERSION = "0.1.0"


@dataclass
class ReasoningRequest:
    envelope: SemanticEnvelope
    task: str = "reason"
    max_tokens: Optional[int] = None
    requires_determinism: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def signals(self) -> Dict[str, Any]:
        source_context = self.envelope.source.context if self.envelope.source else None
        return {
            "task": self.task,
            "intent": self.envelope.intent.act,
            "industry": getattr(source_context, "industry", None),
            "jurisdiction": getattr(source_context, "jurisdiction", None),
            "region": getattr(source_context, "region", None),
            "programming_language": getattr(source_context, "programming_language", None),
            "confidence": self.envelope.confidence,
            "requires_escalation": self.envelope.requires_escalation,
            "blocking_unknowns": [u.id for u in self.envelope.unknowns if u.blocking],
            "lossy": self.envelope.is_lossy(),
            "pack_versions": self.envelope.pack_versions(),
            "requires_determinism": self.requires_determinism,
        }


@dataclass
class RoutingDecision:
    tier: str  # deterministic | local | frontier | human
    rationale: str
    signals: Dict[str, Any] = field(default_factory=dict)
    candidates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "rationale": self.rationale,
            "signals": self.signals,
            "candidates": self.candidates,
        }


@runtime_checkable
class IntelligenceRouterAdapter(Protocol):
    def route(self, request: ReasoningRequest) -> RoutingDecision:
        ...

    def describe(self) -> Dict[str, Any]:
        ...


class PolicyRouterAdapter:
    """Reference router: deterministic first, human on blocking escalation.

    Tiers are names, not vendors. Binding a tier to a concrete provider is the
    deployment's responsibility.
    """

    def __init__(self, low_confidence: float = 0.7, tier_candidates: Optional[Dict[str, List[str]]] = None) -> None:
        self.low_confidence = low_confidence
        self.tier_candidates = tier_candidates or {}

    def route(self, request: ReasoningRequest) -> RoutingDecision:
        signals = request.signals
        if signals["requires_escalation"]:
            tier, rationale = "human", "blocking unknowns require adjudication before reasoning"
        elif request.requires_determinism:
            tier, rationale = "deterministic", "caller requires a deterministic transform"
        elif signals["industry"] in ("TAX", "LEGAL", "REAL_ESTATE"):
            tier, rationale = "frontier", "high-impact domain with jurisdictional consequences"
        elif signals["confidence"] < self.low_confidence:
            tier, rationale = "frontier", f"confidence {signals['confidence']} below {self.low_confidence}"
        else:
            tier, rationale = "local", "well-formed canonical envelope with high confidence"
        return RoutingDecision(
            tier=tier,
            rationale=rationale,
            signals=signals,
            candidates=self.tier_candidates.get(tier, []),
        )

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": "policy_router",
            "version": ADAPTER_VERSION,
            "tiers": ["deterministic", "local", "frontier", "human"],
            "low_confidence": self.low_confidence,
        }


__all__ = [
    "ADAPTER_VERSION",
    "IntelligenceRouterAdapter",
    "PolicyRouterAdapter",
    "ReasoningRequest",
    "RoutingDecision",
]
