"""Human-auditable explanations of how a mapping was reached."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .code import shell_semantics, sql_dialects
from .envelope import SemanticEnvelope
from .packs import PackRegistry


def explain_mapping(
    concept: str,
    source_locale: Optional[str] = None,
    target_locale: Optional[str] = None,
    target_pack_id: Optional[str] = None,
    registry: Optional[PackRegistry] = None,
) -> Dict[str, Any]:
    """Explain how a concept is expressed and mapped, with rule-level citations."""
    registry = registry or PackRegistry.load_default()
    entry = registry.concept_index().get(concept)
    if entry is None:
        return {
            "concept": concept,
            "known": False,
            "reason": "concept is not present in any loaded pack lexicon",
            "pack_versions": registry.versions(),
        }

    crosswalks = registry.crosswalk(concept)
    if target_pack_id:
        crosswalks = [item for item in crosswalks if item.get("target_pack") == target_pack_id]

    return {
        "concept": concept,
        "known": True,
        "definition": entry.definition,
        "pack": entry.pack_id,
        "pack_version": entry.pack_version,
        "ambiguous": entry.ambiguous,
        "ambiguity_note": entry.ambiguity_note,
        "surfaces": entry.surfaces,
        "source_surface": entry.surface_for(source_locale) if source_locale else None,
        "target_surface": entry.surface_for(target_locale) if target_locale else None,
        "synonyms": entry.synonyms,
        "abbreviations": entry.abbreviations,
        "crosswalks": crosswalks,
        "pack_versions": registry.versions(),
    }


def explain_code_mapping(
    construct: str,
    source_dialect: str,
    target_dialect: str,
) -> Dict[str, Any]:
    """Explain a code-dialect construct mapping and its equivalence class."""
    mapping = sql_dialects.mapping_for(construct, source_dialect, target_dialect)
    if mapping is not None:
        return {
            "construct": construct,
            "known": True,
            "rule_id": mapping.rule_id,
            "source_form": mapping.source_form,
            "target_form": mapping.target_form,
            "equivalence": mapping.equivalence,
            "note": mapping.note,
            "escalate": mapping.escalate,
        }
    entry = shell_semantics.COMMAND_MAP.get(construct)
    if entry is not None:
        return {
            "construct": construct,
            "known": True,
            "rule_id": f"shell.map.{construct}",
            "source_form": entry.get("sh"),
            "target_form": entry.get("powershell"),
            "equivalence": entry["equivalence"],
            "note": entry["note"],
            "escalate": entry["equivalence"] == "none",
            "pipeline_models": {
                source_dialect: shell_semantics.PIPELINE_MODEL.get(source_dialect),
                target_dialect: shell_semantics.PIPELINE_MODEL.get(target_dialect),
            },
        }
    return {
        "construct": construct,
        "known": False,
        "reason": f"no registered mapping for {construct} from {source_dialect} to {target_dialect}",
        "escalate": True,
    }


def explain_envelope(envelope: SemanticEnvelope) -> List[Dict[str, Any]]:
    """Flatten an envelope's transformations into an ordered audit trail."""
    return [
        {
            "step": index,
            "tool": transformation.tool,
            "at": transformation.at,
            "source": transformation.source,
            "target": transformation.target,
            "rule_ids": transformation.rule_ids,
            "pack_versions": transformation.pack_versions,
            "lossy": transformation.lossy,
            "notes": transformation.notes,
            "confidence": transformation.confidence,
        }
        for index, transformation in enumerate(envelope.provenance.transformations)
    ]
