# ATG Compute Execution Profile

Status: Draft
Version: 0.1.0

## Purpose

This profile defines how ATG messages describe governed compute execution without coupling ATG to any programming language, compiler, accelerator framework, model provider, or hardware vendor.

ATG remains the semantic and transaction grammar. Atranic remains the structured semantic language carried by ATG messages. ATRALITH and other conforming implementations may translate an authorized ATG compute request into a compatible execution target such as Python, TypeScript, Rust, WASM, Mojo, MAX, CUDA-backed infrastructure, local CPU execution, or another registered runtime.

Core rule:

> ATG describes the authorized computation. Execution backends decide how that computation runs.

## Non-goals

This profile does not:

- add Mojo syntax to ATG or Atranic
- make Mojo, MAX, CUDA, Python, Rust, or any other runtime a constitutional dependency
- require AGENTROPOLIS adopters to run ATRALITH
- allow a runtime selector to bypass mandate, policy, risk, accounting, or receipt controls
- treat model output as execution authority

## Execution corridor

```text
Human or Agent Intent
        -> HLF / input interpretation layer
        -> Atranic semantic expression
        -> ATG mandate and capability request
        -> ATRALITH or conforming implementation
        -> capability resolution
        -> policy / risk / 54-T verification
        -> Quantization Torque attention and compute budgeting
        -> execution target selection
        -> Utility Grid execution
        -> verification
        -> ATG receipt
        -> economic accounting / $XENTS where applicable
```

HLF is referenced only as an upstream input/interpretation layer. This profile does not define HLF semantics or alter HLF.

## Required fields

A conforming compute execution object SHOULD include:

- `request_id` - stable request identifier
- `capability` - requested compute capability
- `execution` - runtime and target requirements
- `resources` - bounded compute requirements
- `authority` - mandate and capability-handle references
- `policy` - applicable risk and execution policy references
- `accounting` - utility metering and settlement metadata
- `receipt` - verification and provenance requirements

## Capability model

Compute capabilities SHOULD describe the job rather than the implementation.

Examples:

- `compute.execute`
- `compute.kernel`
- `compute.inference`
- `compute.quantize`
- `compute.compile`
- `compute.benchmark`
- `compute.profile`

Implementation-specific capabilities MAY be exposed as scoped handles when necessary, for example:

- `compute.runtime.mojo`
- `compute.accelerator.max`
- `compute.device.gpu`

However, callers SHOULD prefer implementation-neutral capabilities unless they require a specific backend for reproducibility, compatibility, benchmarking, or policy reasons.

## Execution target object

Example:

```yaml
execution:
  target: mojo
  runtime_version: "1.0.0"
  accelerator_framework: max
  accelerator_version: "26.5"
  target_class: gpu
  portability: preferred
  fallback_allowed: true
```

The `target` field identifies a registered execution backend. It does not modify ATG semantics.

## Runtime selection

A conforming implementation SHOULD select the smallest verified execution surface that satisfies the mandate.

Selection MAY consider:

1. capability compatibility
2. required precision and determinism
3. latency and throughput objectives
4. local versus remote availability
5. CPU, GPU, memory, battery, and thermal budgets
6. trusted-computing and credential boundaries
7. provider and licensing constraints
8. Utility Grid price and economic policy
9. Quantization Torque context and cognition budget
10. reproducibility requirements

Runtime selection MUST NOT expand authority beyond the originating mandate.

## Mojo and MAX

Mojo and MAX are execution targets, not ATG language extensions.

A conforming implementation MAY use Mojo for compiled CPU/GPU workloads and MAY use MAX accelerator libraries or inference infrastructure when the registered target and device capabilities satisfy the request.

The runtime boundary SHOULD preserve this separation:

```text
ATG / Atranic = meaning, mandate, authority, evidence
ATRALITH = implementation, validation, translation, routing
Mojo / MAX = execution
Utility Grid = delivery and metering
54-T / policy layer = verified capability and risk boundaries
$XENTS = optional economic accounting and settlement unit
```

## Fallback behavior

If a preferred runtime is unavailable, an implementation MAY select another compatible runtime only when:

- `fallback_allowed` is true
- the fallback satisfies the same capability and authority constraints
- required determinism and compatibility guarantees remain satisfied
- the receipt records both the requested target and actual target

A fallback MUST NOT silently reduce a security, privacy, provenance, or approval guarantee.

## Utility Grid metering

When execution consumes AGENTROPOLIS Utility Grid resources, accounting SHOULD record at least:

- agent or principal identifier
- district or application identifier when applicable
- execution target
- runtime version
- device class
- CPU time
- accelerator time
- peak memory where available
- compile time where applicable
- execution time
- provider cost where applicable
- internal Utility Grid charge
- `$XENTS` amount or settlement reference when enabled
- receipt identifier

## Receipt requirements

A compute execution receipt SHOULD record:

- stable request and mandate identifiers
- requested capability
- requested execution target
- actual execution target
- runtime and accelerator versions
- device class and provider class
- artifact or source digest when applicable
- policy decision and capability-handle references
- timing and resource measurements
- verification state
- result digest or artifact pointer
- accounting state
- fallback or downgrade events

## Security requirements

Implementations MUST NOT place raw production secrets in ATG messages, model context, runtime logs, or receipts.

Execution targets receive scoped capability handles or sealed credentials rather than raw secrets.

Runtime-generated output is untrusted until verification completes.

Remote execution SHOULD be treated as external infrastructure and MUST pass the same authority, egress, provenance, and receipt requirements as local execution.

## Compatibility

The profile is intentionally runtime-neutral. New execution targets can be added without revising ATG core semantics as long as they conform to this profile and the execution-target registry.

The registry is descriptive and versioned. It is not an allow-all list. Local policy determines which targets are permitted for a given principal, district, device, or mandate.
