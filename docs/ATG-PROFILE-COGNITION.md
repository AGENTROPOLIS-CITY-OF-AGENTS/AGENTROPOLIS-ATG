# ATG:COGNITION Profile

Status: Draft
Version: 0.1.0

## Purpose

ATG:COGNITION carries a human-facing cognitive presentation preference through AGENTROPOLIS without turning presentation style into authority, diagnosis, or employment scoring.

It recovers the useful parts of earlier WIRED CHAOS / NEUROMETAX builds:

- explicit user-selected explanation depth;
- adaptive guidance for beginners through advanced builders;
- progressive disclosure;
- low-stimulation / reduced information-load preferences;
- step-by-step task presentation;
- reusable NEURO communication profiles.

It intentionally does **not** recover diagnosis-based leadership, suitability, or stress scoring into hiring, access, compensation, eligibility, termination, or other high-impact decisions.

## Canonical presentation modes

### MAIN_STREET

For people who want the system to explain the task without assuming technical knowledge.

Defaults:

- plain language;
- define jargon immediately;
- one primary action at a time;
- progressive disclosure;
- examples before abstractions;
- visible next step;
- reduced information density by default.

### BUILDER

For people who understand products and workflows but do not need every implementation detail.

Defaults:

- moderate technical language;
- explain unfamiliar infrastructure terms;
- show architecture when it changes a decision;
- group related steps;
- include implementation implications;
- keep code optional unless requested.

### DEVELOPER

For people who want native technical detail.

Defaults:

- technical vocabulary allowed without basic definitions;
- contracts, schemas, interfaces, edge cases, tests, and failure modes first;
- code and exact integration points preferred;
- fewer explanatory analogies;
- dense output allowed unless the user selects lower verbosity.

## Verbosity is orthogonal

Presentation mode and response length are separate controls.

```text
presentation_mode = MAIN_STREET | BUILDER | DEVELOPER
text_verbosity    = LOW | MEDIUM | HIGH
```

A user may therefore select combinations such as:

- MAIN_STREET + HIGH
- BUILDER + LOW
- DEVELOPER + MEDIUM

A runtime such as Hermes may map `text_verbosity` to its own supported response-length control, but ATG does not require a specific provider command.

## Selection precedence

```text
explicit user selection
  > current session override
  > accepted adaptive suggestion
  > product default
```

Explicit user selection always wins.

## Adaptive guidance

Adaptive guidance is allowed only as a bounded suggestion based on observable interaction signals.

Permitted signals include:

- repeated requests for simpler wording;
- repeated requests for more technical depth;
- repeated clarification loops;
- explicit statements of confusion;
- explicit requests to skip basics;
- successful completion of a previously scaffolded task.

The system may suggest moving **one level** up or down. It must not silently jump modes when the profile is locked.

The system must not infer or store:

- a medical or psychiatric diagnosis;
- intelligence;
- disability status;
- education level;
- employability;
- competence or fitness.

## Low-stimulation and executive-function supports

ATG:COGNITION may express presentation supports such as:

- `progressive_disclosure`
- `one_action_at_a_time`
- `recap_after_branch`
- `show_progress`
- `reduced_visual_load`
- `low_stimulus`
- `examples_first`
- `checklist_mode`
- `preserve_context`
- `avoid_unnecessary_interruptions`

These are interaction preferences, not clinical conclusions.

## Semantic object

Example:

```json
{
  "profile": "ATG:COGNITION",
  "version": "0.1.0",
  "presentation_mode": "MAIN_STREET",
  "text_verbosity": "LOW",
  "jargon": "DEFINE",
  "step_density": "ONE_AT_A_TIME",
  "progressive_disclosure": true,
  "low_stimulus": true,
  "locked_by_user": true,
  "selection_source": "USER",
  "adaptive_guidance": {
    "enabled": true,
    "requires_acceptance": true,
    "max_tier_delta": 1
  }
}
```

## Runtime boundary

ATG carries the semantic preference. It does not own rendering or model routing.

```text
USER / AGENT PREFERENCE
  -> ATG:COGNITION
  -> policy / privacy boundary
  -> presentation adapter / CHAOS RANK runtime lane
  -> rendered response
  -> user override remains available
```

The profile must not:

- grant tool permission;
- widen a mandate;
- choose settlement rails;
- alter execution authority;
- bypass AEGIS;
- change evidence requirements.

## Employment and HR boundary

ATG:COGNITION may be used inside HR systems only for accessibility and interaction support.

It must not be an input to:

- candidate ranking;
- hiring recommendations;
- promotion or compensation decisions;
- termination decisions;
- eligibility gates;
- automated performance scoring.

If an HR system needs accommodation support, store and route the minimum preference data separately from ranking or selection models.

## Provenance

A persisted profile should record:

- profile version;
- selection source;
- timestamp;
- user-lock state;
- accepted adaptive changes;
- previous mode when changed;
- product/runtime that consumed it.

Do not persist raw conversation text merely to justify the profile when a compact event record is sufficient.

## Canonical rule

> ATG expresses how the human wants the system presented. It does not define what the human is.
