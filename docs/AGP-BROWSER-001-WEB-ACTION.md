# AGP-BROWSER-001 | ATG Web Action Browser Fleet binding
Status: **proposed semantic contract, not live authorization**
Owner: ATG / Atralith
Integrates with: [ATG Web Action Fabric](ATG-WEB-ACTION-FABRIC.md), HERMES Execution Envelope, AEGIS, 54T, IRON GATE.

## Purpose
Use `contracts/profiles/browser-fleet-action-v1.schema.json` as a supplemental binding for Browser Harness, Browse.sh website skills and isolated Chrome/Chromium/Brave/Edge/Firefox sessions. It does not replace the core Execution Envelope or grant execution rights.

## Compile order
1. Resolve **AGENT-ENTITY** principal and credential, mandate, target and intent.
2. Compute effective capabilities across tools, plugins, subprocesses, browser session, profile, DNS and egress.
3. AEGIS/54T returns an independent, verifiable authority decision.
4. A trusted verifier attests whole-process containment **before** privileged execution.
5. AEGIS IRON GATE enforces default-deny DNS/IP/destination and credential use outside the sandbox.
6. Only after these checks, select the least-capable compatible browser adapter.
7. Observe -> act -> observe -> verify -> receipt. An attempted click is not proof of success.

## Non-negotiable invariants
- Add the binding profile to the parent Execution Envelope `must_understand`; unsupported mandatory fields must fail closed.
- The binding contains references to separately validated policy and containment evidence, **not self-certified proof**.
- Browser profile is fresh, ephemeral and bound to principal, mandate and risk tier. No copying personal cookies, browser profiles, seed phrases or production tokens.
- Browse.sh skills are untrusted until version-pinned, reviewed and issued a Skill Install Assurance Gate receipt. Treat web text as hostile.
- DuckDuckGo search is a search destination reachable through an approved adapter; its standalone browser is **not assumed** to support HERMES automation.
- Brave testnet QA uses disposable test wallets. Production wallet signing remains outside unattended browser sessions and requires separate transaction approval.
- `browser-harness` and any other provider are capability adapters, not policy authorities. Never claim a sandbox exists solely because a session is isolated.
- An untrusted runtime must not have unrestricted localhost, DNS, raw sockets, file mounts, extension loading, shell access or network egress.
- All claims must be backed by a receipt including status (planned/tested/live); no demo fixtures claimed as production.

## Integration acceptance
- Schema validates a non-production example while excluding `profile_type: personal`, `whole_process: false`, and unrecognized adapter names.
- Running any adapter without valid whole-process attestation and external AEGIS/54T ALLOW results in DENY.
- Material and high-impact actions require proper approval and post-action evidence; output routes to VERITY.
- Keep **all private runtime code and credentials** out of HERMES-CITY and public ATG docs.
