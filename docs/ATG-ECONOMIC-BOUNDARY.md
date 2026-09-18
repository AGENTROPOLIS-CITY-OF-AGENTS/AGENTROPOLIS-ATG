# ATG / FISCALITH Economic Boundary

Status: CANONICAL BOUNDARY

**ATRALITH / ATG is the AGENTROPOLIS agent language.**

ATG defines how agents communicate, negotiate, delegate, request, refuse, verify, report, reference mandates, reference proofs, and carry domain payloads. ATG does **not** own financial semantics.

**FISCALITH is the financial language.** It defines economic meaning for payments, quotes, bids, jobs, invoices, treasury, FX, swaps, bridges, fees, credit, collateral, settlement, reconciliation and other agentic-commerce operations.

## Canonical rule

```text
AGENTENTITY
  -> ATRALITH / ATG message envelope
  -> FISCALITH financial payload when the interaction is economic
  -> Execution Envelope
  -> AEGIS authority / policy / risk decision
  -> AQUADUCT when sandbox or certification is required
  -> PAYRAIL for approved production routing
  -> provider / rail / contract adapter
  -> financial evidence + receipts
  -> FISCALITH result
  -> ATG.RECEIPT / ATG.DENY / ATG.ESCALATE
```

## ATG owns

- agent speech acts such as REQUEST, PROPOSE, OFFER, ACCEPT, DELEGATE, REFUSE, VERIFY, RECEIPT and ESCALATE;
- sender / recipient AGENTENTITY references;
- conversation and correlation identity;
- mandate references;
- delegation references;
- capability references;
- proof requirements and proof references;
- Execution Envelope references;
- result, refusal, escalation and receipt communication;
- provider-neutral agent-to-agent and agent-to-system message structure.

## FISCALITH owns

- financial intent semantics;
- asset and amount semantics;
- quote / bid / offer;
- invoice / payroll / royalty / split;
- treasury and budget semantics;
- escrow and job economics;
- bridge / swap / FX / credit / collateral;
- fee, slippage, expiry, finality and reconciliation semantics;
- financial result semantics.

## ATG must not

- redefine financial instruments;
- choose Arc, Base, XRPL, bank rails or another settlement provider;
- hold raw signing credentials;
- grant financial authority;
- become the treasury or wallet;
- infer permission from a connected wallet;
- convert provider support into authority;
- bypass AEGIS, 54T, AQUADUCT, PAYRAIL or receipt requirements.

## FISCALITH bridge

ATG MAY carry a FISCALITH payload:

```text
ATG.REQUEST {
  from: TREASURY-042
  to: PAYRAIL
  mandate_ref: M-881
  payload: FISCALITH.PAY {
    counterparty: VENDOR-12
    asset: USDC
    amount: 4200
  }
}
```

A financial response returns through ATG:

```text
ATG.RECEIPT {
  payload: FISCALITH.SETTLED {
    amount: 4200
    asset: USDC
    settlement_ref: S-771
  }
  proofs: [
    ProofOfExecution,
    ProofOfSettlement,
    ProofOfOutcome
  ]
}
```

## Compatibility doctrine

Existing ATG economic code and profiles are compatibility surfaces while financial semantics migrate to FISCALITH. They MUST NOT be treated as canonical ownership of finance.

The migration must preserve working consumers while moving canonical economic vocabulary, financial IR, fee semantics and financial state machines into AGENTROPOLIS-FISCALITH.

## Standing rule

> **ATRALITH tells agents how to speak. FISCALITH defines financial meaning. AEGIS decides whether an action is allowed. 54T protects the trust boundary. AQUADUCT proves safely. PAYRAIL routes approved production value. Receipts prove what happened.**
