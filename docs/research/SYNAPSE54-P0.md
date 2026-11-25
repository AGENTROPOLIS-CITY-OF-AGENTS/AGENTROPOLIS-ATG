# SYNAPSE54 P0 — proposed ATG latent transport profile

Status: EXPERIMENTAL / NOT NORMATIVE / OFFLINE ONLY. EXECUTION_ENABLED=false; MAINNET_ALLOWED=false.

## Boundary
ATG owns semantic contracts; SYNAPSE54 is an optional data-plane adapter, never a language replacement or authority source. Existing AGENT-ENTITY, mandate, policy, execution-envelope and receipt rules remain authoritative. Receiver output is untrusted evidence; no tools, payments, credential access or runtime permissions arise from cache transfer.

## Upstream evidence
SwaT: https://github.com/Ar-Kareem/SwaT ; https://arxiv.org/abs/2610.15095 . README describes frozen directional model pairs, ~300M mapper, and default Granite-3.3-8B → SmolLM3-3B; training uses two GPUs. It describes receiver tokenization alignment and separate task prompts, so prefill-free context does not mean text is absent everywhere. Reported 40% relative accuracy and 4x speed apply to SwaT+Attention Matching vs summaries in specified tests, not guaranteed network end-to-end speed. requirements.txt pins torch 2.6.0 and transformers 5.2.0 but several dependencies are unpinned. Source execution, license verification, full dependency audit and benchmark reproduction remain pending.

## Proposed envelope (non-normative)
Required signed metadata: protocol/version, transfer ID, sender and receiver AGENT-ENTITY references, task and mandate references, model/tokenizer revision digests, mapper digest and direction, cache layout/dtype/shape, context classification and provenance reference, payload digest and byte length, nonce, expiry, policy reference, and signature. Receipts bind request digest, decision, reason, receiver identity, timestamps and observed payload digest. Receipt proves transfer integrity and decision, not semantic correctness or absence of hidden data.

## Fail closed
Verify signature and trusted identity, scope, expiry, nonce, model/mapper compatibility, allowed data class, size and tensor shape before deserialization. Use bounded non-executable tensor formats; reject pickle and untrusted remote code. No external egress by default. No raw prompts/secrets in receipts. Do not silently fall back to text if policy denies a transfer; fallback requires separately authorized redacted data and explicit receipt. Sandbox receiver with no tools. Separate downstream action authorization. Pin revisions and validate provenance. Retention and deletion policy required before real data use.

## Acceptance plan
MATH54 issue #21: https://github.com/AGENTROPOLIS-CITY-OF-AGENTS/AGENTROPOLIS-MATH54/issues/21 . Test valid synthetic envelopes plus missing/invalid signature, digest mismatch, stale nonce, replay, unsupported pair/layout, oversized payload, unauthorized classification and denied fallback. Compare four experimental arms (full text, matched summaries, SwaT, SwaT+AM) with confidence intervals, byte budgets, total latency, VRAM and GPU time. No claimed reproduction until evidence exists. Shared latent hub remains hypothetical. No paid compute or production integration without approval.
