# ATG Market Evidence Profile

## Role

Define how financial-market observations enter Agentropolis governance without being mistaken for authority.

FIN54 and other approved intelligence providers emit normalized `MarketEvidence`. ATG consumes that evidence as context for mandate compilation and risk classification. Evidence is not an execution instruction.

## Required Semantics

A market-evidence object SHOULD include:
- version
- instrument / venue / chain when applicable
- timeframe and observation timestamp
- detector capability ID and version
- direction or neutral classification
- confidence
- supporting evidence
- invalidation conditions
- source provenance / hashes
- staleness / expiry
- experimental flag when applicable
- `trade_authority: none`

## Compilation Rule

```text
MarketEvidence
  -> semantic validation
  -> mandate compatibility check
  -> correlation / provenance checks
  -> economic-exposure assessment
  -> Progressive Governance risk classification
  -> Execution Envelope
```

ATG MUST NOT:
- convert one detector directly into permission to trade;
- allow the executing agent to self-assign its risk tier;
- treat confidence as authority;
- allow experimental evidence to bypass stronger governance;
- allow stale evidence to silently authorize consequential action.

## Capability Families

Recommended capability namespace:

```text
market.fibonacci.detect
market.breakout.detect
market.reversal.detect
market.fvg.detect
market.candlestick.classify
market.heikin_ashi.transform
market.renko.transform
market.harmonics.detect
market.elliott.classify
market.gann.analyze
market.support_resistance.detect
market.dynamic_sr.compute
market.trendline.fit
market.momentum.compute
market.oscillator.compute
market.divergence.detect
market.volume.analyze
market.ma.compute
market.psar.compute
```

## Authority Rule

Signals are evidence. Mandates establish purpose. ATG compiles authority. AEGIS and fiscal controls enforce the boundary. Executors only receive the permissions encoded in the resulting Execution Envelope.
