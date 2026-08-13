# RFC-0004: HERMES Chief-of-Staff Operating Contracts

Status: Draft

## Abstract

This RFC defines five implementation-neutral ATG contracts for persistent agentic operations: Goal Contract, Work Item, Brand Pack, Autonomy Policy, and Capability Handle. Together they let a coordinator such as HERMES convert human intent into bounded work, dispatch specialists, preserve portable work state, apply brand constraints, graduate autonomy, and use credentials without exposing raw secrets.

The coordinator is not sovereign authority. User intent is not execution authority. These contracts compose with RFC-0001 Trusted Authorization Path and existing ATG mandate and receipt semantics.

## 1. Design doctrine

The operating loop is:

```text
Intent
  -> Goal Contract
  -> Work Graph
  -> Minimum Necessary Capability Selection
  -> District / Specialist Dispatch
  -> Delta Observation
  -> Approval When Required
  -> Execution
  -> Verification
  -> Evidence + Receipt
  -> Memory Update
  -> Operator Report
```

Normative rules:

1. A goal MUST define measurable completion criteria before autonomous execution can claim completion.
2. A coordinator MAY propose work but MUST NOT silently expand its own authority.
3. External-effect actions MUST satisfy the applicable RFC-0001 A0-A4 authorization class in addition to any autonomy policy.
4. Raw production secrets SHOULD NOT be placed into model context when an opaque capability handle can be used.
5. Work state MUST remain portable across project systems such as Linear, GitHub Issues, Jira, Airtable, or local stores.
6. Brand context SHOULD be loaded as the minimum necessary versioned Brand Pack rather than as an unbounded prompt corpus.
7. Durable receipts SHOULD connect consequential work to goal, mandate, policy, capability, evidence, and result.

## 2. Goal Contract / GOAL-ENGINE

The Goal Contract defines the outcome, not merely a task prompt.

Required concepts:

- stable `goal_id`
- objective
- explicit definition of done
- one or more success tests
- execution constraints
- authority policy reference
- current lifecycle state

A goal MUST NOT transition to `complete` solely because an agent reports success. Required success tests must pass or an authorized human reviewer must explicitly accept the result.

Reference schema: `contracts/core/goal-contract.schema.json`.

## 3. Work Item / WORK-SPINE

The Work Item is a neutral task-state object used to build persistent work graphs without making any single project vendor constitutional infrastructure.

A Work Item may map to a Linear issue, GitHub issue, Jira ticket, Airtable record, local database row, or another adapter. The ATG object remains authoritative for protocol semantics while the external system is an implementation surface.

Reference schema: `contracts/core/work-item.schema.json`.

## 4. Brand Pack / BRAND-PACK

A Brand Pack is a versioned, portable artifact-generation contract. It carries only the brand context required for the current artifact class.

It may include typography, palette, logo rules, visual language, image-generation rules, artifact templates, accessibility requirements, and forbidden patterns. Provenance references SHOULD identify the approved source material.

A coordinator SHOULD resolve `brand_id` and load the smallest applicable Brand Pack before delegating to an artifact generator.

Reference schema: `contracts/core/brand-pack.schema.json`.

## 5. Autonomy Policy / AUTHORITY-LADDER

Autonomy and authorization are distinct.

RFC-0001 authorization classes answer: **what authorization path is required for this action?**

RFC-0004 autonomy levels answer: **how far may this agent proceed without requesting a new human decision?**

The levels are:

- `L0_READ_ONLY` - inspect only
- `L1_DRAFT` - prepare proposed output but do not transmit or mutate
- `L2_HUMAN_APPROVAL` - execution only after explicit human approval
- `L3_BOUNDED_AUTOMATION` - automatic execution for narrowly pre-approved action classes
- `L4_DELEGATED_BOUNDED` - broader delegated execution inside explicit recipients, systems, value, time, and policy limits
- `L5_EXECUTIVE_DELEGATED` - rare executive delegation; still bounded by mandate, authorization class, policy, and receipts

No autonomy level overrides A0-A4 authorization requirements. A high autonomy level with insufficient authorization MUST fail closed.

Reference schema: `contracts/core/autonomy-policy.schema.json`.

## 6. Capability Handle / CREDENTIAL-BROKER

A Capability Handle is an opaque, revocable reference such as:

```text
cap://github/repo-write/AGENTROPOLIS
```

The handle identifies allowed capability and scope without exposing the underlying credential to the agent. A broker or trusted execution component resolves the handle only at execution time.

Handles SHOULD support:

- least privilege
- expiration
- revocation
- resource constraints
- policy binding
- non-exportable secrets where supported
- 54-T effective-capability verification in AGENTROPOLIS deployments

Reference schema: `contracts/core/capability-handle.schema.json`.

## 7. HERMES reference profile

Inside AGENTROPOLIS, HERMES is the operator and coordinator surface, not the sovereign brain of the system.

A recommended HERMES execution profile is:

```text
Operator
  -> HERMES
  -> Goal Contract
  -> Intelligence Grid
  -> Work Spine
  -> District / Specialist Agent
  -> Scoped Capability Handle
  -> RFC-0001 Authorization Envelope
  -> Execution
  -> Verification
  -> Receipt
```

AGENTROPOLIS-specific governance may additionally use 54-T for effective capability verification, WikiVault for evidence provenance, Quantization Torque for context allocation, CONTRA for adversarial claim validation, gBRAIN as a rebuildable derived graph/index, and Obsidian as a governed human-readable knowledge surface. Those components are an AGENTROPOLIS profile, not dependencies required for independent ATG adoption.

## 8. Minimum Necessary Cognition

A compliant implementation SHOULD minimize the capability and context surface before inference or execution.

Recommended pattern:

```text
scripts detect -> coordinator investigates
full evidence persists -> model receives relevant delta
```

Fixed-format watchdogs, thresholds, and deterministic state comparisons SHOULD run without an LLM when practical. The coordinator should wake on meaningful normalized state changes rather than continuously re-reading full histories.

## 9. Completion and receipts

For consequential goals, the final receipt SHOULD identify:

- `goal_id`
- relevant `work_id` values
- mandate hash
- autonomy policy
- authorization class
- capability handles used
- success tests and verification outcome
- evidence references
- produced artifacts
- execution result

## 10. Security considerations

Key risks include prompt-injected goal expansion, project-system state poisoning, privilege drift, credential exposure, silent autonomy escalation, false completion claims, and third-party impact.

Implementations SHOULD:

- fail closed on policy ambiguity
- bind execution to stable goal and mandate identifiers
- prevent agents from rewriting their own authority policies
- independently verify effective capability scope
- require explicit review for destructive or irreversible actions
- record policy and execution receipts
- keep raw secrets outside model context when possible

## 11. Schemas

This RFC introduces:

- `contracts/core/goal-contract.schema.json`
- `contracts/core/work-item.schema.json`
- `contracts/core/brand-pack.schema.json`
- `contracts/core/autonomy-policy.schema.json`
- `contracts/core/capability-handle.schema.json`

## 12. Non-goals

This RFC does not mandate HERMES, Linear, Slack, OAuth, Tailscale, Obsidian, or any single model provider. Those are replaceable implementation choices or profile components.
