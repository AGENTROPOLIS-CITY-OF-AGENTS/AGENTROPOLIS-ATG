# ATG as Layer-1 semantic infrastructure

ATG is the canonical semantic language of Agentropolis. Agents do not translate
to one another when semantics matter: they emit a canonical **semantic
envelope**, and every downstream transform is a function over that envelope.

```
SOURCE (human text | code | schema | API)
  -> atg.parse        -> canonical envelope
  -> atg.normalize    -> canonical + core signatures
  -> atg.translate.*  -> target representation
  -> atg.validate     -> reverse-parse comparison, fail-closed
  -> atg.provenance   -> lineage, pack versions, confidence
```

## Layers

| Layer | Owns | In this repo |
| --- | --- | --- |
| ATG | language + semantic bridge | `packages/atg-core`, `packages/atg-mcp` |
| Ontology | shared meaning and relations | `packages/atg-ontology-adapter` (seam) |
| Intelligence Grid | who should reason | `packages/atg-router-adapter` (seam) |
| Utility Grid | tools, resources, compute | `packages/atg-utility-adapter` (seam) |
| Governance | what is allowed | jurisdiction rules in packs + escalation policy |
| Provenance | what happened and why | `atg_core.provenance`, envelope transformations |

The adapters are protocols plus reference implementations. No vendor is named
anywhere in the core; router tiers (`deterministic`, `local`, `frontier`,
`human`) are names a deployment binds to its own providers.

## Canonical types

- **Context vector** (`schemas/atg/context-vector.schema.json`): language,
  locale, region, jurisdiction, industry, profession, role,
  programming_language, programming_dialect, framework, runtime, platform,
  architecture, standards[], regulations[], units, currency, audience,
  output_medium.
- **Semantic envelope** (`schemas/atg/semantic-envelope.schema.json`):
  atg_version, message_id, source/target endpoints, intent, entities,
  relations, constraints, contracts, assumptions, unknowns, provenance
  (sources + transformations), confidence, semantic_equivalence,
  roundtrip_score, requires_escalation.

Two hashes are exposed, and the difference matters:

- `canonical_hash()` — full meaning **including** region-derived execution
  constraints. Two locales of the same sentence differ here, because what must
  be enforced differs.
- `core_hash()` — meaning with `region:`-originated constraints removed. This
  is the locale-independent intent identity used to prove that US and UK
  English normalise to the same request.

## MCP surface

`packages/atg-mcp` serves twelve tools over JSON-RPC stdio with no vendor SDK:

`atg.parse`, `atg.normalize`, `atg.context.resolve`, `atg.translate.human`,
`atg.translate.domain`, `atg.translate.code`, `atg.localize`, `atg.validate`,
`atg.roundtrip`, `atg.explain_mapping`, `atg.pack.resolve`, `atg.provenance`.

```bash
python -m atg_mcp.server   # stdio MCP server
```

Tool contracts are declared as data (`atg_mcp.tools.TOOL_CONTRACTS`) and bound
to plain callables, so the same contracts can be hosted over another transport
or invoked in-process with `call_tool(name, arguments)`. No contract references
a pack implementation; packs are resolved at call time.

## Domain packs

Packs are versioned YAML data loaded by `atg_core.packs.PackRegistry`. Adding a
pack never changes an MCP contract. Every pack declares `lexicon`, `entities`,
`relationships`, `industry_codes`, `standards`, `authorities`, `documents`,
`workflows`, `roles`, `abbreviations`, `synonyms`, `jurisdiction_rules`,
`source_mappings`, `translation_rules`.

Shipped: `COMMON` (locale variants and deliberate ambiguities), `TECH`, `TAX`,
`REAL_ESTATE`, `LEGAL`, `FILM`.

Ambiguity is resolved only when exactly one *active domain* pack claims a
candidate concept; COMMON never resolves its own ambiguity. Two domain
candidates stay ambiguous and escalate.

## Code as a first-class ATG language

Code is translated through a behavioural IR (`atg_core.code.ir`), never by
token substitution. A construct with no proven IR equivalent raises
`UnsupportedConstruct`, which becomes a blocking unknown rather than a guess.

Registered: Python, TypeScript/JavaScript, Rust (registered, no emitter —
escalates), SQL (`postgresql`, `mysql`, `sqlite`, `sqlserver`), shell (`sh`,
`bash`, `zsh`, `powershell`), JSON/YAML/schema, REST/GraphQL/OpenAPI.

Worked divergences:

- Python `int` -> TypeScript `number` records IEEE-754 widening.
- PostgreSQL `JSONB`/`TIMESTAMPTZ` -> SQLite `TEXT` is marked non-equivalent
  and escalates; emitted SQLite DDL is executable and carries `-- atg:` rule
  annotations after the structural comma.
- PowerShell is an object pipeline; POSIX shells are byte pipelines. Exit
  status, globbing and word splitting divergences are recorded explicitly.

## Region is execution context

`atg_core.regions` carries, per region: default locale/language, jurisdiction,
units, currency, date/number/address format, regulations, standards, data
residency, tax regime, tax authorities and restricted services. `atg.localize`
reports exactly which execution fields changed, and appends `region:`-origin
constraints to the envelope. Region is never inferred for high-impact domains:
a TAX or LEGAL context without a jurisdiction is a blocking unknown.

## Validation

`atg.roundtrip` runs SOURCE -> ATG -> TARGET -> reverse ATG -> compare, and
`atg.validate` compares intent, concepts, contract signatures (canonicalised
across naming conventions and numeric widths), errors, behaviour signatures,
authorities and jurisdiction. Material drift fails closed: `passed=False`,
semantic equivalence below threshold, `requires_escalation=True`.

## Evidence packets

`build_evidence_packet` reduces a large raw document to concept-bearing claims
with source spans, retained constraints, open questions, pack versions and
confidence — the input a frontier model should receive instead of raw context.

## Running

```bash
python -m pytest tests -q
```

Tests are grouped as: `test_acceptance.py` (the ten acceptance criteria),
`test_packs.py`, `test_mcp_tools.py`, `test_adapters.py`, `test_schemas.py`.
