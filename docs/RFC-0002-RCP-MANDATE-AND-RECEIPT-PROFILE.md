# RFC-0002: RCP Mandate and Receipt Profile

Status: Draft 0.1  
Protocol dependency: `rcp/0.1-draft`  
RCP authority: `wiredchaos/AGENTROPOLIS-CREATOR`  
ATG authority: `wiredchaos/AGENTROPOLIS-ATG`

## Purpose

This profile defines how Agent Transaction Grammar messages authorize, transport, and record Reality Construction Protocol work.

RCP describes what a governed world package contains. ATG describes who may request each construction action, under which authority, with what evidence, and which receipt must be returned.

## Construction corridor

```text
identity
  -> construction mandate
  -> plan
  -> sandbox build
  -> audit
  -> repair proposal
  -> human approval
  -> release receipt
```

No stage inherits authority merely because an earlier stage succeeded.

## Message types

- `atg.rcp.mandate.create`
- `atg.rcp.plan.propose`
- `atg.rcp.compile.request`
- `atg.rcp.audit.request`
- `atg.rcp.repair.propose`
- `atg.rcp.release.propose`
- `atg.rcp.release.approve`
- `atg.rcp.rollback.request`
- `atg.rcp.receipt.issue`

## Authority scopes

| Scope | Permitted action |
|---|---|
| `rcp.read` | Inspect packages, schemas, profiles and receipts |
| `rcp.plan` | Produce plans and inferred decision ledgers |
| `rcp.build.sandbox` | Compile geometry and runtime artifacts in an isolated environment |
| `rcp.audit` | Execute read-only tests and produce findings |
| `rcp.repair.sandbox` | Apply bounded repairs to an unreleased sandbox build |
| `rcp.release.propose` | Submit a reviewed build for approval |
| `rcp.release.approve` | Approve a specific immutable artifact digest |
| `rcp.rollback` | Repoint release state to a previously approved artifact |
| `rcp.physical.actuate` | Separate high-risk authority; never implied by another RCP scope |

## Construction mandate

```json
{
  "type": "atg.rcp.mandate.create",
  "version": "0.1",
  "mandate_id": "mandate_rcp_...",
  "actor": {
    "id": "agent-or-human-id",
    "kind": "human|agent|service"
  },
  "target": {
    "world_id": "agentropolis.city.core",
    "package_version": "0.1.0-draft"
  },
  "authority": {
    "scopes": ["rcp.plan", "rcp.build.sandbox", "rcp.audit"],
    "denied_scopes": ["rcp.release.approve", "rcp.physical.actuate"],
    "expires_at": "2026-08-03T00:00:00Z",
    "budget": {
      "max_compute_seconds": 3600,
      "max_cost_usd": 25,
      "max_repairs": 3
    }
  },
  "constraints": {
    "source_rights_required": true,
    "human_review_required": true,
    "network_mode": "deny_by_default",
    "allowed_targets": ["threejs-webgpu"],
    "protected_paths": ["identity", "authority", "provenance"]
  },
  "evidence_requirements": [
    "world_package_digest",
    "schema_validation",
    "audit_report",
    "artifact_manifest"
  ]
}
```

## Receipt envelope

Every RCP stage returns an ATG receipt envelope.

```json
{
  "type": "atg.rcp.receipt.issue",
  "version": "0.1",
  "receipt_id": "rcpt_rcp_...",
  "mandate_id": "mandate_rcp_...",
  "stage": "compile|audit|repair|release|rollback",
  "decision": "allowed|blocked|failed|completed|approved",
  "authority_scope_used": "rcp.build.sandbox",
  "inputs": {
    "world_package_digest": "sha256:...",
    "source_digests": []
  },
  "outputs": {
    "artifact_manifest_digest": "sha256:...",
    "audit_report_digest": null
  },
  "controls": {
    "sandboxed": true,
    "human_reviewed": false,
    "inferred_defaults_recorded": true,
    "physical_actuation": false
  },
  "timing": {
    "started_at": "...",
    "completed_at": "..."
  },
  "issuer": {
    "service": "...",
    "version": "..."
  }
}
```

## Release approval binding

A release approval MUST bind all of the following:

1. World identifier and package version.
2. World Package digest.
3. Artifact manifest digest.
4. Audit report digest.
5. Runtime target and renderer version.
6. Rights and provenance state.
7. Named approving identity.
8. Expiration or revocation policy when applicable.

Approval of a preview, screenshot, prompt, mutable branch, or human-readable title alone is invalid.

## Mandatory denials

An ATG implementation MUST block the request when:

- the requested scope is absent or expired;
- the package digest differs from the reviewed package;
- protected authority or provenance fields were modified during repair;
- rights state is unknown for release-bound assets;
- required audit evidence is missing;
- a sandbox mandate attempts external publication;
- physical actuation is requested without the separate scope and corridor;
- an agent attempts to approve its own release without explicit delegated authority.

## Receipt sequence

```text
construction_receipt
  -> audit_receipt
  -> optional repair_receipt(s)
  -> release_proposal_receipt
  -> human approval
  -> release_receipt
```

A later receipt references earlier receipt identifiers and digests. It does not overwrite them.

## Compatibility

This draft is implementation-neutral. MCP servers, local agents, Cloudflare Workers, game engines, Blender tools, build systems, and robotics simulators may carry the profile, but none may broaden its authority semantics.

## Security doctrine

Authority is not a prompt. It is a runtime constraint.

World generation stamina is not release authority. A model may construct, inspect, and propose. Consequential publication, economic mutation, identity changes, destructive operations, and physical actuation remain separately authorized actions.
