# ATG:LOCALIZATION 0.1.0-draft.2

Status: proposed, offline validation only. No interpreter registration, publication adapter or execution capability. ATG owns semantics; GTM owns campaign decisions.

## Identity and pins

SOURCE, ROUTE, TRANSFORM, EXPRESSION, VERIFY, RELEASE evidence and RECEIPT belong to `ATG:LOCALIZATION`. This does not redefine `ATG_LANGUAGE`, `docs/ATG-PROFILE-LANGUAGE.md` or `registries/language-surface.yaml`. Source semantic IR remains authoritative; observer translations and glyphs cannot increase authority. The former localization draft path is a withdrawn-name notice, not a native LANGUAGE alias.

Canonical field names/types: `contracts/localization-v0.1.schema.json`. Consumers must also run the cross-field checker `atralith/localization.py`. Exact version only. Contract and provider pins require repository, full 40-hex commit, path and SHA-256 of bytes. Resolve and hash bytes before use. Tags, labels and branches alone are insufficient. Existing language, voice and execution-envelope dependencies are pinned in `registries/localization-dependencies.json`.

## Source and transform

Source records include repository/commit/digest/locale, semantic IR and exposure approval evidence. Transforms repeat source digest/commit and locale and require integer revision, previous-record reference, immutable output digest, mode, declared changes, rights and claims ledger. Revision 1 has no predecessor; later revisions require its URI/digest. External lineage verification must resolve predecessors, check increasing revisions and unchanged lineage. Approved bytes cannot be overwritten. Any source/output/locale/destination change invalidates prior approvals and requires new evidence.

Preserve numbers, dates, claims, disclosures, citations, product status, entities and registered Atralith constructs. New claims need an approved source revision or rejection. Cultural adaptation declares changes separately from literal translation. Region and audience require separate evidence, never inference from language. Emotion/body-language cues convey meaning, not new facts or hidden instructions. Provider rights review and immutable pins are mandatory; no unreviewed training on non-public content.

## Quality

Quality names producer, immutable model revision, digest-pinned method/calibration rubric, normalized score [0,1], threshold exactly 0.90, independent qualified native reviewer and evidence. VERIFIED requires >=0.90 and zero blocking failures. Unknown, categorical or uncalibrated scores remain REVIEW/BLOCKED; never invent normalization. The rubric must cover semantic equivalence, claims, disclosures, register, cultural risk and accessibility. Scores are filters, not proof. REVIEW/BLOCKED cannot carry release evidence.

The pilot allowlist is es-419, pt-BR, fr-FR, ja-JP, plus en-US for sources. It is deliberately narrower than BCP-47, not a complete parser. Arabic remains blocked until explicit dialect/locale and reviewer selection. Country, audience and visual RTL review need evidence. Subtitles require accessible timed-caption evidence; this checker checks references, not caption timing or media bytes.

## Scoped voice consent

Dubbing requires voice ID, performer ID, `consent_ref`, usage `dub` and an external grant. These map to ATG:VOICE `voice.id`, `voice.consent_ref`, `voice.channel` (destination channel) and `voice.authority_ref` (grant record). Scope binds voice, performer, usage, source/output digests, revision, locale, destination platform/account/channel/region and action. The grant record must match consent_ref. A boolean cannot convey consent. Voice Gateway must authenticate issuer, rights chain, expiry and revocation immediately before synthesis. No denied-voice/provider/channel fallback.

## Release evidence never grants authority

Release defaults to null. A release request binds exact artifact/revision/locale/destination/action to independent human approval, platform permission, execution envelope, AEGIS decision, 54T isolation evidence and VERITY receipt. Signed evidence includes URI/digest, issuer, key ID, signature, expiry and scope. Signatures cover exact referenced record bytes including full scope. Trust anchors, issuer identities and human roles must come from an independent trusted registry, never producer-supplied keys or strings.

Future dispatch must resolve/hash evidence, authenticate human sponsor authority, verify signatures/expiry/revocation/replay protection, validate the canonical execution-envelope schema and mandate/capability/action/destination bindings, recheck live platform permission, AEGIS and 54T, and verify exact-SHA quality/rights/VERITY evidence. Missing, unknown, changed, stale or unreachable evidence means deny. No alternate-channel fallback. Localization routing only proposes intent and cannot set consent, execute provider tools or grant capabilities.

These external services are not implemented here. `authorize_publication` always raises PermissionError, even with complete-looking release records. Schema validity is not authentication or permission. `publishAllowed` and unknown authority fields are rejected.

## Receipts and remaining gates

Offline receipts bind source/output digest, revision, contract commit and destination. Status is review, blocked or simulation; execution evidence and observed outcomes must be null. Receipt URI/digest points to a separate immutable evidence blob, not a recursive hash of the enclosing record. example.invalid fixtures prove no real approval or rights.

Future execution needs a separately reviewed receipt schema with executor, approvals, envelope, timestamp, destination, replay ID, action result and independently observed outcomes. Metrics require raw evidence, cohort and observation window by locale/region/platform. No invented engagement. Contract review, merge, external verification services and separately authorized activation remain outstanding.
