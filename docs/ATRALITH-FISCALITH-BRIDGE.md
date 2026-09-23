# ATRALITH / FISCALITH Bridge

ATG transports financial meaning without owning it.

## Message contract

Every financial ATG message SHOULD carry:
- sender and recipient AGENTENTITY references;
- correlation id;
- mandate reference when authority is required;
- delegation chain when delegated;
- capability references;
- Execution Envelope reference when available;
- requested proof classes;
- one provider-neutral FISCALITH payload.

## Compilation boundary

```text
ATG message
  -> detect financial speech act
  -> validate FISCALITH payload
  -> preserve ATG identity / delegation / mandate context
  -> hand to governance and execution corridor
```

ATG compilation MUST NOT choose a settlement rail.

## Result mapping

Provider-specific execution results are normalized into FISCALITH result objects and then communicated as ATG receipts, denials, reviews or escalations.

## Non-duplication

Financial schemas belong to AGENTROPOLIS-FISCALITH.
ATG may reference versioned FISCALITH schemas but MUST NOT fork them.
