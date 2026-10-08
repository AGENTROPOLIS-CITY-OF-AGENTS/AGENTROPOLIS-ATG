# ATG Contract: AgenticPSAGrade

`AgenticPSAGrade` is a portable evidence contract for communicating an assurance grade between governed agents and systems.

It is descriptive evidence, not executable authority.

## Semantic contract

```json
{
  "type": "AgenticPSAGrade",
  "version": "1.0",
  "subject": {
    "id": "agent-or-component-id",
    "kind": "agent|skill|mcp|model|workflow|bundle",
    "version": "immutable-version-or-digest"
  },
  "grade": 9,
  "dimensions": {
    "identity_assurance": 10,
    "mandate_clarity": 9,
    "permission_minimization": 9,
    "security_posture": 9,
    "reliability": 9,
    "evidence_provenance": 10,
    "auditability_receipts": 10,
    "drift_entropy_controls": 8,
    "human_oversight": 9,
    "recovery_rollback": 9
  },
  "hard_caps": [],
  "findings": [],
  "assessor": {
    "id": "independent-assessor-id"
  },
  "evidence": [
    {
      "type": "receipt|test|audit|attestation|policy-result",
      "ref": "immutable-reference"
    }
  ],
  "issued_at": "RFC3339 timestamp",
  "valid_until": "RFC3339 timestamp or null",
  "supersedes": null,
  "receipt_ref": "tamper-evident-receipt-reference"
}
```

## Required behavior

Consumers MUST:

1. verify subject identity and exact version/digest
2. verify issuer/assessor identity
3. evaluate freshness and revocation state
4. inspect hard caps and unresolved findings
5. treat the grade as evidence only
6. run local policy and authority checks independently
7. reject grade reuse across materially different versions

Consumers MUST NOT interpret a PSA grade as:

- tool permission
- financial authority
- policy exemption
- mandate
- identity proof
- execution authorization

## Status semantics

- 10: production-grade
- 9: production-ready
- 8: operational with remediation
- 7: conditional deployment
- 6: isolated canary/sandbox
- 5 or lower: lab-only

## Chaining

Typical chain:

`AgenticPSAGrade -> ATG risk context -> policy compile -> Execution Envelope -> AEGIS gate -> receipt`

The grade can affect risk tier, required review, or routing, but it cannot bypass any downstream authorization gate.
