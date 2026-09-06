"""The canonical ATG semantic envelope.

Every ATG transform consumes and produces this structure. Agents do not
translate to each other directly when semantics matter: they emit an envelope,
and the envelope is the unit of provenance, validation and escalation.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .context import ContextVector
from .serde import from_jsonable, to_jsonable
from .version import ATG_VERSION

REPRESENTATION_KINDS = ("human_text", "code", "schema", "api", "protocol", "document")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Representation:
    kind: str
    name: str
    version: str = ""
    dialect: str = ""

    def label(self) -> str:
        return "/".join(part for part in (self.kind, self.name, self.dialect, self.version) if part)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "version": self.version, "dialect": self.dialect}


@dataclass
class Endpoint:
    representation: Representation
    context: ContextVector = field(default_factory=ContextVector)


@dataclass
class Intent:
    act: str = "state"
    predicate: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Entity:
    id: str
    concept: str
    surface: str = ""
    type: str = "concept"
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class Relation:
    id: str
    type: str
    source: str
    target: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Constraint:
    id: str
    kind: str
    expression: str
    severity: str = "must"
    origin: str = ""


@dataclass
class Contract:
    id: str
    kind: str
    name: str
    signature: Dict[str, Any] = field(default_factory=dict)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    behavior: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Assumption:
    id: str
    statement: str
    basis: str = ""
    impact: str = "low"


@dataclass
class Unknown:
    id: str
    question: str
    kind: str = "ambiguity"
    blocking: bool = False
    candidates: List[str] = field(default_factory=list)


@dataclass
class ProvenanceSource:
    id: str
    kind: str
    reference: str
    version: str = ""
    digest: str = ""


@dataclass
class Transformation:
    id: str
    tool: str
    at: str = field(default_factory=utc_now)
    source: str = ""
    target: str = ""
    rule_ids: List[str] = field(default_factory=list)
    pack_versions: Dict[str, str] = field(default_factory=dict)
    lossy: bool = False
    notes: List[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class Provenance:
    sources: List[ProvenanceSource] = field(default_factory=list)
    transformations: List[Transformation] = field(default_factory=list)


@dataclass
class SemanticEnvelope:
    atg_version: str = ATG_VERSION
    message_id: str = field(default_factory=lambda: new_id("atg"))
    source: Optional[Endpoint] = None
    target: Optional[Endpoint] = None
    intent: Intent = field(default_factory=Intent)
    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    contracts: List[Contract] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    unknowns: List[Unknown] = field(default_factory=list)
    provenance: Provenance = field(default_factory=Provenance)
    confidence: float = 1.0
    semantic_equivalence: Optional[float] = None
    roundtrip_score: Optional[float] = None
    requires_escalation: bool = False
    rendered: Optional[str] = None

    # -- serialisation -------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return to_jsonable(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SemanticEnvelope":
        return from_jsonable(cls, data)

    # -- mutation helpers ----------------------------------------------
    def add_transformation(self, transformation: Transformation) -> Transformation:
        self.provenance.transformations.append(transformation)
        self.confidence = min(self.confidence, transformation.confidence)
        return transformation

    def add_source(self, source: ProvenanceSource) -> ProvenanceSource:
        self.provenance.sources.append(source)
        return source

    def add_unknown(self, unknown: Unknown) -> Unknown:
        self.unknowns.append(unknown)
        if unknown.blocking:
            self.requires_escalation = True
        return unknown

    def add_assumption(self, assumption: Assumption) -> Assumption:
        self.assumptions.append(assumption)
        return assumption

    def pack_versions(self) -> Dict[str, str]:
        versions: Dict[str, str] = {}
        for transformation in self.provenance.transformations:
            versions.update(transformation.pack_versions)
        return versions

    def is_lossy(self) -> bool:
        return any(t.lossy for t in self.provenance.transformations)

    # -- canonical comparison ------------------------------------------
    def canonical_signature(self) -> Dict[str, Any]:
        """Locale/dialect-free view of meaning, used for equivalence checks."""
        return {
            "intent": {"act": self.intent.act, "predicate": self.intent.predicate},
            "concepts": sorted({e.concept for e in self.entities}),
            "relations": sorted({f"{r.type}({r.source}->{r.target})" for r in self.relations}),
            "constraints": sorted({f"{c.kind}:{c.expression}" for c in self.constraints}),
            "contracts": sorted(contract_signature(c) for c in self.contracts),
        }

    def canonical_hash(self) -> str:
        payload = json.dumps(self.canonical_signature(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def core_signature(self) -> Dict[str, Any]:
        """Intent and meaning without region-derived execution constraints.

        Two locales of the same request share this signature; they do not share
        ``canonical_signature``, because region changes what must be enforced.
        """
        signature = self.canonical_signature()
        signature["constraints"] = sorted(
            f"{c.kind}:{c.expression}"
            for c in self.constraints
            if not c.origin.startswith("region:")
        )
        return signature

    def core_hash(self) -> str:
        payload = json.dumps(self.core_signature(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def contract_signature(contract: Contract) -> str:
    params = ",".join(
        f"{p.get('name')}:{p.get('type')}" for p in contract.signature.get("params", [])
    )
    returns = contract.signature.get("returns", "void")
    errors = ",".join(sorted(contract.errors))
    return f"{contract.kind}:{contract.name}({params})->{returns}!{errors}"
