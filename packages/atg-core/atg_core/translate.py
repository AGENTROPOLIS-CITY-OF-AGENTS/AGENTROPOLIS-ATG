"""Canonical ATG -> TARGET rendering for human, domain and code targets."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .code import ir as code_ir
from .code import python_adapter, shell_semantics, sql_dialects, typescript_adapter
from .code.registry import resolve_language
from .context import ContextVector, resolve_context
from .envelope import (
    Assumption,
    Constraint,
    Endpoint,
    Entity,
    Representation,
    SemanticEnvelope,
    Transformation,
    Unknown,
    new_id,
)
from .packs import PackRegistry

ACT_TEMPLATES = {
    "en": {
        "schedule": "Schedule",
        "acquire": "Acquire",
        "dispose": "Dispose of",
        "file": "File",
        "report": "Report",
        "compute": "Compute",
        "deploy": "Deploy",
        "rollback": "Roll back",
        "review": "Review",
        "send": "Send",
        "translate": "Translate",
        "store": "Store",
        "process": "Process",
        "state": "State",
    },
    "es": {"schedule": "Programar", "send": "Enviar", "state": "Declarar"},
    "de": {"schedule": "Planen", "send": "Senden", "state": "Feststellen"},
}


def translate_human(
    envelope: SemanticEnvelope,
    target_context: ContextVector,
    registry: Optional[PackRegistry] = None,
) -> SemanticEnvelope:
    """Render the canonical envelope into the target locale's surfaces."""
    registry = registry or PackRegistry.load_default()
    concept_index = registry.concept_index()
    resolution = resolve_context(target_context)
    resolved = resolution.context

    out = copy.deepcopy(envelope)
    for assumption in resolution.assumptions:
        out.add_assumption(Assumption(**assumption))
    for unknown in resolution.unknowns:
        out.add_unknown(Unknown(**unknown))

    surfaces: List[str] = []
    unrenderable: List[str] = []
    for entity in out.entities:
        if entity.type == "authority":
            continue
        entry = concept_index.get(entity.concept)
        surface = entry.surface_for(resolved.locale, resolved.language) if entry else None
        if surface is None:
            unrenderable.append(entity.concept)
            surface = entity.concept
        surfaces.append(surface)

    verb = ACT_TEMPLATES.get(resolved.language or "en", ACT_TEMPLATES["en"]).get(
        out.intent.act, out.intent.act
    )
    out.rendered = f"{verb}: " + ", ".join(surfaces) if surfaces else verb
    out.target = Endpoint(
        representation=Representation(
            kind="human_text", name="natural_language", version="1", dialect=resolved.locale or ""
        ),
        context=resolved,
    )

    for concept in unrenderable:
        out.add_unknown(
            Unknown(
                id=f"translate.human.no_surface.{concept}",
                question=f"No surface form registered for '{concept}' in locale '{resolved.locale}'.",
                kind="missing_surface",
                blocking=False,
            )
        )

    out.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.translate.human",
            source="atg.canonical",
            target=f"human_text/{resolved.locale}",
            rule_ids=["common.tr.locale_surface"],
            pack_versions=registry.versions(),
            lossy=bool(unrenderable),
            notes=[f"no surface for {c}" for c in unrenderable],
            confidence=round(max(0.0, out.confidence - 0.05 * len(unrenderable)), 3),
        )
    )
    return out


def translate_domain(
    envelope: SemanticEnvelope,
    target_pack_id: str,
    registry: Optional[PackRegistry] = None,
) -> SemanticEnvelope:
    """Re-frame concepts into another domain pack through declared crosswalks."""
    registry = registry or PackRegistry.load_default()
    out = copy.deepcopy(envelope)
    target_pack = registry.get(target_pack_id)
    if target_pack is None:
        out.add_unknown(
            Unknown(
                id="translate.domain.unknown_pack",
                question=f"Domain pack '{target_pack_id}' is not registered.",
                kind="unknown_pack",
                blocking=True,
            )
        )
        return out

    rule_ids: List[str] = []
    notes: List[str] = []
    lossy = False
    for entity in out.entities:
        if entity.type == "authority":
            continue
        mappings = [m for m in registry.crosswalk(entity.concept) if m.get("target_pack") == target_pack_id]
        if not mappings:
            out.add_unknown(
                Unknown(
                    id=f"translate.domain.unmapped.{entity.concept}",
                    question=f"No declared mapping from '{entity.concept}' into pack {target_pack_id}.",
                    kind="unmapped_concept",
                    blocking=False,
                )
            )
            continue
        mapping = mappings[0]
        equivalence = mapping.get("equivalence", "partial")
        rule_ids.append(f"{mapping['from_pack']}:{entity.concept}->{mapping['target_concept']}")
        notes.append(mapping.get("note", ""))
        entity.attributes["domain_mapping"] = {
            "target_pack": target_pack_id,
            "target_concept": mapping["target_concept"],
            "equivalence": equivalence,
            "note": mapping.get("note", ""),
        }
        if equivalence != "exact":
            lossy = True
        if equivalence == "none":
            out.add_unknown(
                Unknown(
                    id=f"translate.domain.not_equivalent.{entity.concept}",
                    question=(
                        f"'{entity.concept}' has no equivalent in {target_pack_id}: {mapping.get('note', '')}"
                    ),
                    kind="non_equivalence",
                    blocking=True,
                )
            )

    out.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.translate.domain",
            source="atg.canonical",
            target=f"domain/{target_pack_id}@{target_pack.version}",
            rule_ids=rule_ids,
            pack_versions=registry.versions(),
            lossy=lossy,
            notes=[note for note in notes if note],
            confidence=round(max(0.0, out.confidence - (0.1 if lossy else 0.0)), 3),
        )
    )
    return out


def translate_code(
    envelope: SemanticEnvelope,
    target: Representation,
    registry: Optional[PackRegistry] = None,
) -> Tuple[str, SemanticEnvelope]:
    """Emit target-dialect code from the behavioural contracts in the envelope."""
    registry = registry or PackRegistry.load_default()
    spec, dialect = resolve_language(target.name, target.dialect or None)
    out = copy.deepcopy(envelope)
    source_rep = out.source.representation if out.source else Representation(kind="code", name="unknown")
    notes: List[str] = []
    applied_rule_ids: List[str] = []
    rendered = ""
    lossy = False

    try:
        if spec.language in ("python", "typescript"):
            contracts = [
                {
                    "name": contract.name,
                    "params": contract.signature.get("params", []),
                    "returns": contract.signature.get("returns", "unknown"),
                    "errors": contract.errors,
                    "docstring": contract.behavior.get("docstring", ""),
                    "statements": contract.behavior.get("statements", []),
                }
                for contract in out.contracts
                if contract.kind == "function"
            ]
            if not contracts:
                raise code_ir.UnsupportedConstruct("translate.code", "no function contracts in envelope")
            emitter = python_adapter if spec.language == "python" else typescript_adapter
            rendered, emit_notes = emitter.emit_functions(contracts)
            notes += emit_notes
            lossy = bool(emit_notes)
        elif spec.language == "sql":
            rendered, applied = _translate_sql(out, dialect)
            notes += [f"{item['rule_id']}: {item['note']}" for item in applied]
            applied_rule_ids += [item["rule_id"] for item in applied]
            lossy = any(item["equivalence"] != "exact" for item in applied)
            _record_sql_findings(out, applied, dialect)
        elif spec.language == "shell":
            rendered, applied, divergences = _translate_shell(out, source_rep, dialect)
            notes += [item["note"] for item in applied] + [item["statement"] for item in divergences]
            applied_rule_ids += [item["rule_id"] for item in applied] + [item["id"] for item in divergences]
            lossy = bool(divergences) or any(item["equivalence"] != "exact" for item in applied)
            _record_shell_findings(out, applied, divergences, dialect)
        else:
            raise code_ir.UnsupportedConstruct("translate.code", f"no emitter for {spec.language}")
    except code_ir.UnsupportedConstruct as error:
        out.add_unknown(
            Unknown(
                id="translate.code.unsupported",
                question=f"Cannot emit behaviour-preserving {spec.language}: {error}",
                kind="unsupported_construct",
                blocking=True,
            )
        )
        rendered = ""
        lossy = True
    except ValueError as error:
        out.add_unknown(
            Unknown(
                id="translate.code.error",
                question=str(error),
                kind="translation_error",
                blocking=True,
            )
        )
        rendered = ""
        lossy = True

    if notes:
        for note in notes:
            out.add_assumption(
                Assumption(
                    id=new_id("asm"),
                    statement=note,
                    basis=f"atg.translate.code:{spec.language}/{dialect}",
                    impact="medium",
                )
            )

    out.rendered = rendered
    out.target = Endpoint(
        representation=Representation(kind="code", name=spec.language, version=spec.version, dialect=dialect),
        context=(out.source.context if out.source else ContextVector()),
    )
    if out.target.context:
        out.target.context = ContextVector.from_dict(out.target.context.to_dict())
        out.target.context.programming_language = spec.language
        out.target.context.programming_dialect = dialect

    out.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.translate.code",
            source=source_rep.label(),
            target=f"code/{spec.language}/{dialect}",
            rule_ids=[f"atg.code.{spec.language}.emit.v1", *applied_rule_ids],
            pack_versions=registry.versions(),
            lossy=lossy,
            notes=notes,
            confidence=round(max(0.0, out.confidence - (0.1 if lossy else 0.0)), 3),
        )
    )
    return rendered, out


def _translate_sql(envelope: SemanticEnvelope, target_dialect: str) -> Tuple[str, List[Dict[str, Any]]]:
    source_rep = envelope.source.representation if envelope.source else None
    source_dialect = (source_rep.dialect if source_rep else "") or "postgresql"
    if not envelope.rendered:
        raise code_ir.UnsupportedConstruct("translate.code.sql", "envelope carries no source statement")
    return sql_dialects.translate_create_table(envelope.rendered, source_dialect, target_dialect)


def _record_sql_findings(envelope: SemanticEnvelope, applied: Sequence[Dict[str, Any]], dialect: str) -> None:
    for item in applied:
        envelope.constraints.append(
            Constraint(
                id=new_id("con"),
                kind="dialect_mapping",
                expression=f"{item['construct']}:{item['equivalence']}",
                severity="must",
                origin=item["rule_id"],
            )
        )
        if item.get("escalate"):
            envelope.add_unknown(
                Unknown(
                    id=f"translate.sql.{item['rule_id']}",
                    question=f"{item['construct']} cannot be preserved in {dialect}: {item['note']}",
                    kind="dialect_divergence",
                    blocking=True,
                )
            )


def _translate_shell(
    envelope: SemanticEnvelope, source_rep: Representation, target_dialect: str
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    source_dialect = source_rep.dialect or "sh"
    if not envelope.rendered:
        raise code_ir.UnsupportedConstruct("translate.code.shell", "envelope carries no source pipeline")
    return shell_semantics.translate_pipeline(envelope.rendered, source_dialect, target_dialect)


def _record_shell_findings(
    envelope: SemanticEnvelope,
    applied: Sequence[Dict[str, Any]],
    divergences: Sequence[Dict[str, Any]],
    dialect: str,
) -> None:
    for divergence in divergences:
        envelope.constraints.append(
            Constraint(
                id=new_id("con"),
                kind="execution_model_divergence",
                expression=divergence["statement"],
                severity="must",
                origin=divergence["id"],
            )
        )
        if divergence["impact"] == "high":
            envelope.add_unknown(
                Unknown(
                    id=f"translate.shell.{divergence['id']}",
                    question=f"{divergence['statement']} {divergence['consequence']}",
                    kind="execution_model_divergence",
                    blocking=True,
                )
            )
    for item in applied:
        if item.get("escalate"):
            envelope.add_unknown(
                Unknown(
                    id=f"translate.shell.op.{item['op']}",
                    question=f"{item['op']} has no behaviour-preserving form in {dialect}: {item['note']}",
                    kind="non_equivalence",
                    blocking=True,
                )
            )
        envelope.entities.append(
            Entity(
                id=new_id("ent"),
                concept=f"shell.mapping.{item['op']}",
                surface=str(item.get("target_form", "")),
                type="mapping",
                attributes=dict(item),
            )
        )
