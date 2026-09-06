# Extraction boundaries, mirror targets and repo access

## Repo access status (verified this run)

The prior 403s did not reproduce. Read/write access was confirmed by listing
remote heads on each repository:

| Repository | Status |
| --- | --- |
| `AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-ATG` | accessible — **this work landed here** |
| `AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-ONTOLOGY` | accessible |
| `AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-UTILITY-GRID` | accessible |
| `AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-AGENT-MCP` | accessible |
| `AGENTROPOLIS-CITY-OF-AGENTS/agentropolis` | accessible (shared repo, fallback not needed) |

Because the dedicated ATG repository was reachable, the core landed in its
canonical home instead of the shared-repo fallback. No blockers remain to
propagate the adapter seams outward.

## Extraction boundaries

Every package below is import-clean: it depends only on `atg_core` public API
plus the standard library and PyYAML. Nothing imports across sibling adapters,
and no adapter is referenced by `atg_core`. Extraction is therefore a directory
move plus a dependency declaration on `atg-core`.

| Source in this repo | Mirror target | Notes |
| --- | --- | --- |
| `packages/atg-core/` | stays in `AGENTROPOLIS-ATG` | canonical language, published as `atg-core` |
| `packages/atg-mcp/` | `AGENTROPOLIS-AGENT-MCP` → `servers/atg/` | depends on `atg-core` only; twelve tool contracts are data, transport is replaceable |
| `packages/atg-ontology-adapter/` | `AGENTROPOLIS-ONTOLOGY` → `adapters/atg/` | replace `PackOntologyAdapter` with the real graph store; keep the `OntologyAdapter` protocol as the contract |
| `packages/atg-utility-adapter/` | `AGENTROPOLIS-UTILITY-GRID` → `adapters/atg/` | replace `StaticUtilityGridAdapter` with the live capability catalogue; region/residency/restricted-service filtering semantics must be preserved |
| `packages/atg-router-adapter/` | `AGENTROPOLIS-CITY` (Intelligence Grid) → `adapters/atg/` | tier names are abstract; a deployment binds them to providers |
| `packages/atg-packs-*/` | may split per domain (e.g. FILM → `AGENTROPOLIS-FILM-DISTRICT`) | packs are pure YAML data; the registry loads any directory containing `pack.yaml` |
| `schemas/atg/` | mirror read-only into consumers | schema `$id`s are absolute URLs and are the versioning surface |

### Contract stability rules for the split

1. MCP tool input/output schemas must not encode pack identity or pack version;
   packs are resolved at call time from the context vector.
2. Adding, versioning or removing a pack must never require an MCP contract
   change. `atg.pack.resolve` is the only tool that names packs, and it names
   them as data.
3. Adapters are protocols first. A consumer repo may replace the reference
   implementation, but changing the protocol is an ATG-level change and belongs
   in this repo.
4. `atg_core` must never import an adapter. If core needs a capability, the
   caller injects it.

## Publishing sequence

1. Tag `atg-core` in this repo (`ATG_VERSION` / `ATG_CORE_VERSION` in
   `packages/atg-core/atg_core/version.py`).
2. Mirror `schemas/atg/` into consumers as read-only artefacts.
3. Move each adapter directory to its target repo, adding a dependency on the
   tagged `atg-core`; keep the tests that assert the protocol.
4. Move `packages/atg-mcp` into `AGENTROPOLIS-AGENT-MCP` and register the
   server in that repo's MCP manifest.
5. Delete the moved directories here only once the mirrors are green; until
   then this repo remains the source of truth.
