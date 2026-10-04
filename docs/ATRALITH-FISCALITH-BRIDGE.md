# ATRALITH / FISCALITH Bridge

ATG transports financial meaning without owning it.

## Message contract

Every financial ATG message MUST carry exactly one provider-neutral FISCALITH payload (`fiscalith_payload`) and a `schema_ref` naming the pinned FISCALITH schema. A message without `fiscalith_payload` is not a financial speech act and takes the legacy compatibility path; it is never compiled by this bridge.

Every financial ATG message MUST also carry:
- sender and recipient AGENTENTITY references;
- correlation id (stable per conversation; replay rejection and idempotency are enforced by 54T, not ATG);
- mandate reference when authority is required (REQUEST, ACCEPT, DELEGATE);
- delegation chain (empty when not delegated);
- capability references;
- Execution Envelope reference (null until assigned);
- requested proof classes.

The envelope never carries `rail`, `provider`, `chain`, `wallet` or `signer` fields. Their presence anywhere in the envelope or at the payload top level is a boundary violation and the message is rejected.

Canonical example (validates against `contracts/core/atralith-financial-message.schema.json`):

```json
{
  "speech_act": "REQUEST",
  "from_agent_entity_ref": "AGENTENTITY:TREASURY-042",
  "to_agent_entity_ref": "AGENTENTITY:VENDOR-12",
  "correlation_id": "corr-0001",
  "mandate_ref": "M-881",
  "delegation_chain": ["AGENTENTITY:CFO-01", "AGENTENTITY:TREASURY-042"],
  "capability_refs": ["cap.fiscalith.pay"],
  "execution_envelope_ref": null,
  "requested_proof_classes": ["ProofOfExecution", "ProofOfSettlement", "ProofOfOutcome"],
  "fiscalith_payload": {
    "intent_id": "fi-0001",
    "kind": "PAY",
    "actor_ref": "AGENTENTITY:TREASURY-042",
    "mandate_ref": "M-881",
    "payload": {"counterparty": "VENDOR-12", "asset": "USDC", "amount": "4200"}
  },
  "schema_ref": "https://agentropolis.dev/fiscalith/financial-intent.v1.json"
}
```

## Compilation boundary

```text
ATG message
  -> detect financial speech act
  -> validate FISCALITH payload
  -> preserve ATG identity / delegation / mandate context
  -> hand to governance and execution corridor
```

ATG compilation MUST NOT choose a settlement rail. The compiled handoff always targets `EXECUTION_ENVELOPE` as its next hop and carries `grants_authority = false`; AEGIS decides authority, 54T protects the boundary, and PAYRAIL routes only when production execution is approved.

## Result mapping

Provider-specific execution results are normalized into FISCALITH result objects and then communicated as ATG receipts, denials, reviews or escalations:

| FISCALITH result | ATG speech act |
| --- | --- |
| `SETTLED` (verified finality only) | `RECEIPT` |
| `REFUSED`, `FAILED` | `REFUSE` |
| `PENDING`, `PARTIAL` | `VERIFY` (neither failure nor settlement) |
| any result with `escalation_required: true` | `ESCALATE` |

A provider reporting inclusion before required finality is `PENDING`, not `SETTLED`. The mapped ATG message carries the result as `fiscalith_payload`, adds no authority fields, and does not mutate AGENTENTITY state.

## Non-duplication

Financial schemas belong to AGENTROPOLIS-FISCALITH.
ATG may reference versioned FISCALITH schemas but MUST NOT fork them. Pinned versions and digests live in `registries/fiscalith-schemas.yaml`.

## Executable surface

- `contracts/core/atralith-financial-message.schema.json` — ATG-owned envelope schema; `fiscalith_payload` is opaque.
- `registries/fiscalith-schemas.yaml` — pinned FISCALITH schema id, version, source commit and sha256.
- `atralith/fiscalith_bridge.py` — `detect_financial_speech_act`, `compile_financial_message(message, payload_validator)`, `map_result_to_atg(result, correlation_id)`, `CorridorHandoff`.
- `tests/test_fiscalith_bridge.py` — run with `python -m unittest discover -s tests`; enforced by `.github/workflows/ci.yml`.
