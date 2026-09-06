"""Localization as execution context.

Localizing an envelope may change the units, currency, formats, applicable
regulations, data residency, tax regime and available services that downstream
execution must assume -- not merely the strings that get rendered.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .context import ContextVector, resolve_context
from .envelope import Assumption, Constraint, SemanticEnvelope, Transformation, Unknown, new_id
from .packs import PackRegistry
from .translate import translate_human


@dataclass
class LocalizationResult:
    envelope: SemanticEnvelope
    rendered: str = ""
    execution_assumptions: Dict[str, Any] = field(default_factory=dict)
    changed_execution_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope": self.envelope.to_dict(),
            "rendered": self.rendered,
            "execution_assumptions": self.execution_assumptions,
            "changed_execution_fields": self.changed_execution_fields,
        }


EXECUTION_FIELDS = (
    "units",
    "currency",
    "date_format",
    "number_format",
    "address_format",
    "data_residency",
    "tax_regime",
    "tax_authorities",
    "regulations",
    "standards",
    "restricted_services",
)


def localize(
    envelope: SemanticEnvelope,
    target_context: ContextVector,
    registry: Optional[PackRegistry] = None,
) -> LocalizationResult:
    registry = registry or PackRegistry.load_default()
    source_context = envelope.source.context if envelope.source else ContextVector()
    source_profile = resolve_context(source_context).execution_profile
    resolution = resolve_context(target_context)
    target_profile = resolution.execution_profile

    out = translate_human(envelope, resolution.context, registry=registry)
    out = copy.deepcopy(out)

    changed = [
        field_name
        for field_name in EXECUTION_FIELDS
        if source_profile.get(field_name) != target_profile.get(field_name)
    ]

    for regulation in target_profile.get("regulations", []):
        expression = f"region_regulation_applies:{regulation}"
        if expression not in {c.expression for c in out.constraints}:
            out.constraints.append(
                Constraint(
                    id=new_id("con"),
                    kind="regulatory",
                    expression=expression,
                    severity="must",
                    origin=f"region:{resolution.context.region}",
                )
            )
    if target_profile.get("data_residency") and target_profile.get("data_residency") != "unspecified":
        out.constraints.append(
            Constraint(
                id=new_id("con"),
                kind="data_residency",
                expression=f"data_residency={target_profile['data_residency']}",
                severity="must",
                origin=f"region:{resolution.context.region}",
            )
        )
    for service in target_profile.get("restricted_services", []):
        out.constraints.append(
            Constraint(
                id=new_id("con"),
                kind="service_availability",
                expression=f"restricted_service:{service}",
                severity="must",
                origin=f"region:{resolution.context.region}",
            )
        )
    for assumption in resolution.assumptions:
        out.add_assumption(Assumption(**assumption))
    for unknown in resolution.unknowns:
        out.add_unknown(Unknown(**unknown))

    out.add_transformation(
        Transformation(
            id=new_id("tx"),
            tool="atg.localize",
            source=f"region:{source_context.region}",
            target=f"region:{resolution.context.region}",
            rule_ids=[f"atg.localize.{field_name}" for field_name in changed],
            pack_versions=registry.versions(),
            lossy=False,
            notes=[
                f"{field_name}: {source_profile.get(field_name)} -> {target_profile.get(field_name)}"
                for field_name in changed
            ],
            confidence=out.confidence,
        )
    )
    return LocalizationResult(
        envelope=out,
        rendered=out.rendered or "",
        execution_assumptions=target_profile,
        changed_execution_fields=changed,
    )
