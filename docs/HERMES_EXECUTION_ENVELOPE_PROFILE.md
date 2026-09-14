# Hermes Execution Envelope Profile

ATG compiles Hermes-targeted work into the same governed Execution Envelope used by other AGENTROPOLIS runtimes.

## Required compiled fields
- citizen_id / mandate_ref / risk_tier
- execution_mode: attended | unattended
- runtime_profile / runtime_address
- requested_route / effective_route
- runtime_route_snapshot
- capability_epoch / toolset_fingerprint
- operation-level capability grants
- approval_request_id + action_digest where required
- occurrence_id for scheduled work
- delegation_id / completion-unit identity for delegated work
- artifact egress classification
- receipt/audit correlation

## Compile-time invariants
- Hermes transport cannot grant authority.
- Provider/model selection cannot expand capability.
- Runtime/profile transitions cannot inherit ambient credentials.
- Unattended durable memory replace/remove requires approval.
- Delegation attenuates authority on every hop.
- Consequential scheduled effects are idempotent by occurrence_id.
- Delivery success and execution success are independent states.
- Capability/plugin revision changes create a new epoch.

## Runtime portability
These fields are semantic AGENTROPOLIS contracts. Hermes-specific wire details remain in the Hermes adapter so NemoClaw/Nemotron, Devin, and future runtimes can implement the same envelope without changing governance.