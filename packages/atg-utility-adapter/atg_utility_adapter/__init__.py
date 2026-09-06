"""Utility Grid adapter interface.

The Utility Grid answers "what tools, resources and compute are available, and
under what governance". ATG only needs a capability query and a governance
check, so the interface stays small and vendor-neutral.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from atg_core import ContextVector, SemanticEnvelope, resolve_context

ADAPTER_VERSION = "0.1.0"


@dataclass
class Capability:
    id: str
    kind: str  # tool | model | compute | data
    name: str
    regions: List[str] = field(default_factory=list)
    data_residency: str = "unspecified"
    certifications: List[str] = field(default_factory=list)
    cost_unit: str = "unspecified"
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityDecision:
    allowed: List[Capability]
    denied: List[Dict[str, Any]] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": [capability.__dict__ for capability in self.allowed],
            "denied": self.denied,
            "reason": self.reason,
        }


@runtime_checkable
class UtilityGridAdapter(Protocol):
    def list_capabilities(self, kind: Optional[str] = None) -> List[Capability]:
        ...

    def select(
        self, envelope: SemanticEnvelope, context: ContextVector, kind: Optional[str] = None
    ) -> CapabilityDecision:
        ...

    def describe(self) -> Dict[str, Any]:
        ...


class StaticUtilityGridAdapter:
    """Reference implementation over a static capability catalogue.

    Region and residency are enforced here rather than assumed: a capability
    that cannot legally run in the resolved region is denied with a reason.
    """

    def __init__(self, capabilities: Optional[List[Capability]] = None) -> None:
        self._capabilities = capabilities or []

    def list_capabilities(self, kind: Optional[str] = None) -> List[Capability]:
        return [c for c in self._capabilities if kind is None or c.kind == kind]

    def select(
        self,
        envelope: SemanticEnvelope,
        context: ContextVector,
        kind: Optional[str] = None,
    ) -> CapabilityDecision:
        resolution = resolve_context(context)
        profile = resolution.execution_profile
        region = resolution.context.region
        residency = str(profile.get("data_residency", "unspecified")).lower()
        restricted = set(profile.get("restricted_services") or [])

        allowed: List[Capability] = []
        denied: List[Dict[str, Any]] = []
        for capability in self.list_capabilities(kind):
            if capability.name in restricted or capability.id in restricted:
                denied.append({"id": capability.id, "reason": f"restricted in region {region}"})
                continue
            if capability.regions and region and region not in capability.regions:
                denied.append({"id": capability.id, "reason": f"not available in region {region}"})
                continue
            if (
                residency not in ("unspecified", "")
                and capability.data_residency.lower() not in ("unspecified", "", residency)
            ):
                denied.append(
                    {
                        "id": capability.id,
                        "reason": f"data residency {capability.data_residency} conflicts with {residency}",
                    }
                )
                continue
            allowed.append(capability)

        return CapabilityDecision(
            allowed=allowed,
            denied=denied,
            reason=(
                "escalation required before execution"
                if envelope.requires_escalation
                else "capabilities filtered by resolved execution context"
            ),
        )

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": "static_utility_grid",
            "version": ADAPTER_VERSION,
            "capabilities": len(self._capabilities),
        }


__all__ = [
    "ADAPTER_VERSION",
    "Capability",
    "CapabilityDecision",
    "StaticUtilityGridAdapter",
    "UtilityGridAdapter",
]
