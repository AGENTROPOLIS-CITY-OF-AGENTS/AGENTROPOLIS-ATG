# ATG CONTINUITY Profile

Status: Draft
Version: 0.1.0

ATG CONTINUITY defines semantic references for a persistent AGENT-ENTITY moving across replaceable runtimes.

## Core semantic rule

```text
AGENT-ENTITY = actor
RUNTIME-BINDING = current execution attachment
CONTINUITY-PASSPORT = proof-backed continuity reference
```

ATG carries references. It does not mint identity truth or grant authority.

## Example semantic object

```json
{
  "type": "ATG.CONTINUITY",
  "agent_entity_id": "agt:axiom",
  "agent_did": "did:agentropolis:axiom",
  "runtime_binding_id": "runtime-binding:hermes:01",
  "continuity_passport_ref": "passport:axiom:current",
  "proof_refs": [
    "proof:identity:...",
    "proof:control:...",
    "proof:continuity:..."
  ]
}
```

## Link distinction

ATG LINK establishes a governed relationship with a surface, workspace, device, application, peer or runtime.

ATG CONTINUITY answers whether the actor on the new binding resolves to the same persistent AGENT-ENTITY.

```text
LINK = establish relationship
CONTINUITY = resolve same actor across relationships
```

Neither object is execution authority. Both remain subordinate to mandate, policy, Capability Grid and Execution Envelope.
