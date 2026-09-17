# ATG Economic Boundary

Status: CANONICAL BOUNDARY

ATG is the Atralith agentic language and semantic protocol surface for AGENTROPOLIS. It expresses economic meaning, intent, constraints, authority references, policy requirements, and receipt requirements. It does not own settlement routing and does not choose payment rails.

## Canonical rule

```text
ATG expresses economic intent.
Economic Fabric evaluates economic policy.
PAYRAIL selects eligible settlement infrastructure.
Settlement adapters execute.
Receipts prove the result.
AGENT-ENTITY state updates after verified settlement.
```

## ATG may express

- payer / payee entity references;
- asset or unit constraints;
- maximum charge or spend ceiling;
- required finality;
- required receipt class;
- custody restrictions;
- approval requirements;
- jurisdiction or policy references;
- deadline / expiry;
- whether partial settlement is permitted;
- semantic meaning of the transaction.

Example:

```text
TRANSFER asset:X
FROM entity:A
TO entity:B
MAX_COST 0.25
REQUIRE settlement_finality
REQUIRE signed_receipt
DENY unapproved_custody
```

This is language-level intent. It is not a rail selection.

## ATG must not

- choose Arc, Base, XRPL, bank rails, or any other settlement provider;
- hold raw signing credentials;
- grant payment authority because a wallet or adapter is connected;
- mutate ownership state before required settlement verification;
- become the treasury, wallet, or settlement execution engine;
- silently turn a semantic profile into runtime authority.

## Relationship to AGENT-ENTITY

AGENT-ENTITY is the persistent entity layer. ATG may reference an AGENT-ENTITY's identity, mandate, rights, controller, ownership state, economic permissions, and receipt history, but the language does not become the entity record itself.

A runtime, model, wallet, chain address, card, avatar, robot, or application representation is not the AGENT-ENTITY.

## Relationship to PAYRAIL

PAYRAIL owns AGENTROPOLIS payment and settlement control responsibilities, including policy-gated spend, eligible rail selection, settlement adapter invocation, custody/signing boundaries, replay protection, finality verification, and economic receipts.

ATG should remain rail-agnostic so the same semantic request can survive provider changes.

## Compatibility doctrine

Any ATG settlement profile that pins a chain or rail is a bounded compatibility/adapter profile, not a claim that ATG owns settlement routing.

Legacy or implementation-specific profiles may describe requirements for executing on a selected rail. Selection remains external to the language contract.

## Standing rule

> **AGENT-ENTITY defines the actor. ATG defines the meaning. The Execution Envelope bounds the action. The Capability Fabric finds execution. The Economic Fabric and PAYRAIL decide how approved value moves. Settlement adapters execute. Receipts prove what happened.**
