# ATG:COGNITION Profile

Status: Draft
Version: 0.2.0

## Purpose

ATG:COGNITION carries a human-facing presentation and workstyle preference through AGENTROPOLIS without turning presentation style into authority, diagnosis, identity classification, or employment scoring.

It recovers the useful parts of earlier WIRED CHAOS / NEURO HR builds while keeping three controls independent:

```text
presentation_mode = MAIN_STREET | BUILDER | DEVELOPER
text_verbosity    = LOW | MEDIUM | HIGH
workstyle.primary = ARCHITECT | SPARK | ANCHOR | PHANTOM
```

A person may use any combination. None of these values grants tools, changes policy, selects settlement rails, or determines job suitability.

## Axis 1: presentation mode

### MAIN_STREET
For people who want the system explained without assumed technical knowledge.

Defaults:
- plain language
- define jargon immediately
- one primary action at a time
- progressive disclosure
- examples before abstractions
- visible next step
- reduced information density by default

### BUILDER
For people who understand products and workflows but do not need every implementation detail.

Defaults:
- moderate technical language
- explain unfamiliar infrastructure terms
- show architecture when it changes a decision
- group related steps
- include implementation implications
- keep code optional unless requested

### DEVELOPER
For people who want native technical detail.

Defaults:
- technical vocabulary allowed without basic definitions
- contracts, schemas, interfaces, edge cases, tests, and failure modes first
- code and exact integration points preferred
- fewer explanatory analogies
- dense output allowed unless lower verbosity is selected

## Axis 2: text verbosity

Response length is orthogonal to presentation mode and workstyle.

```text
LOW    = concise
MEDIUM = normal detail
HIGH   = expanded detail
```

A runtime such as Hermes may map `text_verbosity` to its supported response-length control.

## Axis 3: NEURO workstyle

These are selectable interaction and workflow modes recovered from the early Neuro HR concept. They are not diagnoses or personality tests.

### ARCHITECT
Pattern mapper and strategic planner.

Prefer:
- system maps
- dependencies
- sequencing
- tradeoffs
- explicit constraints
- architecture before implementation

### SPARK
Creative generator and nonlinear explorer.

Prefer:
- option generation
- rapid branching
- examples
- idea capture
- short creative bursts
- permission to explore before converging

### ANCHOR
Stabilizer for process, quality, and consistency.

Prefer:
- checklists
- stable state
- visible progress
- QA gates
- reduced context switching
- predictable next actions

### PHANTOM
Deep-focus researcher, writer, and coder.

Prefer:
- low interruption
- bounded autonomous work blocks
- compact prompts
- fewer check-ins
- deep research/build time
- concise handoff plus receipt at the end

A profile may optionally carry a secondary mode or weighted blend. User selection always wins.

## Selection precedence

```text
explicit user selection
  > current session override
  > accepted adaptive suggestion
  > product default
```

## Adaptive guidance

Adaptive guidance is allowed only as a bounded suggestion based on observable interaction signals.

Permitted signals include:
- repeated requests for simpler wording
- repeated requests for more technical depth
- repeated clarification loops
- explicit statements of confusion
- explicit requests to skip basics
- explicit preference for fewer interruptions
- repeated requests for checklists, options, plans, or deep-work handoffs

The system must not infer or store:
- medical or psychiatric diagnosis
- intelligence
- disability status
- education level
- employability
- competence or fitness

When the workstyle or presentation profile is locked by the user, changes require acceptance.

## Interaction supports

ATG:COGNITION may express:
- `PROGRESSIVE_DISCLOSURE`
- `ONE_ACTION_AT_A_TIME`
- `RECAP_AFTER_BRANCH`
- `SHOW_PROGRESS`
- `REDUCED_VISUAL_LOAD`
- `LOW_STIMULUS`
- `EXAMPLES_FIRST`
- `CHECKLIST_MODE`
- `PRESERVE_CONTEXT`
- `AVOID_UNNECESSARY_INTERRUPTION`
- `SYSTEM_MAP_FIRST`
- `OPTIONS_FIRST`
- `DEEP_WORK_BLOCK`
- `QA_GATE`

These are interaction preferences, not clinical conclusions.

## Semantic object

```json
{
  "profile": "ATG:COGNITION",
  "version": "0.2.0",
  "presentation_mode": "MAIN_STREET",
  "text_verbosity": "LOW",
  "workstyle": {
    "primary": "ANCHOR",
    "secondary": "ARCHITECT",
    "locked_by_user": true,
    "selection_source": "USER"
  },
  "supports": [
    "ONE_ACTION_AT_A_TIME",
    "SHOW_PROGRESS",
    "CHECKLIST_MODE"
  ],
  "adaptive_guidance": {
    "enabled": true,
    "requires_acceptance": true,
    "max_tier_delta": 1
  }
}
```

## Runtime boundary

```text
USER / AGENT PREFERENCE
  -> ATG:COGNITION
  -> policy / privacy boundary
  -> presentation + workstyle adapter
  -> Hermes / application renderer
  -> rendered response
  -> user override remains available
```

The profile must not:
- grant tool permission
- widen a mandate
- choose settlement rails
- alter execution authority
- bypass AEGIS
- change evidence requirements
- alter candidate or employee ranking

## Employment and HR boundary

ATG:COGNITION may be used inside HR systems for accessibility, onboarding, communication, task presentation, and voluntary workflow support.

It must not be an input to:
- candidate ranking
- hiring recommendations
- promotion or compensation decisions
- termination decisions
- eligibility gates
- automated performance scoring

Any legacy diagnosis-derived scoring logic is non-canonical and must not be restored into employment decision systems.

## Provenance

Persisted profiles should record:
- profile version
- selection source
- timestamp
- user-lock state
- accepted adaptive changes
- previous presentation mode when changed
- previous workstyle when changed
- product/runtime that consumed the profile

The quartet ARCHITECT, SPARK, ANCHOR, and PHANTOM is recovered project canon from the early Neuro HR work. Surviving GitHub evidence verifies the Neurodivergent HRM, Emergent, and later Vercel lineage, but the exact original quartet source file has not yet been rehydrated. Keep that distinction visible in provenance records.

## Canonical rule

> ATG expresses how the human wants the system presented and supported. It does not define what the human is.
