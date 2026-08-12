# RFC-0003 — Economic Authority and Settlement

**Status:** Draft

## Abstract

This RFC defines a governed transaction profile for AGENTROPOLIS agents. It separates economic intent from transaction authority and settlement credentials.

An agent MUST NOT receive generalized purchasing power merely because a user expressed intent to buy, subscribe, transfer, book, deploy capital, or pay for a service.

The normative flow is:

```text
Intent -> Inspect -> Simulate -> Preview -> Approve -> Execute -> Verify -> Receipt
```

Economic execution is represented by an **ATG Economic Mandate** that is bounded by purpose, amount, counterparty, network, time, use count, delegation rights, approval state, and risk controls.

## 1. Design goals

1. Preserve user intent without converting it into unrestricted financial authority.
2. Minimize the transaction capability exposed to an agent.
3. Support crypto-native settlement first while permitting optional fiat/card bridges.
4. Keep raw private keys, production wallet secrets, PANs, API secrets, and unrestricted treasury credentials outside model context.
5. Produce permanent verifiable receipts for consequential economic actions.
6. Prevent third-party harm caused by agents testing unauthorized transaction paths.
7. Remain implementation-neutral and provider-neutral.

## 2. Non-goals

This RFC does not define a custodian, exchange, bank, payment processor, card issuer, or wallet implementation. External providers are adapters, never constitutional dependencies.

## 3. Economic authority model

### 3.1 Intent is not authority

A natural-language request describes a desired outcome. It does not itself authorize every possible method of achieving that outcome.

Examples:

- "Book me the earliest class" does not authorize removing another customer's reservation.
- "Buy this dataset" does not authorize use of every stored payment method.
- "Pay the invoice" does not authorize changing the destination wallet.

### 3.2 Minimum necessary economic capability

The runtime MUST compile a transaction request into the smallest effective capability surface.

A compliant mandate SHOULD restrict:

- principal or agent identity
- economic purpose
- maximum value
- allowed asset
- allowed chain/network
- merchant/domain/address scope
- validity period
- maximum uses
- retry count
- recurring state
- delegation state
- reversibility requirements
- approval method
- signer class
- third-party impact checks

### 3.3 No generalized money handles

Agents MUST NOT receive unrestricted wallet seed phrases, private keys, card data, treasury credentials, or production secrets in model context.

Execution SHOULD use one of:

- capability handles
- ephemeral authorization tokens
- single-use payment credentials
- bounded session wallets
- sealed signers
- threshold/quorum signers

## 4. Settlement modes

ATG recognizes settlement modes without privileging one provider.

Initial modes:

- `internal_xents`
- `x402`
- `xrpl`
- `evm`
- `solana`
- `fiat_bridge`
- `other`

AGENTROPOLIS MAY prefer internal $XENTS and crypto-native rails for native ecosystem transactions. Fiat/card systems SHOULD be modeled as optional external adapters.

## 5. Authorization classes

Economic actions inherit ATG authorization classes:

- `A1_REVERSIBLE` — low-impact, clearly reversible transaction.
- `A2_BOUNDED` — value-capped, scoped, controlled economic action.
- `A3_IRREVERSIBLE` — irreversible or materially consequential settlement.
- `A4_ROOT` — treasury-root or authority-root action. Requires strongest controls.

A runtime MUST NOT silently downgrade the authorization class to gain execution success.

## 6. Third-party impact rule

Before execution, the runtime MUST determine whether the intended action can alter, remove, transfer, reserve, cancel, spend, or encumber an asset, booking, entitlement, account, or resource belonging to another principal.

If the target does not belong to the authorizing principal and explicit authority is absent, execution MUST stop.

Discovery of a technical path is not authorization to exercise that path.

## 7. Approval policy

Human approval SHOULD be required when any of the following apply:

- action is `A3_IRREVERSIBLE` or `A4_ROOT`
- counterparty changed after approval preview
- value exceeds policy threshold
- destination is new or untrusted
- transaction affects a third party
- fallback settlement mode differs from the approved mode
- blind signing would be required
- recurring authority is requested
- delegation to another agent is requested

High-risk actions SHOULD support passkey, physical confirmation, quorum, or dual-control approval.

## 8. Execution pipeline

### 8.1 Inspect

Resolve merchant, contract, address, asset, price, fees, network, availability, ownership, and third-party impact.

### 8.2 Simulate

Where technically possible, simulate the exact payload and record expected state changes, fees, failure conditions, and reversibility.

### 8.3 Preview

Render the exact material facts that the approving principal must understand. The preview MUST bind to the executable payload by hash where supported.

### 8.4 Approve

Obtain the mandate-required confirmation. Approval is invalid if the material payload changes afterward without re-approval.

### 8.5 Execute

Issue only the bounded capability required for the approved operation. Credentials SHOULD expire immediately after permitted use.

### 8.6 Verify

Confirm settlement result, target, amount, fees, final state, and any relevant external confirmation.

### 8.7 Receipt

Create an ATG receipt covering at minimum:

- source mandate hash
- economic mandate hash
- policy decision hash
- reviewed intent hash
- executable payload hash
- counterparty identity
- settlement mode
- network
- asset and amount
- credential class
- approval method
- signer type
- execution result
- verification state
- third-party impact decision
- fallback state
- timestamps

## 9. Commerce discovery

Merchant and service discovery MUST remain separate from transaction authorization.

Structured catalogs, agent-readable product feeds, MCP tools, APIs, service registries, and marketplace indexes MAY supply discovery data. Their presence does not constitute authority to purchase.

This separation permits AGENTROPOLIS to support machine-readable markets for:

- skills
- datasets
- compute
- GPU time
- media generation
- software licenses
- research services
- agent labor
- game assets
- NFTs and on-chain artifacts
- training and education
- APIs and hosted services
- physical goods through external settlement adapters

## 10. Provider adapters

External commerce or payment platforms MAY implement ATG settlement adapters.

Adapter requirements:

1. No provider becomes a mandatory core dependency.
2. Provider credentials remain sealed outside model context.
3. Provider-specific scopes MUST map into the Economic Mandate.
4. Provider fallback behavior MUST be explicit.
5. The adapter MUST return enough evidence to construct an ATG receipt.
6. Hosted service claims MUST not be represented as local or open-source capabilities unless independently verified.

## 11. Relationship to 54-T and CONTRA

54-T validates effective execution boundaries, tool scope, credential exposure, egress, and authority class before a capability is issued.

CONTRA MAY challenge the transaction premise, merchant claims, pricing assumptions, counterparty trust, reversibility, or risk representation before approval.

Neither component may expand financial authority beyond the mandate.

## 12. Relationship to WikiVault

Raw evidence and transaction artifacts SHOULD be retained in governed storage such as WikiVault. Model context SHOULD receive compact evidence packages and deltas rather than unrestricted raw transaction history.

Receipt identifiers SHOULD be stable and suitable for durable cross-layer references.

## 13. Security invariants

A compliant AGENTROPOLIS implementation MUST preserve these invariants:

1. User intent is not transaction authority.
2. Discovery is not permission.
3. Simulation is not execution.
4. Approval binds to the reviewed payload.
5. Agents receive capability handles, not raw production secrets.
6. Economic authority expires or revokes according to mandate constraints.
7. Third-party resources cannot be modified without explicit authority.
8. Fallback paths cannot silently increase privilege.
9. High-risk actions cannot silently reduce approval requirements.
10. Every consequential execution produces a durable receipt or an explicit receipt-generation failure state.

## 14. Reference contract

The normative draft schema is:

`contracts/core/economic-mandate.schema.json`

Future work may add a dedicated economic receipt extension once implementation requirements stabilize.
