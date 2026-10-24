# ATG:COMM v0.1 — Communications domain profile (draft)

Status: PROPOSED / NOT RATIFIED / NOT DEPLOYED.

## Canonical boundaries
ATG/Atralith remains the semantic language. ATG:COMM extends it with transport-independent communication semantics. CODEC54 represents messages. GATEWAY54 interfaces with media; GRIDMESH routes; TELEPHONE54 manages human and store-and-forward relay. AEGIS/54T enforces policy. No encoding, relay, receipt, or presentation confers authority.

## Dialect registry scope
Discover and register every existing ATG profile without silently redefining it. Known profiles include SIGNAL, VERIFY, IP, MARKET, AGENT-LINK, BROADCAST, ARCANA54, LANGUAGE, COMPUTE-EXECUTION, CONNECTOME, CONTINUITY, EVM/ERC20, EVM/NATIVE, SOLANA/NATIVE, VOICE and COMM. Inventory is not a claim that every profile is already implemented or ratified. Unknown dialects must be rejected or explicitly passed through as opaque, never guessed.

## CODEC54 representation registry
- ATG semantic IR + canonical JSON (lossless baseline)
- UTF-8 text (lossless if byte framing is preserved)
- International Morse (lossless only with defined field/line framing and escape rules)
- Atralith canonical glyphs (24 verified semantic glyph assets, not a full alphabet)
- QR/optical/audio/packet (transport/encoding adapters require independent conformance tests)
- Human-readable summaries (lossy, must never be described as lossless)

For Atralith: glyph tokens SYN, AR, GHAR, RHE, ESH, LUN may annotate resource updates. They do not encode full field values. A lossless glyph grammar requires an approved scalar alphabet, numeric/time grammar, escaping, delimiters, ordering, and round-trip tests. No substitute artwork permitted.

## Message envelope
Required: version, type, origin, priority, payload, authority, ttl_minutes. Optional: message_id, created_at, dialect, provenance, signature_reference, receipt_reference, route_intent, expiry_at. Distinguish a duration TTL from an absolute expiry timestamp. The authority value UNVERIFIED must survive all transformations. Cryptographic signature validation must be checked independently of encoding.

## Round-trip invariants
decode(encode(M, dialect, representation)) == M for any adapter advertised as lossless. Canonical serialization must preserve field names, exact string values, numeric values, version, and provenance. A transformation that cannot preserve all fields must mark itself lossy and retain the original envelope separately. Reject unknown glyph tokens and unknown required fields rather than hallucinating mappings.

## MAP54 integration (provisional)
MAP54 is an unresolved system identifier in the inspected repos. Define only a proposed adapter boundary: input = validated ATG:COMM envelope + explicit routing intent + location-disclosure permission; output = map/coverage visualization metadata or a typed unsupported result. No inferred coordinates, passive user tracking, surveillance-derived peer locations, or route authority. Mapping overlays are not relay nodes. Do not claim MAP54 is integrated until its canonical implementation and schema are identified.

## Example
ATG/COMM/1.0
TYPE: RESOURCE_UPDATE
ORIGIN: COMMUNITY_NODE_07
PRIORITY: HIGH
PAYLOAD: WATER AVAILABLE AT STATION 3
AUTHORITY: UNVERIFIED
TTL: 120 MINUTES

## Governance gate
Review ATG profile ownership, glyph grammar, MAP54 canonical definition, CODEC54 adapters, safety/regulatory limits (particularly amateur-radio encryption), and conformance tests before merge. This draft creates no live communications capability.
