# AGENTROPOLIS Capability ABI v0.1

**Status:** Draft foundation contract  
**Semantic layer:** ATG / Atralith  
**Consumes:** `agentropolis.execution-envelope`  

## Purpose

Define the minimum implementation contract that lets current and future technologies satisfy an AGENTROPOLIS capability without becoming part of the Grid kernel.

Implementations may be Hermes, NemoClaw, Devin, Codex, Nemotron-backed workers, robots, remote services, local devices, or future systems.

## Required operations

A conforming capability adapter exposes the following logical operations:

```text
describe()
health()
estimate(envelope)
authorize(envelope)
execute(envelope)
observe(execution_id)
interrupt(execution_id)
verify(result, evidence)
receipt(execution_id)
```

### describe()
Returns implementation-neutral metadata including:
- capability handle
- adapter version
- supported envelope major versions
- supported operations
- execution classes
- known constraints

### health()
Returns whether the adapter is available and sufficiently healthy to accept work.

### estimate(envelope)
Returns non-binding estimates for:
- latency
- cost
- energy / resource pressure where measurable
- data movement
- expected execution class

### authorize(envelope)
Checks whether the adapter can satisfy the Envelope **without expanding authority, reducing risk, or weakening evidence requirements**.

A worker may refuse or request escalation. It may never self-grant authority or downgrade risk.

### execute(envelope)
Executes only within the compiled Envelope.

### observe(execution_id)
Returns current execution state without mutating the mission.

### interrupt(execution_id)
Provides a bounded stop/cancel path when supported. Adapters must declare whether interruption is immediate, cooperative, delayed, or unsupported.

### verify(result, evidence)
Evaluates claims against available evidence. A verifier must declare its independence class. Executor-self verification cannot satisfy an Envelope that requires independent evidence.

### receipt(execution_id)
Returns signed or attributable claims about what the executor says happened. Receipts are claims, not truth.

## Compatibility

Adapters MUST:
- declare supported Execution Envelope major versions;
- ignore unknown optional Envelope fields;
- refuse execution when an unknown field is listed in `must_understand`;
- never reinterpret an established field incompatibly within a major version.

## Capability identity

Capabilities are named by stable handles, for example:

```text
device.thermal.observe
compute.remote.route
software.modify
repository.patch
physical.humanoid.navigate
```

The capability is the contract. The adapter is replaceable.

## Adapter responses

A capability adapter returns one of:

```text
ACCEPT
REFUSE
REQUEST_CLARIFICATION
REQUEST_MORE_AUTHORITY
REQUEST_RISK_ESCALATION
RUNNING
COMPLETED
FAILED
INTERRUPTED
UNSUPPORTED_ENVELOPE_SEMANTICS
```

## Invariants

An adapter MUST NOT:
- rewrite the mission objective;
- expand mandate scope;
- increase its own authority;
- downgrade the risk tier;
- remove approval requirements;
- remove evidence requirements;
- claim executor-controlled evidence is independent;
- silently substitute a prohibited runtime, model, provider, device, or location.

## Thin-runtime rule

Not every operation requires every Grid subsystem. Low-risk capabilities may execute through a short path so long as Envelope invariants remain intact.

```text
Envelope -> capability adapter -> result -> receipt
```

Higher-risk work may invoke AEGIS, Sentinel-6, approvals, simulation, independent verification, or other governance controls.

Complexity scales with mission risk. The contract does not require bureaucracy for trivial work.
