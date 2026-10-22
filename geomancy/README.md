# GEOMANCY experimental compiler slice

**Status: experimental / non-normative / preview only.** This is not the canonical ATG Semantic IR, not a registered ATG domain profile, not a 3D renderer, and not production-ready.

The initial slice validates a bounded scene payload and compiles parametric boxes into deterministic mesh vertices and triangles. It uses only built-in JavaScript features.

Run from repository root with Node.js 20+:

```sh
node --test geomancy/scene-core.test.mjs
```

Integration boundary: reconcile this illustrative payload with canonical ATG IR, profile registration and Atralith translation before any normative claims. Spatial motion requests must remain within the existing `media.spatial.*` governed capability surface; do not bypass Utility Grid, ASBE/54-T, or budget policies.

Next: add schema-based IR adapter, geometry bounds and complexity budgets, reproducible export manifest, browser preview, CI and independent verification.
