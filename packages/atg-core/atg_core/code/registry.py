"""Registry of programming languages, dialects and their semantic capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class LanguageSpec:
    language: str
    version: str
    dialects: List[str] = field(default_factory=list)
    default_dialect: str = ""
    paradigm: str = ""
    typing: str = "dynamic"
    parse_support: str = "none"  # none | subset | full
    emit_support: str = "none"
    semantic_notes: List[str] = field(default_factory=list)


LANGUAGE_REGISTRY: Dict[str, LanguageSpec] = {
    "python": LanguageSpec(
        language="python",
        version="3.10",
        dialects=["cpython"],
        default_dialect="cpython",
        paradigm="multi-paradigm",
        typing="gradual",
        parse_support="subset",
        emit_support="subset",
        semantic_notes=[
            "int is arbitrary precision; mapping to IEEE-754 doubles is a widening",
            "exceptions are part of the contract surface",
        ],
    ),
    "typescript": LanguageSpec(
        language="typescript",
        version="5.x",
        dialects=["typescript", "javascript", "tsx"],
        default_dialect="typescript",
        paradigm="multi-paradigm",
        typing="structural-static",
        parse_support="subset",
        emit_support="subset",
        semantic_notes=[
            "number is IEEE-754 double; there is no integer type",
            "thrown values are untyped; error identity must be encoded explicitly",
        ],
    ),
    "rust": LanguageSpec(
        language="rust",
        version="1.7x",
        dialects=["rust2021"],
        default_dialect="rust2021",
        paradigm="systems",
        typing="nominal-static",
        parse_support="none",
        emit_support="none",
        semantic_notes=[
            "ownership and lifetimes have no counterpart in the current IR",
            "registered as a first-class ATG language; transforms escalate until an adapter lands",
        ],
    ),
    "sql": LanguageSpec(
        language="sql",
        version="2016",
        dialects=["postgresql", "mysql", "sqlite", "sqlserver"],
        default_dialect="postgresql",
        paradigm="declarative",
        typing="static",
        parse_support="subset",
        emit_support="subset",
        semantic_notes=[
            "dialects differ in type systems, identity generation and JSON support",
        ],
    ),
    "shell": LanguageSpec(
        language="shell",
        version="posix-2018",
        dialects=["sh", "bash", "zsh", "powershell"],
        default_dialect="sh",
        paradigm="imperative",
        typing="untyped",
        parse_support="subset",
        emit_support="subset",
        semantic_notes=[
            "POSIX shells pipe bytes; PowerShell pipes .NET objects",
        ],
    ),
    "json": LanguageSpec(
        language="json",
        version="rfc8259",
        dialects=["json", "json-schema-2020-12"],
        default_dialect="json",
        typing="structural",
        parse_support="full",
        emit_support="full",
    ),
    "yaml": LanguageSpec(
        language="yaml",
        version="1.2",
        dialects=["yaml"],
        default_dialect="yaml",
        typing="structural",
        parse_support="full",
        emit_support="full",
    ),
    "api": LanguageSpec(
        language="api",
        version="1",
        dialects=["rest", "graphql", "openapi-3.1"],
        default_dialect="openapi-3.1",
        typing="schema",
        parse_support="subset",
        emit_support="subset",
        semantic_notes=[
            "REST resources, GraphQL fields and OpenAPI operations map through contracts[]",
        ],
    ),
}

DIALECT_INDEX: Dict[str, str] = {
    dialect: spec.language for spec in LANGUAGE_REGISTRY.values() for dialect in spec.dialects
}


def resolve_language(language: Optional[str], dialect: Optional[str] = None) -> Tuple[LanguageSpec, str]:
    """Resolve (language, dialect) to a spec plus the effective dialect."""
    key = (language or "").lower()
    if key not in LANGUAGE_REGISTRY and dialect:
        key = DIALECT_INDEX.get(dialect.lower(), key)
    if key not in LANGUAGE_REGISTRY:
        raise KeyError(f"unregistered ATG code language: {language!r} (dialect {dialect!r})")
    spec = LANGUAGE_REGISTRY[key]
    effective = (dialect or spec.default_dialect).lower()
    if effective not in spec.dialects:
        raise KeyError(f"unregistered dialect {dialect!r} for language {spec.language}")
    return spec, effective


def registry_snapshot() -> Dict[str, Dict[str, object]]:
    return {
        key: {
            "version": spec.version,
            "dialects": list(spec.dialects),
            "default_dialect": spec.default_dialect,
            "typing": spec.typing,
            "parse_support": spec.parse_support,
            "emit_support": spec.emit_support,
            "semantic_notes": list(spec.semantic_notes),
        }
        for key, spec in LANGUAGE_REGISTRY.items()
    }
