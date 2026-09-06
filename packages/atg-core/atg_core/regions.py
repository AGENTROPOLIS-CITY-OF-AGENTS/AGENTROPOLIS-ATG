"""Region execution profiles.

Region is execution context, not UI decoration: it can change terminology,
units, currency, formats, applicable regulations, data residency and the set of
services an agent may assume exists. Unknown regions are never silently
defaulted -- they surface as unknowns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RegionProfile:
    region: str
    default_locale: str
    default_language: str
    jurisdiction: str
    units: str
    currency: str
    date_format: str
    number_format: str
    address_format: str
    regulations: List[str] = field(default_factory=list)
    standards: List[str] = field(default_factory=list)
    data_residency: str = "unspecified"
    tax_regime: str = "unspecified"
    tax_authorities: List[str] = field(default_factory=list)
    restricted_services: List[str] = field(default_factory=list)


REGION_PROFILES: Dict[str, RegionProfile] = {
    "US": RegionProfile(
        region="US",
        default_locale="en-US",
        default_language="en",
        jurisdiction="US",
        units="us-customary",
        currency="USD",
        date_format="MM/DD/YYYY",
        number_format="1,234.56",
        address_format="street, city, STATE ZIP",
        regulations=["SOX", "CAN-SPAM"],
        standards=["ANSI", "NIST-SP-800-53"],
        data_residency="us",
        tax_regime="federal-state-sales-tax",
        tax_authorities=["IRS"],
    ),
    "US-CA": RegionProfile(
        region="US-CA",
        default_locale="en-US",
        default_language="en",
        jurisdiction="US-CA",
        units="us-customary",
        currency="USD",
        date_format="MM/DD/YYYY",
        number_format="1,234.56",
        address_format="street, city, CA ZIP",
        regulations=["CCPA", "CPRA", "SOX"],
        standards=["ANSI", "NIST-SP-800-53"],
        data_residency="us",
        tax_regime="federal-state-sales-tax",
        tax_authorities=["IRS", "CDTFA", "FTB"],
    ),
    "GB": RegionProfile(
        region="GB",
        default_locale="en-GB",
        default_language="en",
        jurisdiction="GB",
        units="metric",
        currency="GBP",
        date_format="DD/MM/YYYY",
        number_format="1,234.56",
        address_format="street, town, county, POSTCODE",
        regulations=["UK-GDPR", "DPA-2018"],
        standards=["BSI", "ISO-27001"],
        data_residency="uk",
        tax_regime="vat",
        tax_authorities=["HMRC"],
    ),
    "EU": RegionProfile(
        region="EU",
        default_locale="en-IE",
        default_language="en",
        jurisdiction="EU",
        units="metric",
        currency="EUR",
        date_format="DD/MM/YYYY",
        number_format="1.234,56",
        address_format="street, POSTALCODE city, COUNTRY",
        regulations=["GDPR", "eIDAS", "EU-AI-ACT"],
        standards=["CEN", "ISO-27001"],
        data_residency="eu",
        tax_regime="vat",
        tax_authorities=["national-tax-authority"],
        restricted_services=["us-only-data-processing"],
    ),
    "DE": RegionProfile(
        region="DE",
        default_locale="de-DE",
        default_language="de",
        jurisdiction="DE",
        units="metric",
        currency="EUR",
        date_format="DD.MM.YYYY",
        number_format="1.234,56",
        address_format="street number, POSTALCODE city",
        regulations=["GDPR", "BDSG", "EU-AI-ACT"],
        standards=["DIN", "ISO-27001"],
        data_residency="eu",
        tax_regime="vat",
        tax_authorities=["Bundeszentralamt-fuer-Steuern"],
        restricted_services=["us-only-data-processing"],
    ),
    "MX": RegionProfile(
        region="MX",
        default_locale="es-MX",
        default_language="es",
        jurisdiction="MX",
        units="metric",
        currency="MXN",
        date_format="DD/MM/YYYY",
        number_format="1,234.56",
        address_format="calle numero, colonia, CP, ciudad",
        regulations=["LFPDPPP"],
        standards=["NOM"],
        data_residency="mx",
        tax_regime="iva",
        tax_authorities=["SAT"],
    ),
    "AE": RegionProfile(
        region="AE",
        default_locale="ar-AE",
        default_language="ar",
        jurisdiction="AE",
        units="metric",
        currency="AED",
        date_format="DD/MM/YYYY",
        number_format="1,234.56",
        address_format="building, street, area, emirate",
        regulations=["UAE-PDPL"],
        standards=["ESMA"],
        data_residency="ae",
        tax_regime="vat",
        tax_authorities=["UAE-FTA"],
    ),
}

LOCALE_TO_REGION: Dict[str, str] = {
    "en-US": "US",
    "en-GB": "GB",
    "en-IE": "EU",
    "de-DE": "DE",
    "es-MX": "MX",
    "ar-AE": "AE",
}


def get_region_profile(region: Optional[str]) -> Optional[RegionProfile]:
    if not region:
        return None
    return REGION_PROFILES.get(region) or REGION_PROFILES.get(region.upper())


def region_for_locale(locale: Optional[str]) -> Optional[str]:
    if not locale:
        return None
    return LOCALE_TO_REGION.get(locale)


def supported_regions() -> List[str]:
    return sorted(REGION_PROFILES)
