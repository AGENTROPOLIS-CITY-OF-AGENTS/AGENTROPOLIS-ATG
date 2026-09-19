# ATRALITH / FISCALITH Bridge — Implementation

Status: IMPLEMENTED (executable)

This document describes the executable bridge that connects the ATRALITH / ATG
agent language to the FISCALITH financial language. It complements the
specification in `docs/ATRALITH-FISCALITH-BRIDGE.md` (the boundary contract)
with a working, tested implementation.

## Role split (unchanged canon)

- ATG carries financial meaning; it does not own financial semantics.
- FISCALITH defines financial meaning.
- AEGIS decides whether an action is allowed.
- AQUADUCT proves safely when required.
- PAYRAIL routes approved production value.
- Receipts prove what happened.

## What this module implements

`atralith/fiscalith_bridge.py` provides the ATG-side bridge responsibilities:

| Component | Responsibility |
|---|---|
| Financial payload detector | `detect()` — recognizes a FISCALITH payload inside an ATG message |
| FISCALITH parser | `parse()` — extracts kind, payload, and ATG context |
| FISCALITH validator | `validate()` — fail-closed JSON + integer-money + authority checks |
| FISCALITH IR / compiler | `compile()` — produces a provider-neutral `FiscalithIR` |
| ATG wrapper | `wrap_for_aegis()` — Execution Envelope candidate for the AEGIS decision plane |
| Response mapper | `map_result()` — normalizes provider results to FISCALITH result objects |
| Refusal mapper | `map_refusal()` — explicit denial state |
| Receipt mapper | `map_receipt()` — ATG.RECEIPT from verified settled result |
| Version negotiation | `negotiate_version()` — supported FISCALITH version set |
| Compatibility migration | `migrate_legacy_payload()` — legacy ATG economic payloads |

## Canonical flow

```text
ATG message
  -> detect FISCALITH payload
  -> parse
  -> validate (fail closed)
  -> FISCALITH IR
  -> wrap_for_aegis (Execution Envelope candidate)
  -> AEGIS decision (external)
  -> approved downstream execution (external)
  -> FISCALITH result
  -> ATG.RECEIPT
```

The bridge never grants authority, chooses a settlement rail, holds
credentials, or executes value. `wrap_for_aegis` output is a candidate that
MUST pass an AEGIS authority decision before any execution.

## NO FLOAT MONEY invariant

Authoritative monetary representation is integer/fixed-unit. The validator
rejects:

- float amounts (`4.2`)
- boolean amounts
- scientific notation (`4e6`)
- excess precision beyond the declared scale
- negative amounts for PAY/SEND
- malformed numeric strings

Human-readable decimal formatting is presentation only and never canonical.

## Fail-closed authority boundary

The validator enforces a strict allow-list on the FISCALITH envelope. Any
unknown top-level field is rejected. This blocks attempts to smuggle:

- self-promotion
- budget / transaction-cap increases
- new beneficiaries / counterparties
- policy or mandate mutation
- credential access
- alternate-rail / fallback bypass
- FREEZE bypass

A malformed `SignedIntent` signature is rejected. A `rail`/`provider`/credential
field anywhere in the payload is rejected.

## Replay protection

`compile()` consults a replay guard keyed on `(kind, intent_id, mandate_ref)`.
The default is an in-memory guard; production deployments MUST supply a durable
guard via the `replay_guard` constructor argument. Concurrent replay across
bridge instances is rejected when they share a guard.

## Reconciliation

When `reconciliation.expected_principal_minor` and `expected_total_minor` are
both present:

- with a declared `max_fee_minor`: `principal + max_fee == total` must hold;
- without a declared fee: `principal == total` must hold (no hidden fee).

## Version negotiation

`negotiate_version()` accepts only the configured supported version set
(default `{"1.0"}`). Unsupported versions raise `UnsupportedVersionError`.

## Compatibility migration

`migrate_legacy_payload()` maps legacy ATG economic field names to canonical
FISCALITH names and converts legacy decimal-string amounts to integer minor
units while preserving the stated scale. Scientific notation is rejected.

## Tests

`atralith/test_fiscalith_bridge.py` — 51 tests covering:

- financial boundaries (smallest unit, maximum, zero, negative, excess
  precision, scientific notation, whitespace, wrong decimals/asset/
  counterparty/intent, expired intent, stale mandate, expired envelope,
  fee/slippage/settlement mismatch, replay, concurrent replay, malformed
  SignedIntent, provider manipulation, forged receipt);
- authority paths (self-promotion, budget increase, transaction-cap increase,
  new beneficiary, new counterparty, policy mutation, mandate mutation,
  credential access, alternate-rail bypass, fallback bypass, FREEZE bypass);
- compile + mapping + version negotiation + migration.

Run:

```bash
uv run --with jsonschema python -m unittest atralith.test_fiscalith_bridge -v
```

## Non-duplication

Financial schemas belong to AGENTROPOLIS-FISCALITH. This bridge references the
canonical FISCALITH intent by `$id` (`CANONICAL_FISCALITH_INTENT_ID`) and does
not fork it. The typed PAY payload schema under `contracts/fiscalith/` is a
bridge contract, not a replacement for the FISCALITH canonical document.
