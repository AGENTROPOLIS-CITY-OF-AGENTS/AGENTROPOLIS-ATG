# ATG:FLEET — Governed Agent Fleet Execution Profile

**Status:** proposed ATG domain profile  
**Namespace:** `ATG:FLEET`  
**Canonical owner:** AGENTROPOLIS-ATG

ATG:FLEET defines provider-neutral semantics for decomposing one authorized mandate into multiple bounded execution cells without turning concurrency, delegation, model capability, or shared infrastructure into authority.

It specializes the existing ATG corridor. It does not replace the Execution Envelope, mandate, policy, receipt, or verification contracts.

## Semantic objects

### FleetRun
A governed set of execution cells compiled from one task contract and mandate.

Required semantics:
- `run_id`
- `mandate_ref`
- `task_contract_ref`
- `execution_envelope_ref`
- `risk_decision_ref`
- `baseline_ref`
- `cell_refs`
- `integration_graph_ref`
- `budget_ref`
- `status`
- `receipt_refs`

### ExecutionCell
The smallest independently owned work unit dispatched to one runtime route.

Required semantics:
- unique `cell_id`
- parent delegation reference when nested
- repository/resource baseline
- read/write/forbidden scope
- mutation mode
- ownership lease
- capability grants
- runtime/model route
- budget and expiry
- context capsule reference
- verification requirements

### OwnershipLease
A time-bounded exclusive claim over a mutable scope. A lease is not general repository authority.

Two active mutating cells MUST NOT hold overlapping write leases unless ATG compiles an explicit serialization edge that prevents simultaneous mutation.

### BaselineSnapshot
An immutable reference to the pre-execution state used for attribution, regression comparison, and integration review.

### IntegrationEdge
A typed dependency between cells. Initial edge types:
- `DEPENDS_ON`
- `SERIALIZES_WITH`
- `INTEGRATES_INTO`
- `REVIEWS`

### ContextCapsuleRef
A reference to bounded resumable state. Context cannot add permission, credentials, budget, write scope, delegation depth, or expiry.

### VerificationReceiptRef
A reference to independent criterion-level evidence for a cell or integrated candidate.

## Compile-time rules

ATG MUST reject or escalate a proposed FleetRun when:

1. a child grant is broader than its parent grant;
2. two mutating cells have unresolved overlapping write scopes;
3. the baseline is missing for a mutating cell;
4. required integration ordering is cyclic without an explicit approved recovery plan;
5. the selected runtime requires capability outside the current envelope;
6. model/provider selection would broaden data, credential, network, or tool access;
7. an integration cell is also the sole required verifier of its own result;
8. budget, lifetime, or delegation depth exceeds the governing envelope;
9. a required approval is absent or stale;
10. a resumable context capsule conflicts with the current mandate or capability epoch.

## Delegation attenuation

For every parent `P` and child `C`:

```text
Authority(C) ⊆ Authority(P)
WriteScope(C) ⊆ WriteScope(P) or explicitly delegated sub-scope
Budget(C) ≤ remaining delegated budget(P)
Expiry(C) ≤ Expiry(P)
CredentialReach(C) ⊆ CredentialReach(P)
NetworkReach(C) ⊆ NetworkReach(P)
```

Nested orchestration may improve decomposition. It may never manufacture new authority.

## Isolation semantics

ATG:FLEET describes isolation requirements without hard-coding Git. A conforming runtime may use a git worktree, disposable checkout, VM, container, sandbox, remote workspace, or equivalent mechanism if it preserves the same observable invariants.

For source-code mutation, the preferred profile is:

```text
one execution cell
  -> one isolated mutable workspace
  -> one branch/ref lease
  -> one explicit write scope
  -> one baseline
  -> one completion receipt
```

## Baseline attribution

A worker failure is not automatically an introduced regression. When the task contract requires baseline comparison, the verification lane evaluates the relevant failing check against the recorded baseline or records why reproduction was impossible.

States should distinguish:
- `BASELINE_FAILURE`
- `INTRODUCED_FAILURE`
- `UNRESOLVED_ATTRIBUTION`
- `PASS`

## Interface preservation

Tests are not the complete compatibility boundary. A FleetRun may declare protected interfaces such as:
- public exported symbols
- MCP tools and schemas
- CLI arguments and help contracts
- configuration keys/defaults
- JSON/event/wire schemas
- database migration contracts
- plugin extension points
- environment-variable contracts

Unexpected protected-interface drift requires verification or escalation before integration.

## Routing

ATG:FLEET routes abstract capability requirements. It does not name a single privileged model or harness.

Approved workers may include Hermes, NemoClaw/Nemotron, Devin, Codex, Claude Code, local models, and future admitted runtimes. Runtime admission remains outside this profile, and provider selection never changes the envelope.

## Continuity

A FleetRun may be resumed by another admitted runtime when its Context Capsule, baseline, branch/workspace identifiers, accepted commits, unresolved checks, dependencies, and current authority epoch can be revalidated.

A resume MUST re-check:
- mandate validity
- envelope version
- capability epoch
- ownership lease validity
- baseline/ref availability
- pending approvals
- budget remaining

## Receipts

Each consequential cell emits a receipt sufficient to answer:
- what was assigned;
- what authority was granted;
- what baseline was used;
- what workspace/ref was mutated;
- which artifacts changed;
- what checks ran;
- which failures pre-existed or were introduced;
- which interfaces changed;
- which model/runtime route executed the cell;
- what it cost;
- who independently verified it;
- whether it was accepted, rejected, paused, or integrated.

## Canonical rule

> Concurrency increases throughput. It never increases authority.
