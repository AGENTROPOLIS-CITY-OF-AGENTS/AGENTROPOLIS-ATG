# AGENT-ENTITY Canonical Naming — Migration Inventory

Status: INVENTORY (migration requirements documented; no blind breakage)

## Canonical name

The canonical name is **AGENT-ENTITY** (hyphenated).

NOT:
- `AGENTENTITY`
- `AEP`
- `Agent Entity Protocol`

## Rule

Use `AGENT-ENTITY` throughout all NEW human-facing architecture,
documentation, comments, diagrams, interfaces, and schemas where naming
permits. Do not blindly break legacy compatibility identifiers. Inventory them
and document migration requirements.

## Inventory (measured across the economic corridor, 2026-09-19)

| Repository | `AGENT-ENTITY` | `AGENTENTITY` (legacy) | Migration |
|---|---|---|---|
| AGENTROPOLIS-ATG | 11 | 0 | canonical already |
| AGENTROPOLIS-FISCALITH | 0 | 2 | migrate docs |
| AGENTROPOLIS-PAYRAIL | 9 | 4 | migrate docs |
| AGENTROPOLIS-AGENT-ENTITY-FORGE | 7 | 6 | migrate docs + schema refs |
| AGENTROPOLIS-AEGIS-ASSURANCE | 3 | 0 | canonical already |
| AGENTROPOLIS-AQUADUCT | 0 | 0 | n/a |
| AGENTROPOLIS-ARC | 9 | 0 | canonical already |

No occurrence of `AEP` or `Agent Entity Protocol` was found in the corridor.

## Migration requirements

1. **New artifacts** (docs, comments, diagrams, interfaces, schemas): use
   `AGENT-ENTITY` exclusively.
2. **Legacy `AGENTENTITY`** in documentation: migrate to `AGENT-ENTITY` in the
   owning repo's next documentation pass. Low risk (prose/heading only).
3. **Legacy `AGENTENTITY` in schemas / identifiers**: do NOT rename blindly.
   A schema `$id`, enum value, or JSON key that is already referenced by
   consumers is a compatibility identifier. Renaming it is a breaking change
   that requires a version bump and a migration note. Inventory each occurrence
   before touching it.
4. **Code identifiers** (class names, function names, variables): renaming is a
   source-compatibility break. Prefer additive aliases
   (`AGENT_ENTITY = AGENTENTITY`) over silent renames, and document the
   deprecation window.
5. **Cross-repo references**: a rename in one repo must be coordinated with
   every consumer repo. Do not rename a shared identifier in isolation.

## Current state

The canonical `AGENT-ENTITY` is already the dominant form across the corridor.
The remaining `AGENTENTITY` occurrences are documentation-level in FISCALITH,
PAYRAIL, and FORGE, plus schema/identifier references in FORGE that must be
handled as compatibility identifiers (versioned migration, not blind rename).

## Standing rule

> AGENT-ENTITY defines the actor. ATG defines the meaning. FISCALITH defines
> the money. AEGIS decides. AQUADUCT proves. PAYRAIL routes. Receipts prove
> what happened.
