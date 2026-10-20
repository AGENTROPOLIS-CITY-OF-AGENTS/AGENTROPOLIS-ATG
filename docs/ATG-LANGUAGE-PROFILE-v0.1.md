# ATG:LANGUAGE — Global Language Intelligence Semantic Profile v0.1

**Status:** proposed profile, not registered in the production Atralith interpreter. **Canonical language owner:** AGENTROPOLIS-ATG. **Consumer:** AGENTROPOLIS-GTM. This is a domain profile of ATG, not a replacement for ATG or an English-only prompt convention.

## Purpose
Represent multilingual communication intent and evidence using the canonical ATG Semantic IR model. Language identity, region, script, register, cultural adaptation constraints, emotion/body-language cues where used, source truth and authority must survive routing. Adapters do the translation; they do not redefine ATG semantics.

## Semantic vocabulary
- `ATG:LANGUAGE.SOURCE`: canonical source text and SHA-256 digest.
- `ATG:LANGUAGE.ROUTE`: target BCP-47 locale, audience context, provider/model candidate and rationale. This is a **routing proposal**, not authority to publish.
- `ATG:LANGUAGE.TRANSFORM`: translation/localization/subtitle/dub/graphic variant, lineage to source, declared changes, claims retained.
- `ATG:LANGUAGE.EXPRESSION`: optional emotion and body-language representation mapped to ATG-native constructs; localization cannot erase these or turn them into unsupported factual claims.
- `ATG:LANGUAGE.VERIFY`: back-translation/semantic equivalence evidence, reviewer, failures, uncertainty and accessibility checks.
- `ATG:LANGUAGE.RELEASE`: explicit human approval, publication target, platform permission and execution-envelope reference; absent by default.
- `ATG:LANGUAGE.RECEIPT`: artifact digest, source digest, spec version, reviewer, approvals, execution evidence and observed outcomes.

## Hard boundaries
1. The semantic router MUST NOT grant authority, execute translation provider tools, publish, dub a person's voice, alter a source-of-truth fact, or set any consent field.
2. Source and target meanings MUST distinguish literal translation from cultural adaptation, and preserve named entities, material numbers, dates, disclosures, product status and citation references.
3. Region and language are distinct fields. Do not infer geography from language code or write stereotypes into localized assets.
4. Any localization that introduces a new claim requires a new source claim or explicit rejection.
5. For film, retain captions/text plates as accessible selectable text; subtitles need times; authorized dubbing requires scope-specific voice/performer consent.
6. Every transform carries `source_sha256`, `source_commit`, `locale`, `transform_revision`, `quality_state`. Outputs are immutable once approved; changes require new revision.
7. No fallback from denied publication to another channel. No default publish capability. No unaudited outreach.
8. External providers are pinned and evaluated; no unreviewed training use of non-public user content.
9. ATG may use expressive emoji/body language where suitable and authorized; these represent meaning and state, not privileged instructions.

## Canonical profile shape (JSON-compatible semantic IR projection)
```json
{
  "profile": "ATG:LANGUAGE",
  "profileVersion": "0.1-draft",
  "intent": "LOCALIZE_CONTENT",
  "source": {"locale": "en-US", "contentId": "example", "sha256": "<64 hex>", "commit": "<40 hex>"},
  "target": {"locale": "pt-BR", "region": "BR", "audienceEvidence": null},
  "mode": "cultural_adaptation",
  "constraints": {"preserveClaims": true, "preserveDisclosures": true, "consentRequiredForDub": true},
  "authority": {"publishAllowed": false, "mandateRef": null, "policyRef": null},
  "result": {"artifactSha256": null, "qualityState": "NOT_EVALUATED", "verityReceipt": null}
}
```

The placeholder is illustrative, not a valid signed transaction. The authoritative ATG ABI and expression mapping require dedicated review before adding executable interpreter handling.

## Validation gate
- Schema shape checks; BCP-47 locale validation; full SHA lineage; restricted statuses; no self-granted publication.
- Machine equivalence checks followed by qualified human linguistic review for the pilot.
- VERITY exact-SHA audit and authority/permission review before distribution.

## Five candidate pilot locales
`es-419`, `pt-BR`, `fr-FR`, `ar` (specific locale/dialect must be resolved), `ja-JP`. These are exploration candidates, not market rankings.
