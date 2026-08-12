# ATG Profile: Governed XRPL Direct XRP Payment

Status: reference profile

This profile maps a narrow XRPL `Payment` transaction into the ATG RFC-0003
economic-authority model. The first profile supports direct XRP payments only.
It intentionally excludes pathfinding, issued-token exchange, partial payments,
and server-side signing.

## Normative boundary

1. XRPL execution is a live external settlement adapter and requires explicit governed live-mode enablement.
2. Raw seeds, secret keys, signing phrases, and unrestricted wallet objects MUST NOT enter model context.
3. Signing MUST occur through an injected sealed signer capability.
4. Transaction submission/state reads MUST occur through scoped runtime capabilities.
5. Source account and destination MUST be explicitly policy-bound before signing.
6. Amount MUST be represented in drops as a non-negative integer string and MUST fit `max_amount_drops`.
7. Recommended network fee MUST fit `max_fee_drops`; the adapter MUST fail closed when network load pushes the fee above policy.
8. `Sequence` MUST come from trusted account state, not prompt content.
9. `LastLedgerSequence` MUST be present for ordinary single-sign direct XRP payments so transactions expire deterministically.
10. `tfPartialPayment` is forbidden in this profile.
11. `SendMax`, `DeliverMin`, `Paths`, and other advanced exchange/payment semantics are forbidden in this profile.
12. The sealed signer MUST attest that it signed the exact prepared transaction hash.
13. A transaction MUST NOT be labeled settled until the result is from a validated ledger and `TransactionResult` is `tesSUCCESS`.
14. A validated non-success result is `payment_failed`; an unvalidated result remains `pending_verification`.
15. Settlement evidence MUST bind the capability handle, economic mandate hash, policy decision hash, prepared transaction hash, transaction ID, ledger-bound expiry, and final result hash.

## Runtime flow

```text
Agent intent
  -> ATG mandate
  -> RFC-0003 economic mandate
  -> 54-T decision
  -> capability handle
  -> trusted XRPL state read
  -> prepare exact Payment
  -> check destination / amount / fee / sequence / LastLedgerSequence
  -> sealed signer signs exact prepared transaction
  -> submit signed blob
  -> wait/check validated ledger result
  -> truth label: settled | payment_failed | pending_verification
  -> ATG receipt / WikiVault evidence
```

## Reference transaction policy

```json
{
  "settlement_mode": "xrpl",
  "destination": "rDestination...",
  "amount_drops": "1000000",
  "xrpl_policy": {
    "network": "xrpl:mainnet",
    "account": "rSource...",
    "allowed_destinations": ["rDestination..."],
    "max_amount_drops": "5000000",
    "max_fee_drops": "20",
    "last_ledger_offset": 20,
    "required_source_tag": 589
  }
}
```

## Truth labels

- `settled` — transaction is included in a validated ledger and its final `TransactionResult` is `tesSUCCESS`.
- `payment_failed` — transaction is included in a validated ledger with a non-success result.
- `pending_verification` — final validated outcome is not yet established.

Tentative submit responses are not final economic truth.

## Threat model

The profile fails closed against:

- source account substitution
- destination substitution
- amount above mandate/policy ceiling
- fee spikes above approved ceiling
- missing or stale trusted account sequence data
- missing bounded expiry (`LastLedgerSequence`)
- partial-payment semantics
- pathfinding/exchange fields in a direct-XRP mandate
- signer substitution that signs a different transaction
- result hash mismatch
- treating tentative or unvalidated results as final settlement
- raw secret exposure through agent/model context

## Promotion path

This first profile should be extended through separate, reviewable profiles rather
than widening this one:

1. direct XRP single-sign
2. direct XRP multisign / hardware signer
3. XRPL issued-token direct payment
4. XRPL trustline-aware asset policy
5. XRPL NFT / access-key settlement where applicable
6. TARATIA / VAULT33 artifact-specific profiles

Each profile keeps its own authorization, fee, asset, destination, finality, and
receipt semantics while sharing the ATG RFC-0003 economic-authority envelope.
