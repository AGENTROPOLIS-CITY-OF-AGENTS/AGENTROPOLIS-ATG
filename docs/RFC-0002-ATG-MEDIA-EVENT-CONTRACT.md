# RFC-0002: ATG Media Event Contract

## Status

Draft.

## Abstract

This RFC defines how ATG interaction events may be referenced by downstream visualization and media systems without allowing those systems to alter agent identity, authority, evidence, decisions, execution status, or receipts.

The contract supports AGENTROPOLIS-CREATOR, ASBE, CHRONOSCOPE, 789 STUDIOS, PBX, and governed MCP execution while remaining implementation-neutral.

## Design principle

> ATG records the operational meaning. Media systems may visualize that meaning, but may not become a competing source of truth.

## Event classes

Initial media-relevant event classes:

- `agent.entered`
- `agent.addressed`
- `identity.established`
- `capability.advertised`
- `proposal.issued`
- `challenge.raised`
- `evidence.presented`
- `mandate.granted`
- `task.delegated`
- `policy.denied`
- `consensus.reached`
- `execution.started`
- `execution.completed`
- `execution.failed`
- `receipt.issued`

Implementations may extend this list through versioned namespaces.

## Media hints

An ATG event may include non-authoritative media hints.

```json
{
  "message_type": "task.delegated",
  "sender": {
    "agent_id": "hermes-001",
    "role": "orchestrator"
  },
  "recipient": {
    "agent_id": "nexus-historian-04",
    "role": "temporal-researcher"
  },
  "mandate": {
    "id": "mandate-vesuvius-79",
    "scope": "research_only"
  },
  "payload": {
    "objective": "Verify ships, weather, population, and volcanic conditions"
  },
  "media": {
    "eligible": true,
    "preferred_render_level": "ambient",
    "interaction_style": "formal_delegation",
    "privacy_class": "public",
    "importance": 0.82
  }
}
```

Media hints do not grant execution authority, approve a provider, commit budget, authorize likeness use, or permit publication.

## Source binding

Every operational cinematic line, visual decision marker, authority transfer, evidence presentation, denial, consensus state, execution state, and receipt representation must bind to one or more ATG event identifiers.

```json
{
  "media_fragment_id": "fragment_091",
  "source_event_ids": ["event_118", "event_119"],
  "representation_type": "condensed_dialogue",
  "semantic_change": false
}
```

Narration and illustrative staging may be added, but must be labeled and must not contradict the event record.

## Representation states

Downstream systems must distinguish:

- `literal` — close rendering of the source event
- `condensed` — shortened without semantic change
- `reordered` — moved for narrative clarity while preserving causality disclosure
- `illustrative` — symbolic staging, not a literal record
- `narration` — explanatory content not spoken by the agent
- `simulation` — hypothetical or preview behavior

A simulation must never be presented as completed execution.

## Media receipt extension

A media receipt should include:

```json
{
  "receipt_type": "atg.media",
  "source_event_ids": [],
  "source_receipt_ids": [],
  "production_id": "prod_74c22",
  "creator_package": "creator_chronoscope_nexus_01@0.1.0",
  "scene_contract_hash": "sha256:...",
  "render_jobs": [],
  "provider_substitutions": [],
  "artifact_hashes": [],
  "representation_states": [],
  "review_status": "pending",
  "publication_status": "not_authorized"
}
```

The media receipt supplements, but does not replace, execution or authorization receipts.

## Prohibited transformations

A compliant implementation must not:

1. Invent an agent decision.
2. Attribute evidence to the wrong identity.
3. Depict authority outside the active mandate.
4. Hide or reverse a policy denial.
5. Convert disagreement into consensus.
6. Depict proposed, simulated, queued, or failed work as completed.
7. Omit a material provider substitution from the receipt.
8. Publish private interactions without separate authority.
9. Treat cinematic importance as operational priority.
10. allow media hints to bypass MCP policy or approval gates.

## Privacy and likeness

Agent visual identity, human likeness, voice, private conversation, and sensitive evidence are separate permissions. An event being media-eligible does not imply that all associated identities or payloads may be rendered or published.

## Compatibility

This RFC is compatible with any renderer or production system that can preserve event identifiers and emit a media receipt. CHRONOSCOPE and ASBE are reference consumers, not mandatory dependencies.

## Open questions

- Canonical schema namespace and versioning
- Signature and receipt linkage format
- Redaction rules for private payloads
- Cross-production event reuse
- Calibrated importance scoring
- Standard representation-state disclosures in player interfaces
