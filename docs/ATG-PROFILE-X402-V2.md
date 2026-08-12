# ATG Profile — Governed x402 V2 Client

Status: reference implementation profile

## Purpose

This profile maps x402 V2 machine payments into the ATG RFC-0003 economic-authority model.

AGENTROPOLIS does not treat a `402 Payment Required` response as transaction authority. The server may advertise payment requirements; 54-T decides whether any requirement fits the already-approved economic mandate.

## Runtime flow

```text
resource request
  -> 402 + PAYMENT-REQUIRED
  -> parse x402 V2 requirements
  -> 54-T policy-envelope match
  -> sealed signer creates PaymentPayload
  -> retry same resource with PAYMENT-SIGNATURE
  -> resource response + PAYMENT-RESPONSE
  -> verification / receipt evidence
```

## Normative controls

1. x402 version MUST be 2 for this profile.
2. Networks MUST use explicit CAIP-2 identifiers in the policy envelope.
3. Payment requirement amounts MUST be interpreted as atomic-unit integer strings.
4. The selected requirement MUST remain within an explicit `max_amount_atomic` ceiling.
5. Scheme, network, asset, payee, resource URL, and payment flow MUST be checked before signing.
6. The default allowed payment flow is `authorization` only.
7. `upfront` and `escrow` MUST be denied unless the governing policy explicitly allows them.
8. The paid retry MUST target the same protected resource URL that produced the payment requirement.
9. The caller MUST NOT inject a prebuilt `PAYMENT-SIGNATURE` header.
10. Private keys, seed phrases, raw wallet credentials, or unrestricted signer access MUST NOT enter model context or ATG transaction objects.
11. A runtime signer MUST expose a capability-scoped signing interface and return only the x402 PaymentPayload.
12. A successful HTTP response without `PAYMENT-RESPONSE` MUST remain `pending_verification`; it MUST NOT be labeled settled.
13. A settlement response claiming a network different from the selected payment requirement MUST fail verification.
14. x402 execution remains subject to the parent ATG economic mandate, 54-T policy decision, capability handle, audit, and receipt requirements.

## Truth labels

- `not_required` — resource returned without a 402 challenge; no x402 payment was attempted.
- `pending_verification` — paid request returned but no parseable settlement response was available.
- `payment_failed` — payment or paid resource execution did not satisfy success conditions.
- `settled` — a parseable x402 SettlementResponse reports success, its network matches the selected requirement, and the paid resource request returned a success HTTP status.

`settled` in this adapter means the x402 server/facilitator path reported settlement. Independent chain confirmation, finality depth, or asset-specific proof MAY require additional verification before an application calls the payment economically final.

## Separation of authority

The server owns discovery of acceptable payment options.

54-T owns whether the agent may spend.

The sealed signer owns cryptographic payment authorization.

The transport owns network I/O.

ATRALITH binds these stages together with hashes, capability references, and receipts. No one stage may silently inherit the powers of another.
