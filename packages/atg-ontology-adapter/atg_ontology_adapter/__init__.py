"""Ontology adapter interface.

ATG owns canonical meaning; the ontology owns relations between meanings. This
is the seam between them: a protocol plus an in-memory implementation backed by
the pack registry, so ATG never depends on a particular ontology store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Protocol, runtime_checkable

from atg_core import PackRegistry, SemanticEnvelope

ADAPTER_VERSION = "0.1.0"


@dataclass
class ConceptNode:
    concept: str
    definition: str = ""
    pack: str = ""
    pack_version: str = ""
    types: List[str] = field(default_factory=list)


@dataclass
class ConceptEdge:
    type: str
    source: str
    target: str
    pack: str = ""
    pack_version: str = ""


@runtime_checkable
class OntologyAdapter(Protocol):
    """Any ontology backend implementing this protocol can serve ATG."""

    def get_concept(self, concept: str) -> Optional[ConceptNode]:
        ...

    def neighbors(self, concept: str, edge_types: Optional[Iterable[str]] = None) -> List[ConceptEdge]:
        ...

    def relate(self, envelope: SemanticEnvelope) -> List[ConceptEdge]:
        ...

    def describe(self) -> Dict[str, Any]:
        ...


class PackOntologyAdapter:
    """Default adapter: derives the ontology graph from loaded domain packs."""

    def __init__(self, registry: Optional[PackRegistry] = None) -> None:
        self._registry = registry or PackRegistry.load_default()

    def get_concept(self, concept: str) -> Optional[ConceptNode]:
        entry = self._registry.concept_index().get(concept)
        if entry is None:
            return None
        return ConceptNode(
            concept=entry.concept,
            definition=entry.definition,
            pack=entry.pack_id,
            pack_version=entry.pack_version,
            types=[entry.type],
        )

    def _edges(self) -> List[ConceptEdge]:
        edges: List[ConceptEdge] = []
        for pack in self._registry.select():
            for relationship in pack.data.get("relationships") or []:
                edges.append(
                    ConceptEdge(
                        type=relationship["type"],
                        source=relationship["source"],
                        target=relationship["target"],
                        pack=pack.pack_id,
                        pack_version=pack.version,
                    )
                )
        return edges

    def neighbors(self, concept: str, edge_types: Optional[Iterable[str]] = None) -> List[ConceptEdge]:
        wanted = set(edge_types) if edge_types else None
        return [
            edge
            for edge in self._edges()
            if concept in (edge.source, edge.target) and (wanted is None or edge.type in wanted)
        ]

    def relate(self, envelope: SemanticEnvelope) -> List[ConceptEdge]:
        concepts = {entity.concept for entity in envelope.entities}
        return [edge for edge in self._edges() if edge.source in concepts and edge.target in concepts]

    def describe(self) -> Dict[str, Any]:
        return {
            "adapter": "pack_ontology",
            "version": ADAPTER_VERSION,
            "pack_versions": self._registry.versions(),
            "concepts": len(self._registry.concept_index()),
            "edges": len(self._edges()),
        }


__all__ = [
    "ADAPTER_VERSION",
    "ConceptEdge",
    "ConceptNode",
    "OntologyAdapter",
    "PackOntologyAdapter",
]
