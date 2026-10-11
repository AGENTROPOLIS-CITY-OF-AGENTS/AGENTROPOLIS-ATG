# ATG Communication Profile

## Purpose

ATG expresses how an agent should communicate with a human without confusing communication style with reasoning power, authority, or intelligence.

The profile separates three independent controls:

1. **Reasoning** — how much deliberation the runtime should use.
2. **Verbosity** — how much text should be returned.
3. **Cognitive delivery** — how technical, dense, and assumption-heavy the explanation should be.

ATG carries this intent. Runtime adapters compile it into provider-specific controls where supported.

## User-selected audience modes

- **MAIN_STREET** — plain language, define jargon, simple examples, one obvious next step.
- **BUILDER** — assumes some technical familiarity but explains agentic and infrastructure concepts when needed.
- **ENGINEER** — native developer terminology, implementation detail, APIs, schemas, tests, and code when useful.
- **ARCHITECT** — full systems context, tradeoffs, boundaries, failure modes, governance, and cross-layer implications.
- **ADAPTIVE** — the user explicitly authorizes bounded behavioral adaptation.

The selected mode belongs to the user. The system may not silently relabel or downgrade it.

## Bounded behavioral adaptation

When adaptation is enabled, the system may temporarily adjust:

- chunk size
- pace
- terminology explanations
- examples
- detail level
- repetition
- interface information density

Permitted signals are interaction signals such as explicit requests, repeated clarification, repeated errors, task success, topic mastery, or navigation friction.

The system must not infer or store a global intelligence score, medical diagnosis, disability, or protected trait from behavior.

Domain familiarity is specific. A person may be advanced in software engineering and unfamiliar with custody, settlement, or agentic AI.

## Priority order

```text
EXPLICIT TURN OVERRIDE
        ↓
USER-SELECTED COMMUNICATION MODE
        ↓
USER-APPROVED ADAPTIVE SUPPORT
        ↓
DOMAIN FAMILIARITY
        ↓
SURFACE DEFAULT
        ↓
RUNTIME DEFAULT
```

Behavioral adaptation may refine delivery inside the selected mode. It does not replace the selected mode unless the user chose ADAPTIVE or explicitly changes modes.

## Example

```yaml
type: atg.communication.profile
version: 1.0.0
audience: builder
verbosity: low
reasoning: high
terminology: adaptive
examples: adaptive
code: when_helpful
domain_familiarity:
  software: working
  agentic_ai: learning
adaptation:
  enabled: true
  user_controlled: true
  may_adjust:
    - chunking
    - terminology
    - examples
    - detail
  signals:
    - explicit_request
    - repeated_clarification
    - task_success
  selected_mode_locked: true
```

Meaning: **think hard, answer briefly, talk to me like a technically capable builder, and explain agentic concepts when my interaction shows I need it.**

## Runtime compilation

Provider-specific adapters translate the ATG profile into native runtime controls when available.

Example for a Hermes runtime that supports text verbosity:

```text
ATG verbosity: low
        ↓
Hermes adapter
        ↓
agent.text_verbosity = low
```

Unsupported controls fall back to prompt assembly or presentation-layer behavior. Adapters must not pretend a native capability exists when it does not.

## Authority boundary

Communication profile fields never grant tool, financial, identity, policy, or execution authority.

**ATG defines the communication intent. The user owns the selected mode. The runtime adapts delivery. Governance still owns authority.**
