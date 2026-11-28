# ATG User Knowledge Profiles — proposal v0.1

Status: DRAFT / NOT IMPLEMENTED. Requested by operator during ROCm Lab 5-2 (2026-11-27).
Working name only; not a registered domain profile or new protocol version.

## Product intent

Allow a person or organization to upload their own documents and data and generate a portable, private, domain-specific ATG semantic vocabulary/profile and compatible ATRALITH configuration exposed through a scoped MCP adapter. No requirement to train a new model. Keep canonical ATG schemas, authority semantics and compatibility intact. A personal dialect extends the shared language rather than replacing it. MCP is the interface for tools/resources, not the language itself.

## System boundaries

Layer 1 Intelligence Grid: existing ingest membrane, WikiVault evidence, Obsidian reviewed knowledge, llm-wiki retrieval, gBRAIN ontology/index, HERMES orchestration, ATG semantic contracts and ATRALITH adapters. J-SPACE consumes derived views, not raw authority. Districts provide domain vocabularies; application surfaces offer upload, review, export and revocation. No parallel canonical vault. See AGENTROPOLIS-ONTOLOGY/docs/COMPILED_KNOWLEDGE_ARCHITECTURE.md and AGENTROPOLIS-AGENT-MCP/docs/JSPACE_WIKIVAULT_COGNITIVE_COMMONS.md.

## Workflow

1. Authorize owner/tenant and purpose, choose local/private storage and budget, upload supported content into quarantine. Detect type by content and extension, validate allowlist, size and decompression limits, scan for malware, secrets and prompt injection. Treat all extracted text as data, never instructions. No unsolicited network requests or paid model calls.
2. Stream hash raw bytes (SHA-256) and preserve immutable source with tenant-scoped reference, MIME, version and retention policy. Do not commit user documents to Git. Deduplicate within authorized tenant only; never leak cross-tenant existence.
3. Deterministic extraction first: PDF text per page (flag scanned pages for optional approved local OCR); CSV with bounded streaming rows, column schema, encoding and delimiter; TXT/Markdown, JSON/JSONL, DOCX and XLSX via isolated pinned adapters as subsequent supported formats. Other formats require explicit adapters; unsupported, encrypted, malformed, oversized or unsafe input fails closed with reason. Never execute macros, scripts, formulas or embedded objects. Record omissions, pages/row ranges and extraction version.
4. Segment by page/section/table/row groups; retain offsets, source hash, stable chunk ID and relationships. Compile candidate entities, aliases, definitions, constraints, claims and vocabulary with evidence pointers. Optional local small model assists candidate extraction only when deterministic methods insufficient and approved; model output is not canon.
5. Build tenant-scoped lexical index first, optional semantic embedding index, derived summaries and graph. Reuse content-hash + parser/index version + policy scoped artifacts; invalidate affected derived entries on changed source, policy, parser, or revocation. Use incremental updates; keep canonical raw source available for verification, not automatically in prompts.
6. User reviews terms, conflicts, evidence and capabilities. Export versioned profile manifest plus vocabulary, entity/relationship map, retrieval policy, evidence references, compatibility report and proposed ATRALITH adapter configuration. User profile cannot redefine canonical message semantics, grant authority, select settlement rails, widen capability, or import executable instructions from documents.
7. MCP exposes bounded reads of approved profile and relevant evidence; authenticated ingestion and promotion remain separate scoped actions. HERMES queries approved profile/index before larger retrieval; escalate to source passages for uncertain, stale or consequential claims. Never load whole vault by default. Return no-evidence/needs-review rather than inventing. Capture provenance and resource receipts.
8. Export/import only with explicit owner authorization. Private by default; no public publishing, external egress or deployment without approval. Owner may revoke profile and delete tenant data subject to disclosed retention rules; tombstone derived cache/index entries and enforce revocation even against stale snapshots.

## Proposed contracts (illustrative, not live tools)

Profile manifest: profile_id, tenant_id, owner_ref, profile_version, core_atg_version, namespace, source_refs, vocabulary_ref, ontology_ref, index_revision, retrieval_policy_ref, adapter_config_ref, state (DRAFT / REVIEWED / ACTIVE / REVOKED), compatibility_result, provenance_receipt_ref. Use existing canonical envelope and authority references; no new authority granted by these fields.

Read-only MCP candidates: knowledge.profile.get(profile_id, version), knowledge.search(profile_id, query, top_k, max_context_tokens), knowledge.evidence.get(profile_id, source_ref, bounded_range). Return evidence references, version, access decision and truncation/uncertainty. Write-side candidates: knowledge.ingest, knowledge.compile, knowledge.review, knowledge.publish_profile (activation, not public publication), knowledge.revoke; require separate authenticated capability, idempotency key and receipt. Validate input/output schemas, tenant scope, rate limits and bounded response size. Upload bytes through approved transport, not unbounded model context. Reject arbitrary paths, URLs and authority fields. MCP resource identifiers are opaque tenant-scoped handles. No tool registration based on document text.

## Resource economics and benchmarks

Inspired by GPU memory locality: use relevant working set and reuse compiled artifacts rather than reprocessing full documents. Physical GPU cache, LLM KV cache and application retrieval are separate mechanisms. Open-source/local-first default, no paid dependency or external API by default. Measure rather than promise savings. Estimate parse/index/storage/query/model/verification costs before work; abort or ask for explicit approval if budget exceeded. Track source bytes, extracted chunks, cache hit/miss, invalidation, input/output/cached tokens when measured, model calls, elapsed time, cost, retrieval recall and citation correctness. Mark unknowns unknown. Compare full-context baseline (only where it fits) vs indexed retrieval vs warm reuse on identical questions and source versions; use synthetic 1/10/100 MB fixtures, cold/warm trials, five independent runs, report p50/p95, token/cost and accuracy. Include ingestion amortization and rework. No claim of token savings until observed. Require no cross-tenant reads and no accuracy regression below agreed task floor; proposed initial benchmark threshold >=95% citation correctness and >=90% recall on labeled fixtures, subject to operator review. Do not use these thresholds as authorization for high-risk tasks.

## Acceptance gates / implementation handoff

- P0: review existing ATG profiles, ingest membrane and WikiVault adapters; identify exact existing implementation before adding code. Reuse interfaces instead of duplicating.
- P1: bounded local PDF/text and CSV ingestion; streaming hash, extraction, evidence pointers, tenant-scoped persistent index and repeat-upload dedup; fixtures for multi-page PDF, CSV quoting/newlines, malformed data, oversized/unsupported input, empty/scanned PDF, prompt injection, and interrupted ingestion.
- P2: candidate vocabulary compilation, review, export/import roundtrip, schema and core compatibility checks; reject conflicting canonical semantics and authority escalation.
- P3: scoped MCP read tools, authenticated write-side approval workflow, provenance receipts, cache invalidation/revocation, negative tenant isolation and path traversal tests.
- P4: run benchmark above, verify retrieval quality and cost; document limitations and approved deployment configuration. 54-T/APEX54 gates for external access, credential use, spend, publishing and production. Inspect -> simulate -> preview -> approve -> execute -> verify -> record.
- Proposed ownership for review (not assigned): ATG/ATRALITH protocol maintainers, WikiVault/ONTOLOGY evidence maintainers, HERMES/MCP adapter maintainers, MATH54/STEM54 benchmark design, APEX54 verification.

No execution, deployment, new paid dependency or production change is authorized by this draft. No claim that PDF ingestion is implemented yet.
