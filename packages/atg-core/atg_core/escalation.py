"""Escalation policy.

High-impact domains never assume a jurisdiction, and lossy or unproven
transforms are always visible. Escalation is a property of the envelope, not a
side channel.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from .context import ContextVector
from .envelope import SemanticEnvelope, Unknown
from .packs import DomainPack

HIGH_IMPACT_PACKS = {"TAX", "LEGAL", "REAL_ESTATE"}
MATERIAL_EQUIVALENCE_THRESHOLD = 0.85


def apply_domain_policy(
    envelope: SemanticEnvelope,
    packs: Iterable[DomainPack],
    context: ContextVector,
) -> SemanticEnvelope:
    """Attach blocking unknowns for missing or unsupported jurisdiction."""
    concepts = {entity.concept for entity in envelope.entities}
    for pack in packs:
        if pack.pack_id not in HIGH_IMPACT_PACKS:
            continue
        pack_concepts = {entry.concept for entry in pack.lexicon}
        if not (concepts & pack_concepts):
            continue
        if not context.jurisdiction:
            envelope.add_unknown(
                Unknown(
                    id=f"escalation.jurisdiction.missing.{pack.pack_id.lower()}",
                    question=(
                        f"{pack.pack_id} content requires an explicit jurisdiction; none was supplied."
                    ),
                    kind="missing_jurisdiction",
                    blocking=True,
                )
            )
            continue
        supported = pack.supported_jurisdictions()
        if context.jurisdiction not in supported and not any(
            context.jurisdiction.startswith(f"{item}-") for item in supported
        ):
            envelope.add_unknown(
                Unknown(
                    id=f"escalation.jurisdiction.unsupported.{pack.pack_id.lower()}",
                    question=(
                        f"Pack {pack.pack_id}@{pack.version} has no rules for jurisdiction "
                        f"'{context.jurisdiction}'; treatment is uncertain."
                    ),
                    kind="unsupported_jurisdiction",
                    blocking=True,
                    candidates=supported,
                )
            )
    return envelope


def escalate_for_equivalence(
    envelope: SemanticEnvelope,
    equivalence: Optional[float],
    drift: Optional[List[str]] = None,
) -> SemanticEnvelope:
    if equivalence is not None and equivalence < MATERIAL_EQUIVALENCE_THRESHOLD:
        envelope.add_unknown(
            Unknown(
                id="escalation.semantic_drift",
                question=(
                    f"Semantic equivalence {equivalence:.2f} is below the material threshold "
                    f"{MATERIAL_EQUIVALENCE_THRESHOLD}: {'; '.join(drift or []) or 'unspecified drift'}"
                ),
                kind="semantic_drift",
                blocking=True,
            )
        )
    return envelope
