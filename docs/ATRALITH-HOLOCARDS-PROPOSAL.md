# ATRALITH HoloCards — integration proposal

Status: PROPOSAL / NOT DEPLOYED

## Intent
Use Hermes draft-cards as an optional human-editing surface, while displaying ATG's existing Semantic IR and ATG LANGUAGE representation in a spatial holographic view. Do not create a competing language profile or redefine ATG semantics.

## Architecture
1. Hermes draft-cards captures editable scripts, messages and revisions; treat third-party plugin data as untrusted.
2. Adapter converts approved draft revisions into typed, versioned Semantic IR using existing ATG schemas and LANGUAGE surface. Reject unknown or ambiguous mappings.
3. Read-only HoloCards renderer displays glyphs, identity, intent, mandate, constraints, provenance, receipt links and state. Rendering never grants authority.
4. MATH54 transforms position and orientation of visual elements; no semantic mutations.
5. AEGIS/Agent MCP validate policy, destination, content version, human approval and execution envelope before any publish/send.
6. Execution adapters produce immutable receipts and audit references; UI distinguishes simulated, proposed, approved, executed and verified states.

## Security and rollout
- No automatic plugin installation or network permissions. Review upstream code, dependencies, license, desktop compatibility and data retention before installing.
- No auto-send, auto-publish, signing, wallet interaction or trading authority.
- Prevent prompt injection from card content, sanitize rendered text, prohibit HTML/script execution, and keep authorization out of visual layer.
- Phase 1: read-only 2D card + Semantic IR preview and accessibility fallback.
- Phase 2: opt-in 3D holographic visualization with performance budget and motion-reduction option.
- Phase 3: governed human approval and publication adapter after independent security review.

## Acceptance criteria
- Existing ATG LANGUAGE namespace remains canonical.
- Identical Semantic IR yields equivalent 2D and 3D meaning; no loss of evidence or authority references.
- Unapproved changes invalidate prior approval by version hash.
- Renderer cannot trigger execution; unauthorized actions fail closed.
- Tests cover injection, version drift, missing provenance, reduced motion, offline fallback and receipt reconciliation.

Upstream candidate: https://github.com/arsiktech/hermes-draft-cards
