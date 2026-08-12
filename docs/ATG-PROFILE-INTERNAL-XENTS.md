# ATG Profile: INTERNAL_XENTS

Status: reference profile

`internal_xents` is the first state-changing settlement adapter for ATG RFC-0003. It exists to exercise governed economic authority inside AGENTROPOLIS before external payment rails are enabled.

## Boundary

`internal_xents` is an internal ledger profile. It is **not** proof of blockchain settlement, token custody, bridge execution, or external financial finality.

A successful internal settlement MUST be labeled:

- `status: settled_internal`
- `asset: $XENTS`
- `finality: internal_ledger`
- `on_chain: false`

Implementations MUST NOT relabel internal ledger movement as on-chain transfer.

## Required flow

```text
ATG parent mandate
  -> RFC-0003 economic mandate
  -> 54-T policy decision
  -> bounded capability handle
  -> internal_xents adapter
  -> atomic ledger entry
  -> durable receipt / evidence record
```

## Normative controls

1. The economic mandate MUST use `settlement.mode = internal_xents`.
2. The asset MUST be `$XENTS`.
3. Amount checks MUST use exact decimal arithmetic rather than binary floating point.
4. Source balance MUST be sufficient before mutation.
5. Debit and credit MUST occur atomically inside the ledger boundary.
6. Every transfer MUST include an idempotency key.
7. Reuse of an idempotency key with identical parameters MUST return the prior result without double debit.
8. Reuse of an idempotency key with changed parameters MUST fail.
9. Ledger entries MUST bind to both the capability handle and the economic mandate hash.
10. Agents MUST NOT receive treasury credentials, wallet private keys, signing material, or unrestricted balance mutation capabilities.
11. Counterparty scope, amount, approval, and destination checks remain governed by 54-T before adapter execution.
12. Implementations MUST preserve a durable ledger entry suitable for later WikiVault/receipt materialization.

## Reference implementation

`atralith/internal_xents.py` provides:

- `InternalXentsLedger`
- `InternalXentsSettlementAdapter`

The reference ledger is in-memory and process-local. It demonstrates the transaction semantics and authority boundary only. Production persistence, concurrency across nodes, reconciliation, account recovery, fraud controls, reserve policy, and on-chain backing are outside this reference slice.

## Promotion path

`internal_xents` should graduate in stages:

1. reference in-memory ledger
2. durable transactional store
3. auditable account service + append-only receipt journal
4. governed bridge to external settlement
5. optional on-chain $XENTS representation

Each promotion requires a new verification profile and must not inherit trust merely because the prior stage passed.
