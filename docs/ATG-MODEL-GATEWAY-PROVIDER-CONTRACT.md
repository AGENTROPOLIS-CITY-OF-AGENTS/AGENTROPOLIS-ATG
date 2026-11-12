# ATG Model Gateway Provider Contract

**Status:** Proposed contract
**Owner:** AGENTROPOLIS-ATG
**Purpose:** Provider-neutral routing and execution contract for model/compute suppliers
**Initial profile:** Together AI

## Rule

ATG authorizes work. Providers execute bounded requests. Provider or model selection can never expand the capability, data access, autonomy, tool scope, or spend authorized by the Execution Envelope.

This contract prevents districts, applications, runtimes, and agents from hard-coding provider authority.

## Corridor

`Identity -> Mandate -> Plan -> ATG -> Execution Envelope -> Model Gateway -> Provider Adapter -> Result -> Receipt -> Audit`

Provider choice occurs after mandate and envelope compilation.

## ModelRouteRequest

```json
{
  "request_id": "req_...",
  "mandate_ref": "mandate_...",
  "execution_envelope_ref": "env_...",
  "capability": "reason",
  "task_profile": "software_engineering",
  "data_classification": "D1",
  "privacy": {
    "external_egress_allowed": true,
    "dedicated_required": false,
    "jurisdictions_allowed": ["US"]
  },
  "quality": {
    "minimum_eval_profile": "atg-coding-v1",
    "structured_output_required": true,
    "tool_calling_required": true
  },
  "limits": {
    "max_total_cost_usd": 0.50,
    "max_latency_ms": 30000,
    "max_input_tokens": 100000,
    "max_output_tokens": 12000,
    "retry_budget": 2
  },
  "tool_scope_ref": "tools_...",
  "provider_policy": {
    "allow": ["together-ai", "local"],
    "deny": [],
    "local_fallback_required": false
  },
  "receipt_destination": "audit://..."
}
```

## Capability vocabulary

The gateway routes capabilities, not brands. Initial canonical capability names:

- `generate`
- `reason`
- `embed`
- `rerank`
- `transcribe`
- `synthesize`
- `vision`
- `moderate`
- `code`
- `tool_plan`
- `image_generate`
- `video_generate`
- `sandbox_code_execute`
- `fine_tune`
- `batch_inference`

A provider adapter may implement a subset.

## RouteDecision

```json
{
  "decision_id": "route_...",
  "request_id": "req_...",
  "outcome": "EXECUTE",
  "provider": "together-ai",
  "model": "provider-model-id",
  "service_mode": "serverless",
  "reason_codes": [
    "CAPABILITY_MATCH",
    "EVAL_PASS",
    "BUDGET_PASS",
    "PRIVACY_PASS",
    "LATENCY_PASS"
  ],
  "fallback_chain": [
    {"provider": "local", "model": "approved-local-id"}
  ],
  "policy_refs": ["aegis://provider-egress/v1"]
}
```

Allowed outcomes:

- `EXECUTE`
- `DEFER`
- `REJECT`

No provider adapter can change a `REJECT` or `DEFER` to `EXECUTE`.

## Together AI adapter profile

Provider ID: `together-ai`

Potential service modes, when enabled and verified:

- `serverless`
- `dedicated`
- `batch`
- `queue`
- `fine_tune`
- `cluster`
- `sandbox_code`

The adapter MUST discover or consume approved catalog metadata rather than assume that every Together-hosted model supports every capability.

### Endpoint abstraction

Applications MUST call the AGENTROPOLIS Model Gateway, not Together URLs directly.

Adapter implementations may internally translate the provider-neutral contract to Together's API/SDK, including OpenAI-compatible chat/tool schemas where supported.

### Secret handling

`TOGETHER_API_KEY` or successor credentials MUST be injected at runtime from an approved secret store. They MUST NOT appear in:

- repository files;
- prompts;
- memory records;
- training data;
- receipts;
- BUZZ messages;
- client-side application bundles.

## Routing order

ATG evaluates in this order:

1. mandate validity;
2. Execution Envelope validity;
3. autonomy and tool scope;
4. data classification and egress eligibility;
5. jurisdiction policy;
6. model/provider allowlist;
7. minimum evaluation profile;
8. task capability match;
9. privacy/isolation requirement;
10. latency SLO;
11. completed-task economics;
12. availability and circuit-breaker state;
13. fallback readiness.

Price MUST NOT precede authority, privacy, or evaluation.

## Tool-call separation

Model-generated tool calls are proposals until the ATG/AEGIS tool gate authorizes execution.

`model suggests tool -> validate schema -> validate envelope -> validate tool permission -> execute tool -> receipt`

A Together model's tool-calling capability does not grant the provider direct tool access.

## Structured outputs

Where the provider/model supports structured outputs, the adapter SHOULD bind the output to an AGENTROPOLIS schema. Schema conformance does not replace semantic validation.

## Batch and queue semantics

Non-interactive jobs MUST preserve:

- original mandate and envelope references;
- idempotency key;
- dataset/artifact hash when applicable;
- cancellation authority;
- deadline/TTL;
- checkpoint or restart semantics;
- final receipt.

Asynchronous provider status is execution state, not governance state.

## Fine-tune semantics

`fine_tune` is a privileged capability. It requires dataset provenance, rights review, privacy classification, model/license compatibility, budget authorization, evaluation plan, artifact custody plan, and deployment approval.

Training completion never implies deployment approval.

## Execution receipt

```json
{
  "receipt_id": "receipt_...",
  "request_id": "req_...",
  "decision_id": "route_...",
  "execution_envelope_ref": "env_...",
  "provider": "together-ai",
  "model": "provider-model-id",
  "service_mode": "serverless",
  "capability": "reason",
  "data_classification": "D1",
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "provider_cost_usd": 0.0,
    "computed_total_cost_usd": 0.0,
    "latency_ms": 0,
    "retries": 0
  },
  "tool_events": [],
  "fallback_events": [],
  "policy_refs": [],
  "result_hash": "sha256:...",
  "status": "SUCCEEDED",
  "timestamp": "RFC3339"
}
```

## Failure behavior

The adapter MUST fail closed when:

- envelope reference is missing or invalid;
- provider/model is denied;
- data egress is denied;
- secret retrieval fails;
- requested capability is not verified;
- cost ceiling cannot be enforced;
- required receipt fields cannot be produced;
- provider circuit breaker is open.

## Non-goals

This contract does not make ATG a model host, a billing reseller, or a replacement for provider SDKs. It defines the authority boundary above them.