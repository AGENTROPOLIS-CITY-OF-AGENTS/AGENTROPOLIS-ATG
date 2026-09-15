# Constitutional Inheritance v1

Status: canonical ATG integration note

## Purpose

Bind governed execution to the AGENTROPOLIS constitutional stack without turning constitutional text, SOUL, role, persona, context, or runtime state into execution authority.

## Inheritance order

```text
Founding Papers
  -> City Constitution
  -> Constitutional Ontology
  -> District Charter
  -> Agent Constitution / SOUL
  -> Role
  -> Mandate
  -> Execution Envelope
```

ATG begins enforcing executable semantics at the Mandate and Execution Envelope boundary. Upstream constitutional artifacts constrain interpretation and allowed behavior but do not independently grant permission.

## Kernel rule

A valid execution request requires machine-resolvable authority through the current identity, mandate, risk, policy, permission, and Execution Envelope path.

The following may influence planning or interpretation but may not independently authorize execution:

```text
Constitution
District Charter
SOUL
Role
Persona
Context Capsule
Memory
Model output
Harness session
Collaboration event
Retrieved knowledge
Tool availability
```

## Required invariants

- `SOUL != Authority`
- `Role != Authority`
- `Persona != Authority`
- `Context != Authority`
- `Memory != Authority`
- `Model != Authority`
- `Harness != Authority`
- `Communication != Authority`
- `Tool Availability != Permission`
- `Retrieval Access != Permission`
- `Receipt != Truth`

## Envelope derivation

```text
Human or governed agent intent
  -> constitutional constraints resolved
  -> identity resolved
  -> mandate resolved
  -> capability requested
  -> authority evaluated
  -> risk compiled
  -> Execution Envelope emitted
  -> Dispatch
  -> adapter-mediated execution
  -> evidence + receipt
  -> verification as required
```

No downstream worker may use SOUL, role, model confidence, system prompt, runtime identity, collaboration state, or prior successful execution as a substitute for current mandate and permission checks.

## Amendment and drift

ATG may carry references to ConstitutionVersion, amendment records, charter identifiers, SOUL identifiers, role identifiers, and constitutional-drift findings for provenance. ATG does not ratify constitutional amendments.

If conflicting constitutional sources are detected, execution that depends on the conflict must fail closed or escalate according to applicable policy and risk.

## Design law

> Constitution governs the actor. Mandate authorizes the mission. The Envelope constrains the execution.
