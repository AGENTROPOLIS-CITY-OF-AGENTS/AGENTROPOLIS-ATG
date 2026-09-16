# Hermes Execution Envelope Profile

ATG compiles Hermes-targeted work into the same governed Execution Envelope used by other AGENTROPOLIS runtimes.

Hermes is a capability runtime and plugin host. It does not become the AGENTROPOLIS policy authority. Identity, mandate, routing, risk, approval, receipt, and audit remain governed above the runtime.

## Required compiled fields
- citizen_id / mandate_ref / risk_tier
- execution_mode: attended | unattended
- runtime_profile / runtime_address
- requested_route / effective_route
- runtime_route_snapshot
- capability_epoch / toolset_fingerprint
- plugin_name / plugin_repo / plugin_sha when a Hermes plugin is used
- plugin_capability_fingerprint
- plugin_assurance_receipt_ref
- operation-level capability grants
- approval_request_id + action_digest where required
- occurrence_id for scheduled work
- delegation_id / completion-unit identity for delegated work
- artifact egress classification
- receipt/audit correlation

## Compile-time invariants
- Hermes transport cannot grant authority.
- Hermes catalog presence cannot grant AGENTROPOLIS authority.
- Provider/model selection cannot expand capability.
- Runtime/profile transitions cannot inherit ambient credentials.
- A plugin may expose only the capability set admitted by the Execution Envelope.
- A plugin update, SHA change, capability declaration change, or material dependency change creates a new capability epoch.
- Unattended durable memory replace/remove requires approval.
- Delegation attenuates authority on every hop.
- Consequential scheduled effects are idempotent by occurrence_id.
- Delivery success and execution success are independent states.
- Capability/plugin revision changes create a new epoch.

## Hermes plugin compilation

When ATG selects a Hermes plugin, it must compile a plugin binding rather than passing through an unbounded plugin install.

```text
Intent
  -> Skill/Capability Registry match
  -> plugin provenance resolution
  -> Sentinel/AEGIS assurance state
  -> risk tier
  -> operation grants
  -> credential scope
  -> approval requirements
  -> Execution Envelope
  -> Hermes plugin invocation
  -> receipt
```

The plugin binding should preserve:
- exact repository and pinned commit SHA
- catalog tier/source
- declared tools, hooks, middleware, and required environment variables
- district ownership and approved use cases
- platform constraints
- credential class without secret values
- read/write/network/process/filesystem/device scope
- expected artifacts and egress class
- rollback or disable path

## Capability Packs

AGENTROPOLIS may define District Capability Packs that map approved Hermes plugins to district-owned workflows. A pack is a governed selection profile, not a blanket permission grant.

Examples:
- Voice Gateway Pack
- 789 / Neteru Media Pack
- 54.TAILORS Pack
- Gaming District Pack
- Continuity / Memory Pack
- Business Operations Pack
- Sentinel / 54T Security Pack

Each pack resolves into explicit plugin bindings inside the Execution Envelope. Installing a pack never bypasses plugin-level assurance.

## Receipt requirements

For every plugin-backed consequential action, record at minimum:
- plugin name and pinned SHA
- capability epoch
- granted operation set
- runtime profile
- approval reference when required
- execution result
- produced artifacts
- external writes/effects
- errors and denied operations
- start/end timestamps
- receipt correlation ID

## Runtime portability
These fields are semantic AGENTROPOLIS contracts. Hermes-specific wire details remain in the Hermes adapter so NemoClaw/Nemotron, Devin, and future runtimes can implement the same envelope without changing governance.
