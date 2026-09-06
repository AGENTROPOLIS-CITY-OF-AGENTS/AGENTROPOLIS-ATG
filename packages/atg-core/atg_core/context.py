"""Canonical ATG context vector and its resolution rules."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional

from .regions import get_region_profile, region_for_locale, supported_regions
from .serde import from_jsonable, to_jsonable

CONTEXT_FIELDS = (
    "language",
    "locale",
    "region",
    "jurisdiction",
    "industry",
    "profession",
    "role",
    "programming_language",
    "programming_dialect",
    "framework",
    "runtime",
    "platform",
    "architecture",
    "standards",
    "regulations",
    "units",
    "currency",
    "audience",
    "output_medium",
)

HIGH_IMPACT_INDUSTRIES = {"TAX", "LEGAL", "REAL_ESTATE", "HEALTHCARE", "FINANCE"}


@dataclass
class ContextVector:
    language: Optional[str] = None
    locale: Optional[str] = None
    region: Optional[str] = None
    jurisdiction: Optional[str] = None
    industry: Optional[str] = None
    profession: Optional[str] = None
    role: Optional[str] = None
    programming_language: Optional[str] = None
    programming_dialect: Optional[str] = None
    framework: Optional[str] = None
    runtime: Optional[str] = None
    platform: Optional[str] = None
    architecture: Optional[str] = None
    standards: List[str] = field(default_factory=list)
    regulations: List[str] = field(default_factory=list)
    units: Optional[str] = None
    currency: Optional[str] = None
    audience: Optional[str] = None
    output_medium: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return to_jsonable(self)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ContextVector":
        return from_jsonable(cls, data or {}) or cls()

    def merge(self, other: Optional["ContextVector"]) -> "ContextVector":
        """Overlay non-empty values of ``other`` on top of this vector."""
        if other is None:
            return replace(self)
        merged = replace(self)
        for name in CONTEXT_FIELDS:
            value = getattr(other, name)
            if isinstance(value, list):
                if value:
                    combined = list(getattr(merged, name)) + [v for v in value if v not in getattr(merged, name)]
                    setattr(merged, name, combined)
            elif value not in (None, ""):
                setattr(merged, name, value)
        return merged

    @property
    def is_high_impact(self) -> bool:
        return (self.industry or "").upper() in HIGH_IMPACT_INDUSTRIES


@dataclass
class ContextResolution:
    context: ContextVector
    assumptions: List[Dict[str, str]] = field(default_factory=list)
    unknowns: List[Dict[str, Any]] = field(default_factory=list)
    execution_profile: Dict[str, Any] = field(default_factory=dict)

    @property
    def requires_escalation(self) -> bool:
        return any(unknown.get("blocking") for unknown in self.unknowns)


def resolve_context(context: ContextVector) -> ContextResolution:
    """Fill in what the region deterministically implies; flag what it does not.

    Never guesses a jurisdiction for a high-impact industry, and never invents a
    region profile that is not in the registry.
    """
    resolved = replace(context)
    assumptions: List[Dict[str, str]] = []
    unknowns: List[Dict[str, Any]] = []

    if not resolved.region and resolved.locale:
        inferred = region_for_locale(resolved.locale)
        if inferred:
            resolved.region = inferred
            assumptions.append(
                {
                    "id": "ctx.region.from_locale",
                    "statement": f"region={inferred} inferred from locale={resolved.locale}",
                    "basis": "atg_core.regions.LOCALE_TO_REGION",
                    "impact": "low",
                }
            )

    if resolved.locale and not resolved.language:
        resolved.language = resolved.locale.split("-")[0]

    profile = get_region_profile(resolved.region)
    if resolved.region and profile is None:
        unknowns.append(
            {
                "id": "ctx.region.unsupported",
                "question": f"No execution profile is registered for region '{resolved.region}'.",
                "kind": "unsupported_region",
                "blocking": True,
            }
        )

    if profile is not None:
        defaults = {
            "locale": profile.default_locale,
            "language": profile.default_language,
            "units": profile.units,
            "currency": profile.currency,
        }
        for name, value in defaults.items():
            if getattr(resolved, name) in (None, ""):
                setattr(resolved, name, value)
                assumptions.append(
                    {
                        "id": f"ctx.{name}.from_region",
                        "statement": f"{name}={value} derived from region={profile.region}",
                        "basis": f"atg_core.regions.REGION_PROFILES[{profile.region}]",
                        "impact": "medium" if name in ("units", "currency") else "low",
                    }
                )
        for regulation in profile.regulations:
            if regulation not in resolved.regulations:
                resolved.regulations.append(regulation)
        for standard in profile.standards:
            if standard not in resolved.standards:
                resolved.standards.append(standard)
        if not resolved.jurisdiction:
            if context.is_high_impact:
                unknowns.append(
                    {
                        "id": "ctx.jurisdiction.required",
                        "question": (
                            f"Industry '{resolved.industry}' is high impact; jurisdiction must be stated "
                            f"explicitly rather than inferred from region '{profile.region}'."
                        ),
                        "kind": "missing_jurisdiction",
                        "blocking": True,
                    }
                )
            else:
                resolved.jurisdiction = profile.jurisdiction
                assumptions.append(
                    {
                        "id": "ctx.jurisdiction.from_region",
                        "statement": f"jurisdiction={profile.jurisdiction} derived from region={profile.region}",
                        "basis": f"atg_core.regions.REGION_PROFILES[{profile.region}]",
                        "impact": "medium",
                    }
                )

    if not resolved.region and context.is_high_impact:
        unknowns.append(
            {
                "id": "ctx.region.required",
                "question": f"Industry '{resolved.industry}' is high impact; region/jurisdiction must be supplied.",
                "kind": "missing_region",
                "blocking": True,
            }
        )

    execution_profile: Dict[str, Any] = {"supported_regions": supported_regions()}
    if profile is not None:
        execution_profile.update(
            {
                "region": profile.region,
                "date_format": profile.date_format,
                "number_format": profile.number_format,
                "address_format": profile.address_format,
                "units": profile.units,
                "currency": profile.currency,
                "data_residency": profile.data_residency,
                "tax_regime": profile.tax_regime,
                "tax_authorities": list(profile.tax_authorities),
                "regulations": list(profile.regulations),
                "standards": list(profile.standards),
                "restricted_services": list(profile.restricted_services),
            }
        )

    return ContextResolution(
        context=resolved,
        assumptions=assumptions,
        unknowns=unknowns,
        execution_profile=execution_profile,
    )
