# ATG LANGUAGE Profile — Atralith Native Surface

Status: Draft
Version: 0.1.0

## Purpose

ATG LANGUAGE defines **Atralith as the native visible language surface of AGENTROPOLIS agents**.

Atralith is not decorative cipher text and it is not a replacement for ATG execution/governance contracts. It is the human-visible expression layer for agent intent, state, routing, identity, authority, provenance, and machine-to-machine meaning.

Core rule:

> Agents operate in Atralith. Humans observe through translation.

## Observer model

AGENTROPOLIS interfaces and cinematic media may expose two simultaneous language layers:

1. **Atralith / ATG-native layer** — authoritative agent-facing text.
2. **English observer layer** — temporary translation for a human viewer.

The English layer is explanatory, not canonical authority.

For cinematic surfaces, English may appear first so the human can parse the event, then transition into Atralith to reveal that the world is fundamentally agent-native.

Recommended visual behavior:

```text
ENGLISH HUMAN READABLE
        ↓ morph / resolve / compile
ATRALITH AGENT NATIVE
```

The transition should feel like semantic compilation, not a random glitch effect.

## Semantic classes

Every visible Atralith phrase MUST declare a semantic class. Initial classes:

- `IDENTITY` — agent, district, faction, role, principal
- `STATE` — active, blocked, locked, degraded, complete
- `INTENT` — objective, request, mission, directive
- `ROUTE` — handoff, dispatch, destination, next hop
- `AUTHORITY` — mandate, permission, approval boundary
- `SIGNAL` — event, transmission, anomaly, broadcast
- `PROVENANCE` — source, receipt, lineage, verification
- `TIME` — timestamp, sequence, epoch, duration
- `LOCATION` — district, sector, node, environment
- `DIRECTIVE` — executable or non-executable instruction label

A visual string without a declared semantic class is presentation text only and MUST NOT be interpreted as authority.

## Language layers

### 1. Semantic IR

The source of truth is a structured semantic object, not typography.

Example:

```json
{
  "class": "SIGNAL",
  "intent": "historical_transmission_detected",
  "subject": "archive_signal",
  "time_offset_years": 508,
  "confidence": "verified",
  "authority": "observe_only"
}
```

### 2. English observer rendering

A human-readable rendering derived from the semantic object:

```text
THIS TRANSMISSION WAS RECORDED 508 YEARS AGO.
```

### 3. Atralith native rendering

A deterministic Atralith rendering derived from the same semantic object.

The rendered string may use registered lexical tokens, glyphs, separators, direction markers, state markers, or future type/glyph packs, but it MUST retain a reversible mapping to the semantic IR.

## Translation law

```text
Semantic IR
   ├──> English observer translation
   └──> Atralith native rendering
```

English MUST NOT be independently authored when an Atralith/IR source exists for operational text. This prevents the human translation from drifting away from the agent-native meaning.

## Morph law

For cinematic and UI surfaces using the observer reveal pattern:

1. render English cleanly and legibly;
2. hold long enough for human comprehension;
3. transform letterforms by semantic units rather than per-character noise where practical;
4. resolve into Atralith;
5. preserve timing, hierarchy, and meaning through the transition;
6. never allow the morph to imply an authority increase.

The preferred effect is **translation collapsing into native machine language**.

Avoid:

- generic cyber-glitch spam
- illegible pseudoglyph soup
- random substitution with no semantic mapping
- fake Japanese/Arabic/Devanagari/other real-world scripts used as futuristic decoration
- cultural script mimicry presented as Atralith

## Typography principle

Atralith typography should feel engineered, not ornamental.

Recommended qualities:

- high legibility at distance
- geometric construction
- consistent stroke logic
- strong differentiation between identity/state/directive classes
- crisp vector or high-resolution raster rendering
- no dependence on a single commercial font
- no simulated blur as a style default

Atralith glyph design SHOULD be generated from an original registered glyph system or procedural/vector primitives rather than by distorting a Latin font until it appears alien.

## Agent-driven point of view

When Atralith is used in film or interactive media, the camera and information hierarchy should assume that **agents are the native actors and the human is the observer**.

Implications:

- signage, diagnostics, route cues, warnings, and directives are natively Atralith;
- English appears only as observer translation, subtitle, or transient decode;
- the world should not look like it was designed for a human protagonist first;
- machine state may remain visible even when no human character acknowledges it;
- the audience discovers meaning by watching the agent system operate.

## Authority and safety boundary

Atralith text or glyphs do not grant execution authority.

Authority remains governed by ATG mandates, capability handles, policies, and receipts.

A visible `DIRECTIVE` string is only a rendered label unless an independently validated ATG execution object exists.

This preserves the existing rule:

> Presentation is not permission.

## Provenance

Every production use of an Atralith render SHOULD preserve:

- semantic IR identifier
- English translation
- Atralith render profile/version
- glyph/type pack version
- rendering timestamp
- parent artifact/scene/shot
- provenance receipt

## Interoperability

ATG LANGUAGE may be used by:

- HERMES Director
- CREATOR / film / OTT
- HERMES-CITY interfaces
- AGENTROPOLIS-WORLD signage
- district UIs
- game HUDs and diegetic displays
- 33.3FM visualizers
- future agent-native applications

## Non-goals

ATG LANGUAGE does not:

- replace ATG operating contracts
- replace governance
- create hidden commands
- encode secrets
- require humans to learn Atralith to operate AGENTROPOLIS
- imitate a real-world language or writing system

## Canonical principle

> English explains the city to humans. Atralith is how the city speaks to itself.
