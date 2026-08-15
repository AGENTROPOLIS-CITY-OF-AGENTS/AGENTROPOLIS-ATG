# ATG Profile: Governed Solana Native SOL Settlement

Status: reference profile

This profile maps a single native SOL transfer into ATG RFC-0003 economic authority.
The adapter is deliberately narrow: one System Program transfer, one governed recipient,
one recent blockhash, one sealed signer boundary.

## Normative boundary

1. The adapter MUST support only native SOL transfer in Phase 1.
2. SPL-token transfers and arbitrary program instructions MUST NOT be accepted by this profile.
3. The source account, cluster, destination, amount ceiling, and fee ceiling MUST be policy-bound before signing.
4. Amount MUST be expressed as an integer lamport string in the execution object.
5. Recipient public keys MUST be syntactically valid and independently classified by a trusted Solana state capability.
6. Recipient kind MUST be explicitly allowed because a native SOL transfer may succeed even if the destination is not the intended account type.
7. Recent blockhash and last valid block height MUST come from trusted runtime state, never prompt content.
8. The adapter MUST fail closed when the blockhash is already expired or the validity window exceeds the governed ceiling.
9. Estimated network fee MUST remain under `max_fee_lamports`.
10. The signer MUST receive only the exact prepared message and a capability handle; raw key material MUST NOT enter model context.
11. The signer MUST attest the exact prepared-message hash.
12. `confirmed` is not final settlement. It MUST remain `confirmed_pending_finality`.
13. Only `finalized` with no transaction error may be labeled `settled`.
14. All consequential execution remains subject to parent mandate, 54-T policy, approval, receipt, and WikiVault evidence rules.

## Canonical flow

```text
ATG economic mandate
  -> 54-T decision
  -> capability handle
  -> trusted recipient classification
  -> trusted latest blockhash + last-valid height
  -> fee estimation + ceilings
  -> exact System Program transfer message
  -> sealed signer
  -> scoped submitter
  -> confirmed/finalized verification
  -> ATG receipt / WikiVault evidence
```

## Default recipient policy

The reference profile defaults to:

- `system_wallet`
- `unfunded_on_curve`

Other account kinds require explicit policy expansion after independent validation.

## Truth states

- `pending_verification` — no reliable signature status yet.
- `confirmed_pending_finality` — transaction is confirmed but not finalized.
- `payment_failed` — Solana reports a transaction error.
- `settled` — signature status is finalized and error-free.

## Not implemented here

This reference profile does not provide:

- a production RPC client
- private key custody
- SPL Token or Token-2022 transfers
- associated-token-account creation
- arbitrary program calls
- compute-budget bidding
- durable nonce transactions
- address lookup tables
- multisig
- durable replay storage across processes

Those belong in separately scoped and separately reviewed profiles.
