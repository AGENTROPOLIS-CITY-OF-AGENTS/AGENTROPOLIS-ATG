# ATG FASTPATH + Capability Acquisition Semantics

ATG defines the semantic contract for bounded specialists and runtime capability acquisition. It does not grant authority.

## FASTPATH evidence

Canonical semantic type:

`agentropolis-fastpath-evidence/v1`

Required meaning:

- specialist identity
- bounded task class
- immutable input binding
- immutable output binding
- validation state
- optional layout fingerprint
- execution timestamp
- explicit `authorityClaimed=false`

## Capability acquisition receipt

Canonical semantic type:

`agentropolis-capability-acquisition-receipt/v1`

Required meaning:

- capability identity
- source type
- connection identity
- exposed tool surface
- permission scope
- user approval state
- AEGIS approval state
- acquisition timestamp
- optional expiry
- explicit `grantsExecutionAuthority=false`

## Core laws

- capability discovery does not imply permission
- a connected MCP does not expand a mandate
- a specialist decision does not become policy
- UI success does not imply business or financial authorization
- economic intent still crosses into PAYRAIL and the governed economic fabric
- provenance may inform an Execution Envelope but may not replace it
