# ATG Profile — Governed EVM Native Transfer

Status: reference implementation profile

## Purpose

This profile maps a minimal EVM native-value payment into ATG RFC-0003 economic authority. Phase 1 supports only EIP-1559 native transfers with empty calldata. It intentionally excludes contract execution and token approvals.

## Runtime flow

```text
ATG economic mandate
  -> 54-T decision
  -> bounded capability handle
  -> trusted EVM state read (chain id / nonce / base fee)
  -> prepare exact native transfer
  -> sealed signer
  -> scoped raw-transaction submit
  -> receipt lookup
  -> finalized-block comparison
  -> ATG receipt / WikiVault evidence
```

## Normative controls

1. `settlement_mode` MUST be `evm`.
2. The policy MUST pin a positive EIP-155 chain ID.
3. Source and destination MUST be explicit 20-byte hex addresses.
4. The destination MUST remain within the parent ATG economic mandate and EVM policy scope.
5. Native value MUST be represented as an integer string in wei and remain below `max_value_wei`.
6. Phase 1 calldata MUST be empty (`0x`). Arbitrary contract calls are denied.
7. Phase 1 gas limit MUST be exactly 21000.
8. Transactions MUST use EIP-1559-style `maxFeePerGas` and `maxPriorityFeePerGas` ceilings.
9. Worst-case gas spend MUST remain below `max_total_fee_wei`.
10. Nonce MUST come from a trusted state reader, never prompt content.
11. The signer MUST receive the exact prepared transaction and attest its prepared hash.
12. Raw private keys, seed phrases, keystore passwords, or unrestricted signer objects MUST NOT enter model context.
13. A transaction receipt with failure status MUST be labeled `payment_failed`.
14. A successful receipt before finality MUST be labeled `included_pending_finality`.
15. A successful receipt MAY be labeled `settled` only when its block number is at or below the trusted finalized block number.

## Deliberately excluded in Phase 1

- arbitrary calldata
- ERC-20 transfers
- token approvals / Permit / Permit2
- swaps and DEX routing
- bridges
- smart-account execution
- contract creation
- delegatecall/proxy execution
- batch transactions
- dynamic RPC endpoints supplied by prompts

These require separate ATG profiles because their authority and failure surfaces are materially wider than a native transfer.

## Truth labels

- `pending_verification` — broadcast has no usable receipt yet.
- `included_pending_finality` — receipt reports success, but the inclusion block is not yet finalized.
- `payment_failed` — the receipt reports EVM execution failure.
- `settled` — receipt reports success and the inclusion block is within the trusted finalized range.

## Next promotion path

1. durable nonce/replay coordination
2. chain-specific RPC attestation and quorum reads
3. ERC-20 transfer-only profile with pinned token contract and exact calldata template
4. multisig / smart-account profile with separate capability classes
5. bridge/swap profiles only after CONTRA threat modeling and 54-T transitive-capability review
