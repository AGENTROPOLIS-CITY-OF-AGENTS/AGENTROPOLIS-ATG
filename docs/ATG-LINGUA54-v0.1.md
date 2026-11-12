# ATG-LINGUA54 v0.1 — proposed multilingual semantic profile

Status: DRAFT. Preserve existing ATG envelopes and ATG-CODE behavior; map this profile to the actual schema after repository review.

## Required semantic fields
profile_version, message_id, sender_agent, recipient_agent, source_language, target_language, original_payload, intent, typed_entities, quantities_and_units, negation, modality, uncertainty, source_evidence, capability_claims, review_required, acknowledgement_required.

## Constraints
- Preserve original message bytes or authenticated reference.
- Model training language is not proof of competence: capability must be measured.
- Semantic intermediate representation is optional and cannot erase cultural context.
- Unknown language, ambiguity, unsafe confidence or incompatible schema => explicit fallback or human review.
- Translation never grants tool permissions, execution authority or access to private archives.
- ATRALITH spoken layer and ATG protocol layer remain separate and interoperable.
- Offline dictionary, glossary, speech and sign-language resources must be independently recoverable.

## Acceptance
Cross-language numerical integrity; negation and conditional fidelity; unsupported-language rejection; offline operation; source/provenance retention; no privilege escalation through translation.

See CIVILIZATION54 Genesis Nucleus proposal in CHAOS ARK for shared architecture.
