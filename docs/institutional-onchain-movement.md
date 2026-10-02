# ATG Institutional Market Regime Contract

## Role
ATG compiles FIN54 MarketEvidence and InstitutionalRegime state into governed agent-readable policy posture.

## Input
- MarketEvidence[]
- FIN54 IOMI snapshot
- institutional regime R0-R6
- confidence
- provenance
- jurisdiction
- asset class
- concentration and acceleration metrics

## Output
A governed posture object describing what an agent MAY do next.

## Example posture transitions
- increase observation frequency
- deepen research
- open simulation
- request independent verification
- narrow or widen a bounded execution envelope
- require human approval
- deny execution
- freeze and escalate

## Prohibited behavior
ATG MUST NOT compile a benchmark increase directly into BUY, SELL, TRANSFER, MINT, BURN, BRIDGE, or other capital-moving authority.

## Policy axiom
Market movement changes agent posture, not automatically the money.

## Receipt requirement
Every consequential posture transition records:
- evidence ids
- benchmark snapshot id
- previous posture
- next posture
- policy rule
- confidence
- authorizer
- timestamp
