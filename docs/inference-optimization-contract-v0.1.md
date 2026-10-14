# Inference Optimization Contract v0.1 (proposal)

Status: DRAFT / NOT DEPLOYED. Owner: Construction District + Hermes. ATG expresses intent, not authorization.

## Purpose
Reduce total task cost without compromising evidence, security, accessibility, or reliability. Do not equate cheapest tokens with cheapest successful task.

## Canonical flow
Intake -> task decomposition -> per-task RFP/CBA -> deterministic eligibility -> classify/extract/summarize where appropriate -> model selection -> policy and permission checks -> bounded execution -> validation -> receipt -> audit.

## Router rules
1. First test deterministic parsing/rules. Never call a model when a reliable deterministic path suffices.
2. Compare local and hosted candidates on total expected cost = input + output + inference/compute + retries + verification + network + privacy overhead.
3. Classifiers only recommend routing. Never grant privileges, deploy, trade, approve funds, or override AEGIS or human gates.
4. Prefer local for sensitive content. Hosted APIs require explicit data handling approval, redaction and an allowed provider.
5. Preserve original source spans and decision-critical context. Never replace immutable evidence with a summary.
6. Escalate on schema failure, uncertainty, drift, adversarial input, or high risk. Fail closed if no authorized route.
7. Use provider pricing as time-stamped configuration, not a hardcoded constant. Promotional rates require revalidation.

## Contract: request
```json
{"task_id":"uuid","intent":"classify|extract|summarize|reason|execute","risk_tier":"low|medium|high|critical","data_class":"public|internal|restricted","estimated_input_tokens":0,"estimated_output_tokens":0,"quality_floor":0.95,"latency_budget_ms":3000,"allowed_providers":["local"],"execution_authority":false}
```

## Contract: routing receipt
```json
{"task_id":"uuid","route":"deterministic|local|hosted|escalate|deny","model_id":null,"pricing_snapshot_at":null,"estimated_total_usd":0,"actual_total_usd":null,"confidence":null,"schema_valid":null,"source_spans":[],"reason_codes":[],"human_approval_id":null,"policy_decision_id":null,"receipt_id":"uuid"}
```

## Benchmark and acceptance gates
- Build a representative, versioned dataset for each of classification, extraction, summarization and high-risk routing.
- Compare against existing baseline on accuracy, calibration, source-span fidelity, schema validity, p50/p95 latency, dollars per validated task, and failure/retry rate.
- Record false-negative risk routing separately. No high-risk authorization by model output.
- Roll out in shadow mode first; require independent review and regression checks before traffic shifts.
- Expose cost estimates and route explanations in accessible UI; no claims of savings until measured.

## Integration responsibilities
- Hermes: pilot router and instrumentation, not a claim that AGENTROPOLIS is live.
- Construction District: reusable starter template and CI contract tests for new apps.
- ATG: typed intent, risk and receipt semantics; never convert classification into authority.
- AEGIS / VERITY: planned policy validation and evidence review; verify live availability before integration.
- Public sites: documentation/explainer only until benchmark and privacy gates pass; no client-side provider keys.

## Rollback
Feature flag OFF by default. On anomaly disable hosted specialist routing, retain baseline path and preserve receipts. No automated merge or production rollout from this document.
