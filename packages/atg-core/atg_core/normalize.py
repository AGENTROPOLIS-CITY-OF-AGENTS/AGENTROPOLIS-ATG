"""Canonicalisation of a parsed envelope.

Normalisation removes dialect and surface variation so that two inputs meaning
the same thing produce the same canonical signature, without discarding the
locale information needed to render output correctly later.
"""

from __future__ import annotations

from typing import Optional

from .envelope import SemanticEnvelope, Transformation, new_id
from .packs import PackRegistry

CANONICAL_UNITS = {
    "us-customary": {"length": "foot", "area": "square_foot", "mass": "pound"},
    "metric": {"length": "metre", "area": "square_metre", "mass": "kilogram"},
}


def normalize(envelope: SemanticEnvelope, registry: Optional[PackRegistry] = None) -> SemanticEnvelope:
    registry = registry or PackRegistry.load_default()
    concept_index = registry.concept_index()

    for entity in envelope.entities:
        entry = concept_index.get(entity.concept)
        if entry is None:
            continue
        entity.attributes.setdefault("canonical_definition", entry.definition)
        entity.attributes["surface_locales"] = sorted(entry.surfaces)
        entity.attributes.setdefault("pack", entry.pack_id)
        entity.attributes.setdefault("pack_version", entry.pack_version)

    envelope.entities.sort(key=lambda e: e.concept)
    envelope.relations.sort(key=lambda r: (r.type, r.source, r.target))
    envelope.constraints.sort(key=lambda c: (c.kind, c.expression))
    envelope.contracts.sort(key=lambda c: (c.kind, c.name))

    source_context = envelope.source.context if envelope.source else None
    if source_context and source_context.units in CANONICAL_UNITS:
        envelope.intent.arguments.setdefault("unit_system", source_context.units)

    envelope.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.normalize",
            source="atg.canonical",
            target="atg.canonical.normalized",
            rule_ids=["atg.normalize.v1"],
            pack_versions=registry.versions(),
            confidence=envelope.confidence,
        )
    )
    return envelope
