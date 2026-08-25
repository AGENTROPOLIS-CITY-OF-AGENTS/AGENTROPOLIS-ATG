# Cognitive Runtime Namespace Guard

ATG is **Atralith**, the AGENTROPOLIS agentic language.

External cognitive-runtime frameworks, model routers, task schedulers, traffic controllers, inference-time control suites, and benchmark harnesses are not ATG and must not redefine the ATG namespace.

## Boundary

- `ATG` = Atralith agentic language.
- `AGENTROPOLIS::JSPACE` = AGENTROPOLIS JSpace.
- `external.tiger.jspace-v3.6` = third-party J-Space Cognition Suite runtime profile candidate.
- Cognitive-runtime routing is owned by CHAOS RANK under AEGIS qualification.
- External capability transport is bounded by AGENTROPOLIS-AGENT-MCP.

Atralith may express or reference a runtime-profile request in an authorized command, but the language itself does not grant qualification, routing authority, model permissions, tool permissions, or production approval.

## Example

An Atralith instruction may resolve to a structured request such as:

```text
profile.request(external.tiger.jspace-v3.6)
```

The request must still pass:

```text
Atralith expression
  -> runtime parser
  -> CHAOS RANK routing
  -> AEGIS qualification
  -> policy/capability gates
  -> approved execution or base-runtime fallback
```

This prevents syntax from becoming authority.
