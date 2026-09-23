# ATG Overwatch Evidence Profile

## Purpose

Define the ATG semantic boundary for evidence entering from Omarchy Overwatch.

## Profile

`ATG:EVIDENCE/OVERWATCH`

Required semantic fields:

- evidence id
- source/provider
- retrieval time
- observed time when available
- feed state: LIVE | STALE | ERR | OFF
- provenance
- evidence payload reference
- optional geography
- derivation metadata when model/rule generated
- authority class: OBSERVATION
- executable: false

## Invariants

ATG describes the evidence and its authority references. ATG does not upgrade evidence into authority.

```text
ATG:EVIDENCE/OVERWATCH
  -> ATG:VERIFY
  -> optional domain profile such as ATG:MARKET
  -> mandate + policy references
  -> Execution Envelope
```

A LIVE state means the adapter currently considers the source responsive/current under its own policy. It does not mean verified truth.

A model brief MUST be marked derived and MUST retain links to the underlying evidence ids.

An ERR or STALE item remains representable and auditable rather than being silently dropped.
