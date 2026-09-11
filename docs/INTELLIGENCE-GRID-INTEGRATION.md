# ATG Intelligence Grid Integration

ATG occupies the graph/compile boundary in the canonical chain:

```text
CREATOR-CORE -> ATG -> Utility Grid -> Hermes -> SENTINEL-6 -> AEGIS
```

## ATG obligations

- Compile intent into explicit task/agent graph structure.
- Assign risk tier before dispatch; executing agents must not self-classify their risk.
- Preserve identity, mandate, policy references, requested capability, and expected receipt semantics across graph edges.
- Route shared capabilities through Utility Grid rather than silently duplicating them.
- Emit versioned machine-readable contracts.
- Preserve unknown forward-compatible fields where safe.
- Never remove a contract field without a major version bump.
- Expose enough graph/evidence context for SENTINEL-6 verification and AEGIS policy evaluation.

## APCP

Every ATG capability must map to an implementation, language/runtime, toolchain, tests/fixtures, and evidence. Unsupported required coverage is a gap, not a PASS.

ATG does not grant itself authority. Authority remains constrained by Identity -> Mandate -> Policy -> Tool Permission -> Execution -> Receipt -> Audit.
