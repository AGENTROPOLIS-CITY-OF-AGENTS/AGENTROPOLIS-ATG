# ATRALITH RFC-0003 Economic Runtime

This slice turns the ATG Economic Authority + Settlement profile into deterministic reference code without pretending that live custody or settlement exists.

## Pipeline

```text
ATG parent mandate
  -> economic mandate compiler
  -> 54-T fail-closed policy decision
  -> bounded capability handle
  -> settlement adapter
  -> simulation result / future verified live result
  -> ATG receipt pipeline
```

## Modules

- `economic.py` compiles a bounded economic mandate and refuses authority widening.
- `economic_runtime.py` provides the reference 54-T policy hook, capability issuance, settlement adapter protocol, and simulation adapter.
- `smoke_test_economic.py` checks allowed execution, over-limit denial, and parent-scope widening denial.

## Security properties

1. User intent is not transaction authority.
2. Child economic authority may narrow, but never widen, the parent ATG mandate.
3. Raw cards, wallet keys, API secrets, and treasury credentials never enter the mandate or capability handle.
4. Missing approval evidence fails closed when approval is required.
5. Merchant, domain, destination, asset, amount, and network scopes are checked deterministically.
6. Live adapters are blocked unless the caller explicitly enables live execution.
7. The built-in settlement adapter is simulation-only and cannot move funds.
8. A simulation result must remain labeled `simulated`; it is not proof of settlement.

## Run the smoke test

From the repository root:

```bash
python3 atralith/smoke_test_economic.py
```

## Production boundary

This is not a custody system, wallet, payment processor, x402 client, XRPL signer, or card network integration. Production adapters must be implemented separately, reviewed by 54-T, use sealed credentials/capability handles, and generate independently verifiable ATG receipts before they may be marked live.
