# ATG Profile: CONNECTOME

## Status

Production protocol profile for connectome-derived cognitive state entering the AGENTROPOLIS execution corridor.

## Purpose

ATG:CONNECTOME defines how a Connectome Layer may publish bounded cognitive state, request routing, cue memory, escalate to model reasoning, inhibit action, or propose an external intent without owning identity, mandate, authority, policy, truth, or execution permission.

## Canonical rule

```text
CONNECTOME STATE
   -> ATG:CONNECTOME EVENT
   -> IDENTITY + MANDATE RESOLUTION
   -> POLICY + AUTHORITY
   -> EXECUTION ENVELOPE
   -> APPROVED ADAPTER
   -> RESULT + RECEIPT
```

Activation is not authority. Salience is not truth. Reflex is not permission.

## Message types

- `CONNECTOME.OBSERVATION`
- `CONNECTOME.SALIENCE`
- `CONNECTOME.MEMORY_CUE`
- `CONNECTOME.SPECIALIST_ROUTE`
- `CONNECTOME.MODEL_ESCALATION`
- `CONNECTOME.INHIBITION`
- `CONNECTOME.ACTION_PROPOSAL`
- `CONNECTOME.STATE_UPDATE`

## Required fields

Every message MUST include:

- `type`
- `version`
- `message_id`
- `agent_id`
- `topology_id`
- `timestamp`
- `source_event_id` when derived from an external event
- `provenance`
- `authority_state`

`authority_state` MUST be `NONE` for raw activation, salience, memory-cue, specialist-route, and model-escalation messages.

## Action proposal

`CONNECTOME.ACTION_PROPOSAL` MAY propose an action but MUST NOT declare itself authorized.

```json
{
  "type": "CONNECTOME.ACTION_PROPOSAL",
  "version": "1.0",
  "message_id": "msg:c-8841",
  "agent_id": "agent:example",
  "topology_id": "connectome:hybrid-v3",
  "timestamp": "2026-09-13T23:00:00Z",
  "source_event_id": "event:991",
  "intent": {
    "capability": "device.stop_process",
    "target": "process:render-worker-7",
    "reason": "thermal anomaly reflex"
  },
  "confidence": 0.92,
  "authority_state": "NONE",
  "provenance": ["observation:thermal-991"]
}
```

The proposal then enters normal ATG mandate, policy, authority, risk, execution-envelope, adapter, receipt, and verification handling.

## Reflex semantics

A reflex route MAY skip expensive model reasoning. It MUST NOT skip ATG governance.

```text
SENSOR
 -> CONNECTOME REFLEX
 -> CONNECTOME.ACTION_PROPOSAL
 -> ATG AUTHORITY CHECK
 -> EXECUTION ENVELOPE
 -> ADAPTER
 -> RECEIPT
```

## Memory semantics

A `CONNECTOME.MEMORY_CUE` requests bounded retrieval or prioritization. It MUST NOT:

- alter sovereign memory by itself
- overwrite canonical evidence
- claim that retrieved content is true because it was salient
- broaden access beyond the agent/task memory policy

## Model escalation

A `CONNECTOME.MODEL_ESCALATION` requests reasoning from an approved model route. The profile SHOULD include:

- reason for escalation
- requested cognitive function or specialist role
- context budget
- privacy class
- latency sensitivity
- cost ceiling when available
- fallback behavior

The model remains replaceable and does not become the agent identity or authority source.

## Inhibition

`CONNECTOME.INHIBITION` may recommend suppressing, delaying, or escalating an intent when instability, conflict, uncertainty, drift, or entropy thresholds are exceeded. Policy determines whether the inhibition is advisory or blocking.

## Thermodynamic fields

Implementations SHOULD expose relevant measurements:

- `activation_density`
- `propagation_depth`
- `recurrent_loop_count`
- `entropy`
- `drift`
- `stability`
- `latency_ms`
- `compute_cost`
- `model_escalation_rate`

## Provenance

When a topology is based on a biological connectome, provenance MUST reference the source dataset/version and transformation lineage. This profile does not certify scientific fidelity or biological equivalence.

## Security invariants

- connectome activation cannot grant authority
- topology data cannot carry executable credentials
- a learned topology cannot expand its own permissions
- fast paths remain governed paths
- model escalation cannot silently broaden tool access
- state updates must be versioned and attributable
- high-risk external actions remain subject to progressive governance, AEGIS, and applicable human approval

## Standing rule

> **ATG:CONNECTOME lets cognition speak to the Grid. It does not let cognition crown itself king.**
