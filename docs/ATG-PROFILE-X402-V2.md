# ATG Profile: Governed x402 V2 Settlement

Status: reference profile

This profile maps x402 V2 client payments into ATG RFC-0003 economic authority.
It does not turn a wallet into generalized agent authority. The transaction must
first pass the ATG mandate compiler and the 54-T policy decision point, which
issue a bounded capability handle to the x402 adapter.

## Normative boundary

1. The x402 adapter MUST be treated as a live external settlement adapter.
2. `execute_economic_action(..., allow_live=True)` MUST be an explicit governed decision.
3. Private keys, seed phrases, raw wallet credentials, and unrestricted signer objects MUST NOT enter model context.
4. Signing MUST occur through an injected sealed signer capability.
5. HTTP transport MUST be injected as a scoped runtime capability.
6. The protected resource URL and approved domain MUST remain stable between discovery and paid retry.
7. A caller MUST provide an explicit `x402_policy`; the adapter MUST NOT infer a spend ceiling from the server's 402 response.
8. x402 V2 `amount` values MUST be treated as integer strings in atomic asset units.
9. Network identifiers MUST use CAIP-2 form.
10. The selected scheme, network, asset, amount, recipient, and payment flow MUST fit the governed policy envelope.
11. `authorization` is the default permitted payment flow. `upfront` and `escrow` require explicit policy opt-in.
12. A successful HTTP response without a parseable `PAYMENT-RESPONSE` MUST NOT be labeled settled.
13. Settlement evidence MUST bind the capability handle, economic mandate hash, policy decision hash, payment requirement hash, payment payload hash, and settlement response hash.

## V2 HTTP flow

```text
Agent intent
  -> ATG mandate
  -> RFC-0003 economic mandate
  -> 54-T decision
  -> capability handle
  -> GET/POST protected resource
  <- 402 + PAYMENT-REQUIRED
  -> validate requirement against governed x402 policy
  -> sealed signer creates PaymentPayload
  -> retry same resource with PAYMENT-SIGNATURE
  <- resource + PAYMENT-RESPONSE
  -> verify settlement truth state
  -> ATG receipt / WikiVault evidence
```

## Reference transaction policy

```json
{
  "settlement_mode": "x402",
  "resource_url": "https://compute.example/render/42",
  "domain": "compute.example",
  "x402_policy": {
    "network": "eip155:8453",
    "asset": "USDC",
    "max_amount_atomic": "1500000",
    "allowed_schemes": ["exact"],
    "allowed_payment_flows": ["authorization"],
    "pay_to": "0xabc"
  }
}
```

The human-readable economic mandate may express a decimal value such as `1.50`
USDC, while the x402 network requirement expresses the same bounded payment in
atomic token units. Production integration MUST obtain token-decimal metadata
from a trusted chain/asset registry rather than prompt content.

## Truth labels

- `not_required` — resource returned without a 402 challenge; no x402 payment was attempted.
- `pending_verification` — paid request returned but no parseable settlement response was available.
- `payment_failed` — payment or paid resource execution did not satisfy success conditions.
- `settled` — a parseable x402 SettlementResponse reports success, its network matches the selected requirement, and the paid resource request returned a success HTTP status.

`settled` means the x402 server/facilitator path reported settlement. Independent chain confirmation, finality depth, or asset-specific proof may require additional verification before an application calls the payment economically final.

## Threat model

The adapter fails closed against:

- malicious 402 responses asking for more than the approved budget
- chain or asset substitution
- merchant recipient substitution when `pay_to` is pinned
- domain/resource drift after approval
- caller-injected `PAYMENT-SIGNATURE`
- signer payloads that change the selected PaymentRequirements
- extension deletion or overwrite
- unsupported x402 protocol versions
- silent upfront payment when only authorization is approved
- 2xx responses that omit settlement evidence

## Separation of authority

The resource server may advertise acceptable payment options. 54-T owns whether
the agent may spend. The sealed signer owns cryptographic payment authorization.
The transport owns network I/O. ATRALITH binds these stages with capability
handles, hashes, and receipts; no stage silently inherits another stage's power.

## Not implemented here

The reference adapter does not itself provide:

- a private key store
- an EVM or Solana signer
- facilitator hosting
- token decimal discovery
- retry/replay persistence across processes
- durable nonce accounting
- chain finality monitoring
- refunds
- treasury accounting

Those belong behind separately attested provider/chain adapters and 54-T capability scopes.
