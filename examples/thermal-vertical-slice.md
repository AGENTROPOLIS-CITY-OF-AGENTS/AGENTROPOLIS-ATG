# Thermal Vertical Slice v0.1

## Goal

Prove that the AGENTROPOLIS execution path can carry a real capability end to end and catch a false executor claim using evidence the executor does not control.

## Capability

`device.thermal.observe`

## Path

```text
Pocket Grid sensor
  -> baseline thermal observation
  -> ATG/Atralith compiler
  -> Execution Envelope v0.1
  -> Dispatch
  -> capability implementation / remote remediation
  -> executor result + receipt claim
  -> Pocket Grid sensor
  -> independent verification
  -> verdict
```

## Required envelope characteristics

- `risk.tier` is compiled before Dispatch.
- Dispatch cannot downgrade risk or remove evidence requirements.
- `evidence.independent_verification` requires a source outside executor control.
- Unknown optional envelope fields are ignored.
- Unknown fields listed in `must_understand` cause execution refusal.

## Ground truth

For this slice, Pocket Grid owns the independent signal source. The executor must not control, rewrite, or synthesize the post-execution thermal observation used for verification.

Where platform APIs expose only coarse thermal state rather than raw temperature, the slice should compare the platform-native thermal state and record the measurement limitations explicitly.

## Test 1: truthful receipt

1. Capture baseline thermal state from Pocket Grid.
2. Execute a bounded remediation or routing action.
3. Executor emits claim: `device.thermal.reduced = true`.
4. Pocket Grid captures post-action thermal state independently.
5. Verifier compares claim and signal.
6. Expected verdict: `VERIFIED` only when evidence supports the claim.

## Test 2: forged receipt

1. Capture baseline thermal state.
2. Do not produce a real thermal improvement, or deliberately substitute a fixture that leaves the state unchanged.
3. Executor emits claim: `device.thermal.reduced = true`.
4. Pocket Grid captures the independent post-action signal.
5. Verifier compares claim and signal.
6. Expected verdict:

```text
VERIFICATION_CONFLICT
RECEIPT_UNVERIFIED
```

## Success criterion

The slice succeeds only if the system reliably distinguishes a truthful receipt from a forged receipt using evidence outside executor control.

Producing a receipt is not success.
Catching the lie is success.

## Follow-on capability

Once observation and independent verification work, add:

`compute.remote.route`

This allows Dispatch to respond to elevated thermal pressure by moving heavy work off the mobile device while Pocket Grid remains the command and evidence surface.

## Non-goals

This slice does not require every AGENTROPOLIS subsystem to participate. It proves the minimum path first, then adds controls only where the risk tier requires them.
