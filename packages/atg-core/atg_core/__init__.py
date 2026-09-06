"""ATG core: the canonical semantic layer for Agentropolis.

Public surface used by the MCP server, adapters and tests. Nothing here depends
on a specific vendor, model or transport.
"""

from .context import ContextResolution, ContextVector, resolve_context
from .envelope import (
    Assumption,
    Constraint,
    Contract,
    Endpoint,
    Entity,
    Intent,
    Provenance,
    ProvenanceSource,
    Relation,
    Representation,
    SemanticEnvelope,
    Transformation,
    Unknown,
    contract_signature,
)
from .escalation import MATERIAL_EQUIVALENCE_THRESHOLD, apply_domain_policy
from .evidence import EvidencePacket, build_evidence_packet
from .explain import explain_code_mapping, explain_envelope, explain_mapping
from .localize import LocalizationResult, localize
from .normalize import normalize
from .packs import DomainPack, LexiconEntry, PackError, PackRegistry
from .parse import parse
from .provenance import LEDGER, ProvenanceLedger, provenance_record
from .regions import RegionProfile, get_region_profile, supported_regions
from .roundtrip import RoundtripResult, roundtrip
from .translate import translate_code, translate_domain, translate_human
from .validate import ValidationResult, validate
from .version import ATG_CORE_VERSION, ATG_VERSION

__all__ = [
    "ATG_VERSION",
    "ATG_CORE_VERSION",
    "MATERIAL_EQUIVALENCE_THRESHOLD",
    "Assumption",
    "Constraint",
    "Contract",
    "ContextResolution",
    "ContextVector",
    "DomainPack",
    "Endpoint",
    "Entity",
    "EvidencePacket",
    "Intent",
    "LEDGER",
    "LexiconEntry",
    "LocalizationResult",
    "PackError",
    "PackRegistry",
    "Provenance",
    "ProvenanceLedger",
    "ProvenanceSource",
    "RegionProfile",
    "Relation",
    "Representation",
    "RoundtripResult",
    "SemanticEnvelope",
    "Transformation",
    "Unknown",
    "ValidationResult",
    "apply_domain_policy",
    "build_evidence_packet",
    "contract_signature",
    "explain_code_mapping",
    "explain_envelope",
    "explain_mapping",
    "get_region_profile",
    "localize",
    "normalize",
    "parse",
    "provenance_record",
    "resolve_context",
    "roundtrip",
    "supported_regions",
    "translate_code",
    "translate_domain",
    "translate_human",
    "validate",
]
