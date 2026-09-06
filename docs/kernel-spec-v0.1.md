# AGENTROPOLIS Kernel Spec v0.1

**Status:** Draft / lock candidate

## Purpose

Define the irreducible primitives of the AGENTROPOLIS Intelligence Grid without hard-coding any current vendor, model, runtime, protocol, device, or interface.

## Kernel primitives

1. **ATG / Atralith IR** — compiles human or agent intent into a governed execution representation.
2. **Identity** — stable principal identity independent of runtime.
3. **Mandate** — explicit scope, duration, and delegation boundary.
4. **Capability** — implementation-neutral ability requested by the mission.
5. **Authority** — allowed, denied, approval-gated, budgeted, and delegation-bounded actions.
6. **Risk** — compiled before Dispatch from capability, authority, reversibility, blast radius, data sensitivity, economic exposure, and physical effect.
7. **Dispatch** — selects who/what/where may execute without changing the mission contract.
8. **Execution** — adapter-mediated work constrained by the Execution Envelope.
9. **Evidence / Receipt** — executor claims plus independent evidence and verification verdicts.

## Runtime path

The conceptual architecture may contain many planes, but a single mission should traverse only the controls it needs.

```text
Intent
  -> ATG/Atralith
  -> Execution Envelope
  -> Dispatch
  -> Capability Adapter
  -> Result + Receipt
  -> Verification as required
```

## Progressive governance

Governance complexity scales with risk rather than system size.

```text
R0 observation only
R1 reversible low impact
R2 controlled modification
R3 consequential / production / economic
R4 destructive / privileged / high consequence
R5 physical-world / human-safety critical
```

Risk is assigned before Dispatch. Workers may request escalation but may never downgrade their own risk tier.

## Evidence invariant

Receipts are assertions, not truth. Where the Envelope requires independent verification, executor-generated evidence cannot satisfy that requirement.

## Future-capability rule

Unknown future capabilities may be represented before implementations exist, but they do not become canonical kernel primitives merely because they are imaginable.

A new mandatory kernel primitive requires either:
1. a real vertical slice that cannot be represented safely without it; or
2. a credible future capability that cannot be represented safely without it.

## Vendor independence

No kernel primitive may require a specific implementation such as Hermes, BotBae, BUZZ, Devin, NemoClaw, Nemotron, Codex, Slack, MCP, A2A, a particular model, or a particular hardware class.

These systems integrate through versioned adapters and contracts.

## Current role map

- **ATG / Atralith:** semantic IR and contract compiler
- **BotBae:** persistent workforce / agent entity experience
- **Hermes:** persistent agent society and coordination adapter
- **BUZZ:** shared human-agent collaboration and signed event workspace
- **Devin / Codex:** builder implementations
- **NemoClaw:** execution/runtime environment
- **Nemotron:** intelligence/model provider
- **Pocket Grid:** portable human command surface
- **Slack:** external collaboration/command ingress and egress
- **AEGIS:** policy/risk enforcement
- **Sentinel-6:** verification, drift, and independent review

## Design law

> Design for the future. Implement from reality outward.

> The Envelope stays small. The ecosystem grows around it.
