# AGENTROPOLIS Agentdex

Agentdex is a prototype registry interface for discovering agents through ATG-shaped metadata.

## Current status

This directory is a static, non-operational preview.

- No package is installed by the displayed command.
- No identity or receipt is cryptographically verified.
- No reputation score is computed.
- No MCP tool or autonomous execution is invoked.
- `agent.example.json` is non-normative and does not replace a future ATG schema or RFC.

## Purpose

A future Agentdex entry should expose:

1. identity and version
2. mandate and escalation path
3. capability declarations
4. authority and custody boundaries
5. evidence requirements
6. receipt states and verification
7. deployment and runtime constraints

## Run locally

From the repository root:

```bash
python3 -m http.server 8080
```

Open:

```text
http://localhost:8080/agentdex/
```

## Next implementation gates

- publish a normative ATG agent declaration schema
- validate entries before rendering
- sign publisher identity and release artifacts
- bind install commands to immutable package digests
- verify receipts independently
- separate self-asserted claims from audited evidence
- add revocation, versioning, and human approval flows
