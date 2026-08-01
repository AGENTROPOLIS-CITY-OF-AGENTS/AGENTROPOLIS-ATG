# CITYFLIGHT ATG Profile

This profile defines how CITYFLIGHT production requests use Agent Transaction Grammar without making ATG dependent on a specific media provider or frontend runtime.

## Mandate Shape

```json
{
  "type": "atg.media.cityflight.request",
  "subject": "world-or-experience-id",
  "authority": {
    "scope": ["plan", "estimate", "generate", "validate", "publish"],
    "spendCeiling": {
      "currency": "USD",
      "amount": 0
    },
    "expiresAt": null
  },
  "constraints": {
    "rightsReceiptRequired": true,
    "humanReleaseApprovalRequired": true,
    "nativeMobileApproved": false,
    "providerAdapters": []
  }
}
```

## Required Evidence

- identity and requester reference
- approved scene contract hash
- rights and provenance receipt
- provider capability check
- cost estimate
- spend approval reference
- generated asset hashes
- seam-validation report
- media-review decision
- deployment target and release approval

## Receipt States

```text
planning_only
awaiting_rights
awaiting_spend_approval
execution_authorized
execution_partial
execution_failed
validation_failed
release_rejected
release_approved
deployed
rolled_back
```

## Invariants

- A planning mandate cannot authorize paid execution.
- A spend ceiling cannot be silently increased.
- Provider substitution requires a new capability check and evidence record.
- Public release requires a distinct human approval from generation authorization.
- A visual manifest is evidence and presentation configuration, not game-state authority.
- Receipts must distinguish simulated, preview, unsigned, and verified states.
