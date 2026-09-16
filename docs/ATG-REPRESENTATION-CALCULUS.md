# ATG Representation Calculus

Status: proposed ATG language domain
Date: 2026-09-15

## Purpose

ATG Representation Calculus gives agents a governed language for expressing **what may change in a representation, what must survive, how much distortion is acceptable, and what evidence is required**.

It generalizes quantization. EXL3 is an implementation adapter; it is not the language.

## Core form

```atg
REPRESENT <subject>
  AS <representation-class>
  FOR <purpose>
  PRESERVE <invariants>
  ALLOW <bounded-transformations>
  FIDELITY <constraint>
  DISTORTION <budget>
  ROUTE <policy>
  VERIFY <criteria>
  RECEIPT <required-evidence>
```

## Quantization form

```atg
QUANTIZE model:qwen3.8-27b
  FOR local_inference
  PRESERVE identity, mandate, provenance, quality_floor
  ALLOW exl3, gguf, awq, gptq
  TARGET memory_fit(device_passport)
  FIDELITY task_acceptance >= required
  DISTORTION measured_and_declared
  ROUTE torque.adaptive
  VERIFY benchmark(task_suite), reproducibility, vram_peak
  RECEIPT model_representation
```

`TARGET` is intent, not an implementation command. A compatible adapter may select EXL3 target BPW, another quantization family, remote execution, or no quantization when policy and evidence require it.

## Continuity form

```atg
CONTINUE agent:<agent_id>
  ACROSS model_change, runtime_change, context_compaction
  PRESERVE identity, lineage, material_memory, mandate_history, receipts
  REAUTHORIZE current_mandate
  VERIFY continuity_evidence
  RECEIPT continuity
```

Continuity never carries authority implicitly. Current authority must resolve independently.

## Fleet form

```atg
TORQUE fleet:<fleet_run>
  OPTIMIZE verified_output
  AGAINST context_entropy, collision_risk, integration_rework, cost, thermal_pressure
  ADJUST cells, parallelism, recursion_depth, verifier_ratio, model_mix, context_budget
  PRESERVE authority_envelopes, ownership_leases, independent_verification
  RECEIPT fleet_topology
```

This makes fleet topology itself a representation/optimization surface without equating more agents with more authority.

## Representation primitives

- `REPRESENT` — create or select a derived representation.
- `TRANSFORM` — declare a change between representations.
- `PRESERVE` — name invariants that cannot be lost.
- `ALLOW` — bound permitted transform families.
- `FIDELITY` — state minimum task-appropriate faithfulness.
- `DISTORTION` — state tolerated loss/approximation and measurement rule.
- `CONTINUE` — assert continuity subject to evidence.
- `FORK` — create a new lineage branch rather than claim continuity.
- `CHECKPOINT` — preserve a reconstructable state before transformation.
- `REHYDRATE` — restore context/state from a declared source.
- `TORQUE` — request adaptive optimization under constraints.
- `VERIFY` — bind acceptance criteria and verifier independence.
- `RECEIPT` — require durable transformation evidence.

## Compiler invariants

The ATG compiler MUST reject or escalate a representation instruction when:

1. preserved invariants are incompatible with the requested transform;
2. the transform would broaden authority;
3. material distortion has no declared budget or verification method;
4. provenance cannot be retained for consequential evidence;
5. continuity is asserted without sufficient lineage evidence;
6. destructive transformation lacks a preservation/checkpoint rule where policy requires one;
7. the requested implementation is unsupported by the selected runtime and no authorized fallback exists.

## Adapter model

ATG describes intent. Adapters implement it.

Examples:

- EXL3 / ExLlamaV3 adapter
- GGUF / llama.cpp-compatible adapter
- AWQ / GPTQ adapters
- provider-managed quantization adapter
- context compaction adapter
- KV-cache representation adapter
- 3D/LOD/media representation adapter
- fleet topology adapter
- memory migration adapter

Adapters cannot alter ATG authority semantics.

## Receipt minimum

A representation receipt SHOULD include:

```yaml
subject_id:
source_representation:
target_representation:
transform_family:
purpose:
preserved_invariants: []
declared_distortion:
measured_fidelity:
source_evidence: []
runtime:
hardware_profile:
authority_envelope:
verification:
reversible:
checkpoint:
continuity_claim:
lineage_event:
```

## Constitutional relationship

ATG Representation Calculus implements the Founding Papers' Representation Integrity principle. It cannot weaken that principle. Quantization Torque may optimize a representation only inside the resulting ATG contract.
