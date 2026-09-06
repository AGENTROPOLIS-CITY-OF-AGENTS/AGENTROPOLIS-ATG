"""SOURCE -> canonical ATG parsing."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .code import ir as code_ir
from .code import python_adapter, shell_semantics, sql_dialects, typescript_adapter
from .code.registry import resolve_language
from .context import ContextVector, resolve_context
from .envelope import (
    Assumption,
    Constraint,
    Contract,
    Endpoint,
    Entity,
    Intent,
    ProvenanceSource,
    Relation,
    Representation,
    SemanticEnvelope,
    Transformation,
    Unknown,
    new_id,
)
from .escalation import apply_domain_policy
from .packs import DomainPack, PackRegistry

INTENT_VERBS = {
    "schedule": "schedule",
    "book": "schedule",
    "arrange": "schedule",
    "buy": "acquire",
    "purchase": "acquire",
    "acquire": "acquire",
    "sell": "dispose",
    "file": "file",
    "submit": "file",
    "report": "report",
    "compute": "compute",
    "calculate": "compute",
    "deploy": "deploy",
    "release": "deploy",
    "roll": "rollback",
    "rollback": "rollback",
    "review": "review",
    "send": "send",
    "mail": "send",
    "post": "send",
    "translate": "translate",
    "store": "store",
    "process": "process",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")


def digest(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse(
    content: str,
    representation: Representation,
    context: Optional[ContextVector] = None,
    registry: Optional[PackRegistry] = None,
    pack_ids: Optional[Sequence[str]] = None,
) -> SemanticEnvelope:
    """Parse any supported representation into a canonical semantic envelope."""
    registry = registry or PackRegistry.load_default()
    context = context or ContextVector()
    resolution = resolve_context(context)
    resolved = resolution.context
    if pack_ids is None:
        pack_ids = registry.resolve_for_context(resolved.industry, resolved.profession)
    packs = registry.select(pack_ids)

    envelope = SemanticEnvelope(
        source=Endpoint(representation=representation, context=resolved),
    )
    envelope.add_source(
        ProvenanceSource(
            id=new_id("src"),
            kind=representation.kind,
            reference=representation.label(),
            version=representation.version or "unversioned",
            digest=digest(content),
        )
    )
    for assumption in resolution.assumptions:
        envelope.add_assumption(Assumption(**assumption))
    for unknown in resolution.unknowns:
        envelope.add_unknown(Unknown(**unknown))

    if representation.kind == "human_text":
        _parse_human(content, envelope, packs, resolved)
    elif representation.kind == "code":
        _parse_code(content, representation, envelope, resolved)
    elif representation.kind in ("schema", "api", "protocol", "document"):
        _parse_structured(content, representation, envelope)
    else:
        envelope.add_unknown(
            Unknown(
                id="parse.unsupported_representation",
                question=f"No parser registered for representation kind '{representation.kind}'.",
                kind="unsupported_representation",
                blocking=True,
            )
        )

    apply_domain_policy(envelope, packs, resolved)
    _attach_jurisdiction_rules(envelope, packs, resolved)

    envelope.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.parse",
            source=representation.label(),
            target="atg.canonical",
            rule_ids=["atg.parse.v1"],
            pack_versions={pack.pack_id: pack.version for pack in packs},
            confidence=_confidence(envelope),
        )
    )
    envelope.confidence = _confidence(envelope)
    return envelope


# -- human text ---------------------------------------------------------------

def _disambiguate(candidates: Sequence[str], registry: PackRegistry):
    """Resolve an ambiguous term only when one active domain pack claims it.

    COMMON is excluded: it holds the ambiguity itself. Two domain candidates
    stay ambiguous rather than being guessed.
    """
    index = registry.concept_index()
    domain_matches = [
        index[concept]
        for concept in candidates
        if concept in index and index[concept].pack_id != "COMMON"
    ]
    return domain_matches[0] if len(domain_matches) == 1 else None


def _parse_human(
    content: str,
    envelope: SemanticEnvelope,
    packs: Sequence[DomainPack],
    context: ContextVector,
) -> None:
    registry = PackRegistry(packs)
    lexicon = registry.lexicon_index()
    lowered = content.lower()
    words = _WORD_RE.findall(lowered)

    matched: Dict[str, Entity] = {}
    for size in (3, 2, 1):
        for index in range(len(words) - size + 1):
            term = " ".join(words[index : index + size])
            entries = lexicon.get(term)
            if not entries:
                continue
            concepts = {entry.concept for entry in entries}
            entry = entries[0]
            if entry.ambiguous or len(concepts) > 1:
                candidates = sorted(concepts | set(entry.attributes.get("candidates", [])))
                resolved = _disambiguate(candidates, registry)
                if resolved is not None:
                    envelope.add_assumption(
                        Assumption(
                            id=new_id("asm"),
                            statement=(
                                f"Term '{term}' resolved to {resolved.concept} because the active domain pack "
                                f"{resolved.pack_id} supplies exactly one candidate."
                            ),
                            basis="atg.parse.domain_disambiguation",
                            impact="medium",
                        )
                    )
                    entry = resolved
                else:
                    envelope.add_unknown(
                        Unknown(
                            id=f"parse.ambiguous.{term.replace(' ', '_')}",
                            question=(
                                f"Term '{term}' is ambiguous "
                                f"({entry.ambiguity_note or 'multiple candidate concepts'})."
                            ),
                            kind="ambiguity",
                            blocking=True,
                            candidates=candidates,
                        )
                    )
                    continue
            if entry.concept in matched:
                continue
            matched[entry.concept] = Entity(
                id=new_id("ent"),
                concept=entry.concept,
                surface=term,
                type=entry.type,
                attributes={
                    "pack": entry.pack_id,
                    "pack_version": entry.pack_version,
                    "definition": entry.definition,
                },
            )
    envelope.entities.extend(matched.values())

    act = "state"
    for word in words:
        if word in INTENT_VERBS:
            act = INTENT_VERBS[word]
            break
    envelope.intent = Intent(
        act=act,
        predicate="|".join(sorted(matched)),
        arguments={"locale": context.locale, "jurisdiction": context.jurisdiction},
    )
    envelope.rendered = content

    concept_ids = set(matched)
    for pack in packs:
        for relationship in pack.data.get("relationships") or []:
            if relationship.get("source") in concept_ids and relationship.get("target") in concept_ids:
                envelope.relations.append(
                    Relation(
                        id=new_id("rel"),
                        type=relationship["type"],
                        source=relationship["source"],
                        target=relationship["target"],
                        attributes={"pack": pack.pack_id, "pack_version": pack.version},
                    )
                )


def _attach_jurisdiction_rules(
    envelope: SemanticEnvelope,
    packs: Sequence[DomainPack],
    context: ContextVector,
) -> None:
    concepts = {entity.concept for entity in envelope.entities}
    for pack in packs:
        for rule in pack.jurisdiction_rules(context.jurisdiction):
            applies_to = set(rule.get("applies_to") or [])
            if applies_to and not (applies_to & concepts):
                continue
            if not applies_to and rule.get("jurisdiction") != "*":
                continue
            envelope.constraints.append(
                Constraint(
                    id=new_id("con"),
                    kind=rule.get("kind", "regulatory"),
                    expression=rule["expression"],
                    severity=rule.get("severity", "must"),
                    origin=f"{pack.pack_id}@{pack.version}:{rule['rule_id']}",
                )
            )
            authority_id = rule.get("authority")
            if authority_id:
                authority = next(
                    (a for a in pack.data.get("authorities") or [] if a.get("id") == authority_id),
                    None,
                )
                concept = f"authority.{authority_id}"
                if authority and concept not in {e.concept for e in envelope.entities}:
                    envelope.entities.append(
                        Entity(
                            id=new_id("ent"),
                            concept=concept,
                            surface=authority.get("name", authority_id),
                            type="authority",
                            attributes={
                                "jurisdiction": authority.get("jurisdiction"),
                                "scope": authority.get("scope"),
                                "pack": pack.pack_id,
                                "pack_version": pack.version,
                            },
                        )
                    )
    for regulation in context.regulations:
        envelope.constraints.append(
            Constraint(
                id=new_id("con"),
                kind="regulatory",
                expression=f"region_regulation_applies:{regulation}",
                severity="must",
                origin=f"region:{context.region}",
            )
        )


# -- code ---------------------------------------------------------------------

def _parse_code(
    content: str,
    representation: Representation,
    envelope: SemanticEnvelope,
    context: ContextVector,
) -> None:
    spec, dialect = resolve_language(representation.name, representation.dialect or None)
    envelope.intent = Intent(act="define_behavior", predicate=f"{spec.language}:{dialect}", arguments={})
    envelope.rendered = content

    if spec.parse_support == "none":
        envelope.add_unknown(
            Unknown(
                id=f"parse.code.unsupported.{spec.language}",
                question=(
                    f"{spec.language} is registered as an ATG language but has no parsing adapter yet; "
                    "behavioural equivalence cannot be proven."
                ),
                kind="unsupported_language",
                blocking=True,
            )
        )
        return

    try:
        if spec.language == "python":
            _load_function_contracts(python_adapter.parse_functions(content), envelope, dialect)
        elif spec.language == "typescript":
            _load_function_contracts(typescript_adapter.parse_functions(content), envelope, dialect)
        elif spec.language == "sql":
            _parse_sql(content, dialect, envelope)
        elif spec.language == "shell":
            _parse_shell(content, dialect, envelope)
        else:
            _parse_structured(content, representation, envelope)
    except code_ir.UnsupportedConstruct as error:
        envelope.add_unknown(
            Unknown(
                id="parse.code.unsupported_construct",
                question=f"Unsupported construct for behavioural equivalence: {error}",
                kind="unsupported_construct",
                blocking=True,
            )
        )
    except ValueError as error:
        envelope.add_unknown(
            Unknown(
                id="parse.code.error",
                question=str(error),
                kind="parse_error",
                blocking=True,
            )
        )


def _load_function_contracts(contracts: List[Dict[str, Any]], envelope: SemanticEnvelope, dialect: str) -> None:
    for contract in contracts:
        envelope.contracts.append(
            Contract(
                id=new_id("ctr"),
                kind="function",
                name=contract["name"],
                signature={"params": contract["params"], "returns": contract["returns"]},
                preconditions=[
                    code_ir.expression_signature(s["test"])
                    for s in contract["statements"]
                    if s.get("stmt") == "if"
                ],
                postconditions=[
                    code_ir.expression_signature(s.get("value"))
                    for s in contract["statements"]
                    if s.get("stmt") == "return"
                ],
                errors=contract["errors"],
                effects=[],
                behavior={
                    "statements": contract["statements"],
                    "signature": code_ir.behavior_signature(contract["statements"]),
                    "dialect": dialect,
                    "docstring": contract.get("docstring", ""),
                },
            )
        )
        envelope.entities.append(
            Entity(
                id=new_id("ent"),
                concept="code.function",
                surface=contract["name"],
                type="function",
                attributes={"dialect": dialect, "arity": len(contract["params"])},
            )
        )


def _parse_sql(content: str, dialect: str, envelope: SemanticEnvelope) -> None:
    table = sql_dialects.parse_create_table(content, dialect)
    envelope.contracts.append(
        Contract(
            id=new_id("ctr"),
            kind="schema",
            name=table.name,
            signature={
                "columns": [
                    {"name": c.name, "type": c.type, "constraints": c.constraints, "constructs": c.constructs}
                    for c in table.columns
                ]
            },
            preconditions=list(table.table_constraints),
            behavior={"dialect": dialect, "canonical": sql_dialects.canonical_table_signature(table)},
        )
    )
    envelope.entities.append(
        Entity(
            id=new_id("ent"),
            concept="code.relation",
            surface=table.name,
            type="table",
            attributes={"dialect": dialect, "columns": [c.name for c in table.columns]},
        )
    )
    for column in table.columns:
        for construct in column.constructs:
            envelope.constraints.append(
                Constraint(
                    id=new_id("con"),
                    kind="dialect_construct",
                    expression=f"{table.name}.{column.name}:{construct}",
                    severity="must",
                    origin=f"sql:{dialect}",
                )
            )


def _parse_shell(content: str, dialect: str, envelope: SemanticEnvelope) -> None:
    operations = shell_semantics.parse_pipeline(content, dialect)
    model = shell_semantics.pipeline_model(dialect)
    envelope.intent = Intent(act="execute_pipeline", predicate=f"shell:{dialect}", arguments={"pipeline_model": model})
    envelope.constraints.append(
        Constraint(
            id=new_id("con"),
            kind="execution_model",
            expression=f"pipeline_model={model}",
            severity="must",
            origin=f"shell:{dialect}",
        )
    )
    for operation in operations:
        envelope.entities.append(
            Entity(
                id=new_id("ent"),
                concept=f"shell.op.{operation.op}",
                surface=operation.raw,
                type="operation",
                attributes={"dialect": dialect, "arguments": operation.arguments},
            )
        )
        if operation.op == "unknown_command":
            envelope.add_unknown(
                Unknown(
                    id=f"parse.shell.unknown_command.{len(envelope.unknowns)}",
                    question=f"No semantic mapping registered for shell stage {operation.raw!r}.",
                    kind="unsupported_construct",
                    blocking=True,
                )
            )


def _parse_structured(content: str, representation: Representation, envelope: SemanticEnvelope) -> None:
    import json

    import yaml

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as error:
            envelope.add_unknown(
                Unknown(
                    id="parse.structured.error",
                    question=f"Could not parse structured document: {error}",
                    kind="parse_error",
                    blocking=True,
                )
            )
            return
    envelope.intent = Intent(act="declare_schema", predicate=representation.label(), arguments={})
    envelope.rendered = content
    if isinstance(data, dict):
        properties = data.get("properties") if isinstance(data.get("properties"), dict) else data
        required = set(data.get("required") or [])
        envelope.contracts.append(
            Contract(
                id=new_id("ctr"),
                kind="schema",
                name=str(data.get("title") or representation.name),
                signature={
                    "fields": [
                        {
                            "name": key,
                            "type": (value.get("type") if isinstance(value, dict) else type(value).__name__),
                            "required": key in required,
                        }
                        for key, value in properties.items()
                    ]
                },
            )
        )


def _confidence(envelope: SemanticEnvelope) -> float:
    confidence = 1.0
    for unknown in envelope.unknowns:
        confidence -= 0.25 if unknown.blocking else 0.05
    for assumption in envelope.assumptions:
        confidence -= {"high": 0.1, "medium": 0.05}.get(assumption.impact, 0.01)
    return round(max(0.0, min(1.0, confidence)), 3)


def concepts_of(envelope: SemanticEnvelope, exclude_types: Iterable[str] = ("authority",)) -> List[str]:
    excluded = set(exclude_types)
    return sorted({e.concept for e in envelope.entities if e.type not in excluded})
