# ATG Profile: Governed EVM ERC-20 Transfer

Status: reference profile

This profile expands the EVM rail by exactly one capability: EIP-20 `transfer(address,uint256)` to a policy-pinned token contract. It does not grant generic contract-call authority.

## Normative boundary

1. Only ERC-20 `transfer(address,uint256)` is permitted.
2. `approve`, `transferFrom`, permit flows, DEX calls, bridge calls, delegatecall surfaces, and arbitrary calldata are out of scope.
3. Chain ID, source, token contract, recipient, token-unit ceiling, fee ceilings, and gas ceiling MUST be governed before signing.
4. Token amounts MUST be expressed in atomic token units, not human-readable decimals, at execution time.
5. The token contract MUST be independently inspected through a trusted runtime capability.
6. A policy MAY pin token bytecode/code hash and token decimals; if pinned, mismatches MUST fail closed.
7. The adapter MUST construct calldata itself using the fixed selector `0xa9059cbb`; caller-supplied calldata is never accepted.
8. Nonce and base-fee state MUST come from trusted runtime state.
9. Gas MUST be estimated by a trusted runtime capability and remain under `max_gas_limit`.
10. Worst-case total network fee MUST remain under `max_total_fee_wei`.
11. The signer MUST receive the exact prepared transaction and a capability handle only. Raw private keys or seed phrases MUST NOT enter model context.
12. The signer MUST attest the exact prepared-transaction hash.
13. A successful receipt before finalized-block coverage MUST remain `included_pending_finality`.
14. Only a successful finalized receipt may be labeled `settled`.
15. Receipt status failure MUST be labeled `payment_failed`.
16. Parent ATG mandate, 54-T policy, approval, receipt, and WikiVault evidence requirements still apply.

## Canonical flow

```text
ATG economic mandate
  -> 54-T decision
  -> capability handle
  -> trusted token inspection
  -> trusted nonce/base-fee state
  -> fixed transfer(address,uint256) calldata
  -> trusted gas estimate + fee ceilings
  -> sealed signer
  -> scoped raw-transaction submitter
  -> receipt + finalized-block verification
  -> ATG receipt / WikiVault evidence
```

## Authority separation

The token contract defines token behavior.

54-T decides whether this exact token/recipient/amount/chain is allowed.

The adapter only constructs the fixed transfer call.

The sealed signer owns cryptographic authorization.

The submitter owns RPC broadcast and receipt retrieval.

No stage inherits generic contract-call authority.

## Not implemented here

This reference profile does not provide:

- ERC-20 approvals
- `transferFrom`
- EIP-2612 permit
- Permit2
- DEX swaps
- bridges
- arbitrary contract calls
- smart-account execution
- token discovery from prompt content
- production RPC clients
- production key custody
- durable replay storage across processes

Each added capability requires its own separately scoped profile and threat review.
