"""SQL dialect handling.

SQL is one ATG language with several dialects whose differences are semantic,
not cosmetic. Dialect-specific constructs are handled explicitly: each mapping
declares its equivalence class, and anything below ``exact`` is surfaced as a
visible loss with an escalation flag when behaviour can change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

DIALECTS = ("postgresql", "mysql", "sqlite", "sqlserver")


@dataclass
class ConstructMapping:
    rule_id: str
    construct: str
    source_dialect: str
    target_dialect: str
    source_form: str
    target_form: str
    equivalence: str  # exact | partial | none
    note: str
    escalate: bool = False
    match_pattern: str = ""

    @property
    def pattern(self) -> "re.Pattern[str]":
        return re.compile(self.match_pattern or re.escape(self.source_form), re.IGNORECASE)


CONSTRUCT_MAPPINGS: List[ConstructMapping] = [
    ConstructMapping(
        rule_id="sql.pg_sqlite.serial",
        construct="identity_column",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="SERIAL PRIMARY KEY",
        target_form="INTEGER PRIMARY KEY AUTOINCREMENT",
        equivalence="partial",
        match_pattern=r"\bSERIAL(\s+PRIMARY\s+KEY)?\b",
        note=(
            "PostgreSQL SERIAL is backed by an independent sequence that survives row deletion and "
            "can be shared; SQLite AUTOINCREMENT is derived from rowid and monotonic per table."
        ),
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.jsonb",
        construct="json_storage",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="JSONB",
        target_form="TEXT",
        equivalence="none",
        match_pattern=r"\bJSONB\b",
        note=(
            "SQLite has no JSONB storage type, GIN indexing or containment operators; JSON is stored "
            "as text and queried through the json1 extension."
        ),
        escalate=True,
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.timestamptz",
        construct="timestamp_with_zone",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="TIMESTAMPTZ",
        target_form="TEXT",
        equivalence="partial",
        match_pattern=r"\bTIMESTAMPTZ\b",
        note="SQLite has no time-zone aware type; the zone must be normalised to UTC by the writer.",
        escalate=True,
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.boolean",
        construct="boolean",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="BOOLEAN",
        target_form="INTEGER",
        equivalence="partial",
        note="SQLite stores booleans as 0/1 integers; TRUE/FALSE literals are not native.",
        match_pattern=r"\bBOOLEAN\b",
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.numeric",
        construct="exact_numeric",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="NUMERIC(p,s)",
        target_form="NUMERIC",
        equivalence="partial",
        note="SQLite ignores precision/scale; arithmetic falls back to floating point.",
        escalate=True,
        match_pattern=r"\bNUMERIC\s*\(\s*\d+\s*,\s*\d+\s*\)",
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.ilike",
        construct="case_insensitive_match",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="ILIKE",
        target_form="LIKE",
        equivalence="partial",
        match_pattern=r"\bILIKE\b",
        note="SQLite LIKE is case-insensitive for ASCII only; non-ASCII comparisons diverge.",
    ),
    ConstructMapping(
        rule_id="sql.pg_sqlite.returning",
        construct="returning_clause",
        source_dialect="postgresql",
        target_dialect="sqlite",
        source_form="RETURNING",
        target_form="RETURNING",
        equivalence="partial",
        match_pattern=r"\bRETURNING\b",
        note="SQLite supports RETURNING only from 3.35.0; the runtime version becomes an assumption.",
    ),
    ConstructMapping(
        rule_id="sql.sqlite_pg.autoincrement",
        construct="identity_column",
        source_dialect="sqlite",
        target_dialect="postgresql",
        source_form="INTEGER PRIMARY KEY AUTOINCREMENT",
        target_form="SERIAL PRIMARY KEY",
        equivalence="partial",
        match_pattern=r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b",
        note="PostgreSQL uses a sequence; rowid semantics and implicit aliasing do not carry over.",
    ),
    ConstructMapping(
        rule_id="sql.sqlite_pg.affinity",
        construct="type_affinity",
        source_dialect="sqlite",
        target_dialect="postgresql",
        source_form="dynamic type affinity",
        target_form="static column types",
        equivalence="partial",
        note="SQLite permits values of any storage class in a column; PostgreSQL enforces the type.",
        escalate=True,
    ),
]

_COLUMN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$")
_CREATE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_\.]*)\s*\((.*)\)\s*;?",
                        re.IGNORECASE | re.DOTALL)


@dataclass
class SqlColumn:
    name: str
    type: str
    constraints: str = ""
    constructs: List[str] = field(default_factory=list)


@dataclass
class SqlTable:
    name: str
    columns: List[SqlColumn] = field(default_factory=list)
    table_constraints: List[str] = field(default_factory=list)


def parse_create_table(sql: str, dialect: str) -> SqlTable:
    sql = re.sub(r"--[^\n]*", "", sql)
    match = _CREATE_RE.search(sql)
    if not match:
        raise ValueError("only CREATE TABLE statements are supported by the SQL subset parser")
    name = match.group(1)
    body = match.group(2)
    table = SqlTable(name=name)
    for raw in _split_columns(body):
        piece = raw.strip()
        if not piece:
            continue
        if piece.upper().startswith(("PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK", "CONSTRAINT")):
            table.table_constraints.append(piece)
            continue
        column_match = _COLUMN_RE.match(piece)
        if not column_match:
            raise ValueError(f"unparsed column definition: {piece!r}")
        column_name, remainder = column_match.groups()
        type_token, _, constraints = remainder.partition(" ")
        if remainder.upper().startswith("INTEGER PRIMARY KEY AUTOINCREMENT"):
            type_token, constraints = "INTEGER", "PRIMARY KEY AUTOINCREMENT"
        elif "(" in type_token and ")" not in type_token:
            close = remainder.index(")")
            type_token, constraints = remainder[: close + 1], remainder[close + 1 :].strip()
        table.columns.append(
            SqlColumn(
                name=column_name,
                type=type_token.strip(),
                constraints=constraints.strip(),
                constructs=detect_constructs(f"{type_token} {constraints}", dialect),
            )
        )
    return table


def _split_columns(body: str) -> List[str]:
    parts, depth, current = [], 0, []
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def detect_constructs(fragment: str, dialect: str) -> List[str]:
    found: List[str] = []
    for mapping in CONSTRUCT_MAPPINGS:
        if mapping.source_dialect != dialect or not mapping.match_pattern:
            continue
        if mapping.pattern.search(fragment) and mapping.construct not in found:
            found.append(mapping.construct)
    return found


def mapping_for(construct: str, source_dialect: str, target_dialect: str) -> Optional[ConstructMapping]:
    for mapping in CONSTRUCT_MAPPINGS:
        if (
            mapping.construct == construct
            and mapping.source_dialect == source_dialect
            and mapping.target_dialect == target_dialect
        ):
            return mapping
    return None


def translate_create_table(
    sql: str, source_dialect: str, target_dialect: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """Translate a CREATE TABLE across dialects, returning (sql, applied mappings)."""
    if source_dialect not in DIALECTS or target_dialect not in DIALECTS:
        raise ValueError(f"unsupported SQL dialect pair: {source_dialect} -> {target_dialect}")
    table = parse_create_table(sql, source_dialect)
    applied: List[Dict[str, Any]] = []
    entries: List[Tuple[str, str]] = []
    for column in table.columns:
        definition = f"{column.type} {column.constraints}".strip()
        comments: List[str] = []
        for construct in column.constructs:
            mapping = mapping_for(construct, source_dialect, target_dialect)
            if mapping is None:
                applied.append(
                    {
                        "rule_id": f"sql.unmapped.{construct}",
                        "construct": construct,
                        "column": column.name,
                        "equivalence": "none",
                        "note": f"no registered mapping for {construct} from {source_dialect} to {target_dialect}",
                        "escalate": True,
                    }
                )
                continue
            definition = _apply(definition, mapping)
            comments.append(f"{mapping.rule_id} ({mapping.equivalence})")
            applied.append(
                {
                    "rule_id": mapping.rule_id,
                    "construct": construct,
                    "column": column.name,
                    "equivalence": mapping.equivalence,
                    "note": mapping.note,
                    "escalate": mapping.escalate,
                    "source_form": mapping.source_form,
                    "target_form": mapping.target_form,
                }
            )
        entries.append((f"  {column.name} {definition}".rstrip(), "; ".join(comments)))
    for constraint in table.table_constraints:
        entries.append((f"  {constraint}", ""))
    lines = []
    for index, (text, comment) in enumerate(entries):
        separator = "," if index < len(entries) - 1 else ""
        lines.append(f"{text}{separator}" + (f" -- atg: {comment}" if comment else ""))
    body = "\n".join(lines)
    return f"CREATE TABLE {table.name} (\n{body}\n);\n", applied


def _apply(definition: str, mapping: ConstructMapping) -> str:
    return mapping.pattern.sub(mapping.target_form, definition, count=1)


def canonical_table_signature(table: SqlTable) -> Dict[str, Any]:
    return {
        "table": table.name.lower(),
        "columns": [
            {
                "name": c.name.lower(),
                "constructs": sorted(c.constructs),
                "nullable": "NOT NULL" not in c.constraints.upper(),
            }
            for c in table.columns
        ],
    }
