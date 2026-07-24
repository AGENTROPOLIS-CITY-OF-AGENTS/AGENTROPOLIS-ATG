# RFC-0002: Cognitive Coverage Protocol

**Status:** Draft  
**Category:** Decision quality and governed reasoning  
**Applies to:** ATG transactions, ATRALITH implementations, MCP routing, Mission Control, AEGIS policy gates, and AGENTROPOLIS-OPS

## Abstract

ATG defines a machine-readable way to declare which reasoning lenses a consequential transaction requires, which assessments were completed, what evidence supports them, and whether execution is blocked by missing coverage or unresolved conflict.

This protocol does **not** claim that agents are conscious or possess human personality types. The Jungian eight-function model is used only as an error-correction vocabulary for structured cognitive plurality.

## Cognitive function identifiers

| ID | Operational meaning | Core question |
|---|---|---|
| `NI_FORESIGHT` | Direction and long-range consequences | Where is this leading? |
| `NE_SCENARIOS` | Alternatives and second-order possibilities | What else could happen? |
| `TI_CONSISTENCY` | Internal logic and structural coherence | Does the reasoning hold together? |
| `TE_EXECUTION` | Implementation, measurement, and operational efficiency | Can this be executed and verified? |
| `FI_INTEGRITY` | Mandate fidelity, values, and non-negotiable constraints | Does this violate the principal's intent? |
| `FE_IMPACT` | Stakeholder and institutional consequences | Who is affected and how? |
| `SI_PRECEDENT` | Historical evidence, prior incidents, and learned constraints | What happened before? |
| `SE_REALITY` | Current state, direct observation, and live evidence | What is true right now? |

## Normative transaction object

```json
{
  "cognitive_coverage": {
    "profile": "A2_BOUNDED",
    "required": ["NI_FORESIGHT", "TI_CONSISTENCY", "TE_EXECUTION", "SI_PRECEDENT", "SE_REALITY"],
    "completed": ["NI_FORESIGHT", "TI_CONSISTENCY", "TE_EXECUTION"],
    "missing": ["SI_PRECEDENT", "SE_REALITY"],
    "dominant": "TE_EXECUTION",
    "counterweight_required": "SI_PRECEDENT",
    "conflicts": [],
    "status": "BLOCKED_MISSING_COVERAGE"
  }
}
```

## Status values

- `NOT_REQUIRED`
- `PENDING`
- `COMPLETE`
- `BLOCKED_MISSING_COVERAGE`
- `BLOCKED_MISSING_EVIDENCE`
- `BLOCKED_CONFLICT`
- `HUMAN_REVIEW_REQUIRED`

## Assessment object

```json
{
  "assessment_id": "cog_01J...",
  "function": "SE_REALITY",
  "subject": "action:deploy-staging",
  "claim": "The staging target is healthy and reachable.",
  "evidence_refs": ["obs://staging/health/8421"],
  "confidence": 0.94,
  "contradictions": [],
  "recommendation": "CONTINUE",
  "assessor": "agent:runtime-observer",
  "created_at": "2026-07-22T22:00:00Z"
}
```

Assessments MUST identify the assessor and supporting evidence. Unsupported certainty MUST NOT satisfy required cognitive coverage.

## Counterweight pairs

```text
NI_FORESIGHT   <-> SE_REALITY
NE_SCENARIOS   <-> SI_PRECEDENT
TI_CONSISTENCY <-> FE_IMPACT
TE_EXECUTION   <-> FI_INTEGRITY
```

Counterweights are error-correction relationships, not authorization relationships.

## Authorization separation

Cognitive coverage MAY recommend, challenge, or block readiness. It MUST NOT grant authority.

```text
cognitive completeness != permission
capability availability != authority
valid plan != valid mandate
```

Execution remains subject to identity, mandate, policy, authorization class, evidence, signer or capability scope, and receipt requirements defined by RFC-0001.

## Risk-based minimum profiles

| Authorization class | Suggested minimum coverage |
|---|---|
| `A0_OBSERVE` | `TI_CONSISTENCY`, `SE_REALITY` |
| `A1_REVERSIBLE` | task-specific subset; at least one validation lens |
| `A2_BOUNDED` | `TI_CONSISTENCY`, `TE_EXECUTION`, `SI_PRECEDENT`, `SE_REALITY` plus consequence-specific lenses |
| `A3_IRREVERSIBLE` | all eight functions unless policy documents a narrower equivalent control set |
| `A4_ROOT` | all eight functions, independent reviewers, separation of duties, and human or quorum authorization |

## Conflict object

```json
{
  "conflict_id": "conflict_01J...",
  "between": ["TE_EXECUTION", "SI_PRECEDENT"],
  "positions": [
    {"function": "TE_EXECUTION", "claim": "Deployment checks passed."},
    {"function": "SI_PRECEDENT", "claim": "The same dependency caused capability leakage previously."}
  ],
  "resolution": "REQUIRE_CANARY_AND_PERMISSION_DIFF",
  "resolved_by": "policy:aegis/deploy-17",
  "status": "RESOLVED"
}
```

Unresolved material conflict MUST block `A3_IRREVERSIBLE` and `A4_ROOT` actions.

## Receipt requirements

A consequential action receipt SHOULD include:

```json
{
  "cognitive_receipt": {
    "required": ["..."],
    "completed": ["..."],
    "assessment_hashes": ["sha256:..."],
    "evidence_hashes": ["sha256:..."],
    "conflicts": ["conflict_01J..."],
    "coverage_status": "COMPLETE",
    "policy_profile": "A3_IRREVERSIBLE"
  }
}
```

Receipts MUST NOT claim a function was completed unless a corresponding assessment and evidence record exists.

## Mission Control presentation

Mission Control SHOULD display cognitive coverage as a decision-quality panel while keeping the human mandate at the center. Labels MUST avoid claims of machine sentience, enlightenment, emotion, or psychological diagnosis.

## Decision

ATG SHOULD adopt cognitive coverage as an optional extension for low-risk transactions and a policy-selectable requirement for consequential transactions.

> No reasoning lens may authorize itself, certify its own blind spot, or rewrite the mandate to fit its conclusion.
