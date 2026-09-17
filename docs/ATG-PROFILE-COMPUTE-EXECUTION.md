# ATG Compute Execution Profile

Status: Draft
Version: 0.2.0

## Purpose

This profile defines how ATG messages describe governed compute execution without coupling ATG to any programming language, compiler, accelerator framework, model provider, hardware vendor, or settlement rail.

ATG remains the semantic and transaction grammar. Atranic remains the structured semantic language carried by ATG messages. ATRALITH and other conforming implementations may translate an authorized ATG compute request into a compatible execution target such as Python, TypeScript, Rust, WASM, Mojo, MAX, CUDA-backed infrastructure, local CPU execution, or another registered runtime.

Core rule:

> ATG describes authorized intent, constraints, resources, and evidence requirements. Execution backends decide how that computation runs. Economic settlement is owned by the economic/payment infrastructure layer, not ATG.

## Non-goals

This profile does not:

- add Mojo syntax to ATG or Atranic
- make Mojo, MAX, CUDA, Python, Rust, or any other runtime a constitutional dependency
- require AGENTROPOLIS adopters to run ATRALITH
- allow a runtime selector to bypass mandate, policy, risk, accounting, or receipt controls
- treat model output as execution authority
- allow ATG to choose or determine settlement rails

## Execution corridor

```text
Human or Agent Intent
        -> HLF / input interpretation layer
        -> Atranic semantic expression
        -> ATG mandate and capability request
        -> ATRALITH or conforming implementation
        -> capability resolution
        -> policy / risk / 54-T verification
        -> hardware discovery + eligible model/runtime profiles
        -> Quantization Torque attention, cognition, and compute budgeting
        -> Execution Envelope
        -> execution target + placement selection
        -> Utility Grid execution
        -> Dense Feedback telemetry + BE verification evidence
        -> receipt
        -> Audit
        -> economic accounting / settlement infrastructure where applicable
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
- `accounting` - utility metering metadata and optional references to external economic settlement infrastructure
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
- `compute.runtime.exllamav3`

However, callers SHOULD prefer implementation-neutral capabilities unless they require a specific backend for reproducibility, compatibility, benchmarking, or policy reasons.

## Execution target object

Example:

```yaml
execution:
  target: auto
  runtime_version: null
  accelerator_framework: auto
  target_class: local-preferred
  portability: preferred
  fallback_allowed: true
  placement:
    strategy: auto
    gpu: auto
    cpu_ram: auto
    nvme: auto
  quantization:
    profile: auto
    kv_cache_precision: auto
    mtp_or_speculation: auto
  context:
    required_min_tokens: 32768
    preferred_tokens: 262144
```

The `target` field identifies a registered execution backend or automatic resolution request. It does not modify ATG semantics.

## Runtime and placement selection

A conforming implementation SHOULD select the smallest verified execution surface that satisfies the mandate.

Selection MAY consider:

1. capability compatibility
2. required precision and determinism
3. latency and throughput objectives
4. local versus remote availability
5. CPU, GPU, VRAM, host RAM, storage bandwidth, battery, power, and thermal budgets
6. trusted-computing and credential boundaries
7. provider and licensing constraints
8. Utility Grid price and economic policy
9. Quantization Torque context and cognition budget
10. reproducibility requirements
11. task-specific quality floors and BE evidence
12. Dense Feedback from prior or current execution

Runtime selection MUST NOT expand authority beyond the originating mandate.

### Heterogeneous execution

For eligible runtimes, an execution plan MAY split a model across hardware classes such as GPU, CPU RAM, and NVMe when the runtime has a verified implementation for that placement.

Example:

```yaml
placement:
  strategy: heterogeneous
  gpu_resident:
    - attention
    - hot_experts
    - kv_cache
    - mtp
    - vision
  cpu_resident:
    - routed_expert_tail
  nvme_streamed:
    - ngram_table
```

This is an execution detail beneath Quantization Torque, 54-T, AEGIS, and the Execution Envelope. A repository or vendor benchmark does not by itself authorize production use on a different hardware profile.

## Dense Feedback

A conforming implementation SHOULD capture attributable execution evidence where measurable:

- prefill throughput
- decode throughput
- time to first token
- context depth
- MTP/speculative acceptance
- KV-cache precision and footprint
- VRAM / host RAM usage
- CPU worker count and saturation
- expert placement / offload depth for MoE systems
- storage streaming behavior when storage participates in execution
- power / temperature / throttling
- concurrency
- retry / OOM / fallback events
- task-specific BE quality evidence

Quantization Torque MAY use Dense Feedback to revise the execution plan inside the same preserved invariants. It MUST NOT silently trade away required context, capability, privacy, locality, quality, provenance, safety, or approval requirements.

## Evidence profile example: Qwen3.8-Flash-Next EXL3

A current candidate evidence profile in the Utility Grid records the upstream r0b0tlab configuration for Qwen3.8-Flash-Next EXL3 2.50 bpw. The upstream validated host used an RTX 3090 with 24 GB VRAM and 59 GB host RAM, with MoE expert CPU offload and NVMe streaming for the n-gram table.

Reported upstream evidence includes:

- 38.6 tok/s decode with MTP enabled in the short-context sweep
- 27.8 tok/s without MTP in the same configuration
- MTP acceptance 4.06 on GSM8K greedy and 1.84 at 175k depth
- 664 tok/s prefill and 20.9 tok/s decode at 175k depth
- native 262,144-token context
- 20.7 GB observed peak VRAM during long-context requests
- 61 GiB published artifact size

These measurements are evidence for that profile and host class, not universal claims. A materially different host, including a smaller host-RAM system, requires its own placement plan and benchmark receipt.

## Mojo and MAX

Mojo and MAX are execution targets, not ATG language extensions.

A conforming implementation MAY use Mojo for compiled CPU/GPU workloads and MAY use MAX accelerator libraries or inference infrastructure when the registered target and device capabilities satisfy the request.

The runtime boundary SHOULD preserve this separation:

```text
ATG / Atranic = meaning, mandate, authority, evidence requirements
ATRALITH = implementation, validation, translation, routing
Mojo / MAX / ExLlamaV3 / other runtimes = execution
Utility Grid = delivery, metering, execution evidence
54-T / AEGIS = verified capability and risk boundaries
PAYRAIL or equivalent economic layer = settlement routing
```

## Fallback behavior

If a preferred runtime is unavailable, an implementation MAY select another compatible runtime only when:

- `fallback_allowed` is true
- the fallback satisfies the same capability and authority constraints
- required determinism and compatibility guarantees remain satisfied
- task-specific quality floors remain satisfied
- the receipt records both the requested target and actual target

A fallback MUST NOT silently reduce a security, privacy, provenance, quality, context, or approval guarantee.

## Utility Grid metering

When execution consumes AGENTROPOLIS Utility Grid resources, accounting SHOULD record at least:

- agent or principal identifier
- district or application identifier when applicable
- execution target
- runtime version or commit
- device class
- CPU time
- accelerator time
- peak VRAM and host RAM where available
- storage participation where applicable
- compile time where applicable
- execution time
- provider cost where applicable
- internal Utility Grid charge
- receipt identifier
- optional external settlement reference if the economic layer settles the charge

## Receipt requirements

A compute execution receipt SHOULD record:

- stable request and mandate identifiers
- requested capability
- requested execution target
- actual execution target
- runtime and accelerator versions or commits
- device class and provider class
- hardware profile
- model artifact / source digest
- quantization profile
- placement plan
- context and cache settings
- policy decision and capability-handle references
- timing and resource measurements
- Dense Feedback reference
- verification state and BE evidence reference
- result digest or artifact pointer
- accounting state
- fallback or downgrade events

## Security requirements

Implementations MUST NOT place raw production secrets in ATG messages, model context, runtime logs, or receipts.

Execution targets receive scoped capability handles or sealed credentials rather than raw secrets.

Runtime-generated output is untrusted until verification completes.

External model files, checkpoints, plugins, kernels, containers, and runtime extensions are untrusted ingress until the relevant membrane and quarantine rules are satisfied.

Remote execution SHOULD be treated as external infrastructure and MUST pass the same authority, egress, provenance, and receipt requirements as local execution.

## Compatibility

The profile is intentionally runtime-neutral. New execution targets can be added without revising ATG core semantics as long as they conform to this profile and the execution-target registry.

The registry is descriptive and versioned. It is not an allow-all list. Local policy determines which targets are permitted for a given principal, district, device, or mandate.
