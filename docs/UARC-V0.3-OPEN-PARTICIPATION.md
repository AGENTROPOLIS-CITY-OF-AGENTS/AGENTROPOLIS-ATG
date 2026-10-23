# UARC v0.3 — Universal Agent Runtime Contract (PROPOSAL)

Status: DRAFT / TEST ONLY. Not production authority.

## Purpose
UARC is a vendor-neutral description and negotiation contract for agents, models, runtimes, devices, fleets, tools and future unknown participant types. It is not a replacement for existing BYOE/BYOH policies or a universal executor.

## Existing canon and ownership
- Builder Commons BYOE means **Bring Your Own Environment**; see AGENTROPOLIS-BUILDER-COMMONS/docs/BYOE.md.
- Docking District BYOE means **Bring Your Own Everything**; see AGENTROPOLIS-DOCK/docs/byoe-framework.md.
- BYOH means Bring Your Own Hardware; see PUBLIC-PORT-DISTRIBUTION-MEMBRANE/docs/BYOK-BYOH-CONTROL-PLANE.md.
- ATG expresses mission requirements and interoperability contracts; it does NOT own compute routing.
- Dock owns admission, provenance, capability handles and revocation. BE evaluates applicable executable/model/runtime integrations; 54T enforces security boundaries; AEGIS governs policy; Builder Commons brokers user-owned compute.
- Existing registry, schema and execution contracts prevail until reviewed migration explicitly approves compatibility.

## Invariants
1. Presentation is not identity; registration is not authentication; connectivity is not authority.
2. Installed != loaded != live != authorized. Unverified capability claims never become executable grants.
3. Default deny. No agent can approve its own consequential actions.
4. External participants retain ownership; AGENTROPOLIS only brokers scoped, revocable capabilities.
5. Secrets never enter prompts, logs or agent memory.
6. Offline mandates never silently route to cloud; unknown/untrusted execution is sandboxed.
7. Every material action requires traceable receipt and audit; offboarding revokes handles and verifies denial.
8. Unknown vendor, architecture or protocol is representable, not automatically supported.
9. Fallback requires equivalent authorization, data constraints and cost ceiling; otherwise queue or human review.
10. Runtime adapters may translate formats but must not expand grants.

## Participation classes
agent, model, runtime, hardware, fleet, tool, service, hybrid, unknown. These are descriptive categories, not permissions.

## Enrollment flow
Discovery -> owner and identity verification -> provenance -> capabilities claimed -> Dock/54T/BE assessment as applicable -> adapter negotiation -> sandbox/canary -> verified capabilities -> scoped handle -> mandate -> execution -> receipt -> audit -> revoke/offboard.

## Contract boundaries
- ExternalParticipant: stable participant identity, owner, tenant, class, provenance and lifecycle.
- HardwareProfile: architecture, OS, resources, trust/attestation state, connectivity and locality.
- RuntimeAdapter: transport, compatibility version, isolation and cancellation support.
- CapabilityManifest: claimed vs verified capabilities, scope, evidence and constraints.
- Extension namespaces: vendor.*, community.*, experimental.*; extensions cannot override governance fields.

## Reference fleet (NOT presumed integrated)
Devin, Hermes, Nemotron models, NemoClaw, GrokBot fleet, Muse, VERITY, Dots, Codex, third-party agents, user-built devices and future unknown agents. Each requires its own capability and authorization evidence.

## Acceptance gates
- Schema accepts unknown participant and hardware types without allowing unknown permissions.
- Tests reject self-authorization, undeclared egress, missing provenance and missing receipt.
- Dock registry compatibility and BYOE terminology review.
- BYOH local-first and offline no-cloud regression checks.
- Permission revocation denies subsequent calls.
- Cross-tenant isolation, budget ceilings and adapter failure closed.
- Independent VERITY review and human authorization before promotion.

## Proposed integration
ATG owns this portable contract; Dock maps it to existing byoe-capability schema and registry; AGENT-MCP owns protocol adapters; Builder Commons owns BYOE compute brokerage; 54T/AEGIS own security and policy gates. No existing execution path changes in this proposal.
