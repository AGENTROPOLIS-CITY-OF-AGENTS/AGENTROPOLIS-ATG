# ATG Pages package integration gate

Source: user-provided `agentropolis-pages.zip` (2026-10-12). This PR records integration findings; the binary/embedded HTML assets are **not** yet imported or published.

## Package inventory
- `index.html`: landing/navigation
- `atg-atralith.html`: 90-second canvas-driven Atralith explainer with embedded PNG glyph assets (672418 bytes)
- `city-tour.html`: city introduction
- `agent-mission.html`: mission lifecycle
- `motion-style-guide.html`: motion design reference
- `creative-assurance.html`: creative assurance
- `benchmark-spec.html`: benchmark explainer

## Verified constraints
- ATG page has one inline script, one inline stylesheet, canvas, no external links, forms, iframes, or fetch calls observed in static inspection.
- It is a cinematic explainer, **not** a functional glyph editor or semantic IR compiler.
- The ATG page contains no detected reduced-motion media query; a pause control and keyboard/accessibility QA must be verified before release.
- Keep ATG canonical documentation and language semantics authoritative. Any glyph definitions or 24-symbol numbering in visual media must be reconciled with canonical specs before asserting them as validated.

## Proposed route map
- Keep `/index.html` as existing ATG spatial landing until replacement is approved.
- Stage the uploaded explainer as `/experiences/atg-atralith.html` after asset review.
- Stage the other pages under `/experiences/`, with explicit navigation and no duplicate root index.
- Apply NEUROBUILDS palette: obsidian #05070A, cyan #19E6E6, red #FF2A2A.
- Preserve presentation != authentication != authority. No live-runtime or governance claims.

## Release gates
1. Import original HTML/assets from the supplied ZIP without changing canonical specs.
2. Check source and embedded media license/provenance, file size, CSP, and external dependencies.
3. Verify keyboard playback controls, screen reader alternatives, mobile layout, reduced motion, and no horizontal overflow.
4. Test GitHub Pages subpath routing and relative assets on a preview.
5. Review visual parity with AGENTROPOLIS/NEUROBUILDS.
6. Run CI, approve PR, then publish and verify actual Pages URL.

This document alone does not authorize or prove publication.
