"""The twelve ATG MCP tool contracts.

Contracts are declared as data (name, description, JSON Schema) and bound to
plain callables, so the same definitions can be served over MCP stdio, HTTP or
an in-process call without changing the tool surface. Nothing in this module
depends on a pack implementation: packs are resolved at call time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from atg_core import (
    ContextVector,
    PackRegistry,
    Representation,
    SemanticEnvelope,
    explain_code_mapping,
    explain_mapping,
    localize,
    normalize,
    parse,
    resolve_context,
    roundtrip,
    translate_code,
    translate_domain,
    translate_human,
    validate,
)
from atg_core.provenance import LEDGER, provenance_record
from atg_core.version import ATG_VERSION

_CONTEXT_SCHEMA = {"type": "object", "description": "ATG context vector", "additionalProperties": True}
_ENVELOPE_SCHEMA = {"type": "object", "description": "ATG semantic envelope", "additionalProperties": True}
_REPRESENTATION_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["human_text", "code", "schema", "api", "protocol", "document"]},
        "name": {"type": "string"},
        "version": {"type": "string"},
        "dialect": {"type": "string"},
    },
    "required": ["kind", "name"],
}


@dataclass
class ToolContract:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]

    def to_mcp(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
        }


def _registry(arguments: Dict[str, Any]) -> PackRegistry:
    return PackRegistry.load_default()


def _representation(data: Optional[Dict[str, Any]], default_kind: str = "human_text") -> Representation:
    data = data or {}
    return Representation(
        kind=data.get("kind", default_kind),
        name=data.get("name", "natural_language"),
        version=str(data.get("version", "")),
        dialect=data.get("dialect", ""),
    )


def _context(data: Optional[Dict[str, Any]]) -> ContextVector:
    return ContextVector.from_dict(data or {})


def _envelope(data: Dict[str, Any]) -> SemanticEnvelope:
    return SemanticEnvelope.from_dict(data)


def _record(envelope: SemanticEnvelope, validation: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    LEDGER.record(envelope, validation)
    return envelope.to_dict()


# -- handlers -----------------------------------------------------------------

def handle_parse(arguments: Dict[str, Any]) -> Dict[str, Any]:
    envelope = parse(
        arguments["content"],
        _representation(arguments.get("representation")),
        _context(arguments.get("context")),
        registry=_registry(arguments),
        pack_ids=arguments.get("packs"),
    )
    return {"envelope": _record(envelope), "requires_escalation": envelope.requires_escalation}


def handle_normalize(arguments: Dict[str, Any]) -> Dict[str, Any]:
    envelope = normalize(_envelope(arguments["envelope"]), registry=_registry(arguments))
    return {
        "envelope": _record(envelope),
        "canonical_hash": envelope.canonical_hash(),
        "core_hash": envelope.core_hash(),
    }


def handle_context_resolve(arguments: Dict[str, Any]) -> Dict[str, Any]:
    resolution = resolve_context(_context(arguments.get("context")))
    return {
        "context": resolution.context.to_dict(),
        "assumptions": resolution.assumptions,
        "unknowns": resolution.unknowns,
        "execution_profile": resolution.execution_profile,
        "requires_escalation": resolution.requires_escalation,
    }


def handle_translate_human(arguments: Dict[str, Any]) -> Dict[str, Any]:
    envelope = translate_human(
        _envelope(arguments["envelope"]),
        _context(arguments.get("target_context")),
        registry=_registry(arguments),
    )
    return {"envelope": _record(envelope), "rendered": envelope.rendered, "lossy": envelope.is_lossy()}


def handle_translate_domain(arguments: Dict[str, Any]) -> Dict[str, Any]:
    envelope = translate_domain(
        _envelope(arguments["envelope"]),
        arguments["target_pack"],
        registry=_registry(arguments),
    )
    return {"envelope": _record(envelope), "lossy": envelope.is_lossy()}


def handle_translate_code(arguments: Dict[str, Any]) -> Dict[str, Any]:
    rendered, envelope = translate_code(
        _envelope(arguments["envelope"]),
        _representation(arguments["target"], default_kind="code"),
        registry=_registry(arguments),
    )
    return {"envelope": _record(envelope), "rendered": rendered, "lossy": envelope.is_lossy()}


def handle_localize(arguments: Dict[str, Any]) -> Dict[str, Any]:
    result = localize(
        _envelope(arguments["envelope"]),
        _context(arguments.get("target_context")),
        registry=_registry(arguments),
    )
    LEDGER.record(result.envelope)
    return result.to_dict()


def handle_validate(arguments: Dict[str, Any]) -> Dict[str, Any]:
    result = validate(_envelope(arguments["source_envelope"]), _envelope(arguments["reverse_envelope"]))
    return result.to_dict()


def handle_roundtrip(arguments: Dict[str, Any]) -> Dict[str, Any]:
    result = roundtrip(
        arguments["content"],
        _representation(arguments["source"]),
        _representation(arguments["target"]),
        _context(arguments.get("source_context")),
        _context(arguments.get("target_context")) if arguments.get("target_context") else None,
        registry=_registry(arguments),
        pack_ids=arguments.get("packs"),
    )
    LEDGER.record(result.target_envelope, result.validation.to_dict())
    return result.to_dict()


def handle_explain_mapping(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if arguments.get("construct"):
        return explain_code_mapping(
            arguments["construct"],
            arguments.get("source_dialect", ""),
            arguments.get("target_dialect", ""),
        )
    return explain_mapping(
        arguments["concept"],
        source_locale=arguments.get("source_locale"),
        target_locale=arguments.get("target_locale"),
        target_pack_id=arguments.get("target_pack"),
        registry=_registry(arguments),
    )


def handle_pack_resolve(arguments: Dict[str, Any]) -> Dict[str, Any]:
    registry = _registry(arguments)
    context = _context(arguments.get("context"))
    pack_ids = arguments.get("packs") or registry.resolve_for_context(context.industry, context.profession)
    packs = registry.select(pack_ids)
    return {
        "packs": [
            {
                "pack_id": pack.pack_id,
                "version": pack.version,
                "title": pack.title,
                "concepts": len(pack.lexicon),
                "supported_jurisdictions": pack.supported_jurisdictions(),
                "path": pack.path,
            }
            for pack in packs
        ],
        "pack_versions": registry.versions(pack_ids),
        "available": registry.ids(),
    }


def handle_provenance(arguments: Dict[str, Any]) -> Dict[str, Any]:
    if arguments.get("envelope"):
        return provenance_record(_envelope(arguments["envelope"]), arguments.get("validation"))
    record = LEDGER.get(arguments["message_id"])
    if record is None:
        return {"found": False, "message_id": arguments["message_id"]}
    return {"found": True, **record}


# -- contracts ----------------------------------------------------------------

def build_contracts() -> List[ToolContract]:
    return [
        ToolContract(
            name="atg.parse",
            description="Parse any representation (human text, code, schema, API) into a canonical ATG envelope.",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "representation": _REPRESENTATION_SCHEMA,
                    "context": _CONTEXT_SCHEMA,
                    "packs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["content", "representation"],
            },
            output_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "requires_escalation": {"type": "boolean"}},
            },
            handler=handle_parse,
        ),
        ToolContract(
            name="atg.normalize",
            description="Canonicalise an envelope and return its canonical and region-free core hashes.",
            input_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA},
                "required": ["envelope"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "envelope": _ENVELOPE_SCHEMA,
                    "canonical_hash": {"type": "string"},
                    "core_hash": {"type": "string"},
                },
            },
            handler=handle_normalize,
        ),
        ToolContract(
            name="atg.context.resolve",
            description="Resolve a context vector into execution assumptions; never infers high-impact jurisdiction.",
            input_schema={"type": "object", "properties": {"context": _CONTEXT_SCHEMA}, "required": ["context"]},
            output_schema={
                "type": "object",
                "properties": {
                    "context": _CONTEXT_SCHEMA,
                    "assumptions": {"type": "array"},
                    "unknowns": {"type": "array"},
                    "execution_profile": {"type": "object"},
                    "requires_escalation": {"type": "boolean"},
                },
            },
            handler=handle_context_resolve,
        ),
        ToolContract(
            name="atg.translate.human",
            description="Render a canonical envelope into a target human locale, preserving concept identity.",
            input_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "target_context": _CONTEXT_SCHEMA},
                "required": ["envelope", "target_context"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "envelope": _ENVELOPE_SCHEMA,
                    "rendered": {"type": "string"},
                    "lossy": {"type": "boolean"},
                },
            },
            handler=handle_translate_human,
        ),
        ToolContract(
            name="atg.translate.domain",
            description="Re-frame concepts into another domain pack through declared crosswalks only.",
            input_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "target_pack": {"type": "string"}},
                "required": ["envelope", "target_pack"],
            },
            output_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "lossy": {"type": "boolean"}},
            },
            handler=handle_translate_domain,
        ),
        ToolContract(
            name="atg.translate.code",
            description="Emit target-dialect code from behavioural contracts; unproven equivalence escalates.",
            input_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "target": _REPRESENTATION_SCHEMA},
                "required": ["envelope", "target"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "envelope": _ENVELOPE_SCHEMA,
                    "rendered": {"type": "string"},
                    "lossy": {"type": "boolean"},
                },
            },
            handler=handle_translate_code,
        ),
        ToolContract(
            name="atg.localize",
            description="Apply a target region as execution context: units, currency, formats, regulations, residency.",
            input_schema={
                "type": "object",
                "properties": {"envelope": _ENVELOPE_SCHEMA, "target_context": _CONTEXT_SCHEMA},
                "required": ["envelope", "target_context"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "envelope": _ENVELOPE_SCHEMA,
                    "rendered": {"type": "string"},
                    "execution_assumptions": {"type": "object"},
                    "changed_execution_fields": {"type": "array", "items": {"type": "string"}},
                },
            },
            handler=handle_localize,
        ),
        ToolContract(
            name="atg.validate",
            description="Compare a source envelope with a reverse-parsed envelope; fails closed on material drift.",
            input_schema={
                "type": "object",
                "properties": {"source_envelope": _ENVELOPE_SCHEMA, "reverse_envelope": _ENVELOPE_SCHEMA},
                "required": ["source_envelope", "reverse_envelope"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "passed": {"type": "boolean"},
                    "semantic_equivalence": {"type": "number"},
                    "confidence": {"type": "number"},
                    "drift": {"type": "array"},
                    "ambiguities": {"type": "array"},
                    "conflicts": {"type": "array"},
                    "requires_escalation": {"type": "boolean"},
                },
            },
            handler=handle_validate,
        ),
        ToolContract(
            name="atg.roundtrip",
            description="SOURCE -> ATG -> TARGET -> reverse ATG -> compare, returning a roundtrip score.",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "source": _REPRESENTATION_SCHEMA,
                    "target": _REPRESENTATION_SCHEMA,
                    "source_context": _CONTEXT_SCHEMA,
                    "target_context": _CONTEXT_SCHEMA,
                    "packs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["content", "source", "target"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "rendered": {"type": "string"},
                    "roundtrip_score": {"type": "number"},
                    "passed": {"type": "boolean"},
                    "validation": {"type": "object"},
                },
            },
            handler=handle_roundtrip,
        ),
        ToolContract(
            name="atg.explain_mapping",
            description=(
                "Explain how a concept or code construct maps, with rule ids, "
                "equivalence class and pack versions."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "construct": {"type": "string"},
                    "source_locale": {"type": "string"},
                    "target_locale": {"type": "string"},
                    "target_pack": {"type": "string"},
                    "source_dialect": {"type": "string"},
                    "target_dialect": {"type": "string"},
                },
            },
            output_schema={"type": "object", "additionalProperties": True},
            handler=handle_explain_mapping,
        ),
        ToolContract(
            name="atg.pack.resolve",
            description="Resolve which versioned domain packs apply to a context.",
            input_schema={
                "type": "object",
                "properties": {"context": _CONTEXT_SCHEMA, "packs": {"type": "array", "items": {"type": "string"}}},
            },
            output_schema={
                "type": "object",
                "properties": {
                    "packs": {"type": "array"},
                    "pack_versions": {"type": "object"},
                    "available": {"type": "array"},
                },
            },
            handler=handle_pack_resolve,
        ),
        ToolContract(
            name="atg.provenance",
            description="Return the full lineage record for an envelope or a previously recorded message id.",
            input_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "envelope": _ENVELOPE_SCHEMA,
                    "validation": {"type": "object"},
                },
            },
            output_schema={"type": "object", "additionalProperties": True},
            handler=handle_provenance,
        ),
    ]


TOOL_CONTRACTS: List[ToolContract] = build_contracts()
TOOLS: Dict[str, ToolContract] = {contract.name: contract for contract in TOOL_CONTRACTS}
TOOL_NAMES: List[str] = [contract.name for contract in TOOL_CONTRACTS]


def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """In-process invocation used by tests, adapters and non-MCP callers."""
    contract = TOOLS.get(name)
    if contract is None:
        raise KeyError(f"unknown ATG tool '{name}' (known: {', '.join(TOOL_NAMES)})")
    return contract.handler(arguments or {})


def server_info() -> Dict[str, Any]:
    return {"name": "atg-mcp", "version": ATG_VERSION, "tools": TOOL_NAMES}
