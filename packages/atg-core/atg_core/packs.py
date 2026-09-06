"""Domain pack registry.

Packs are versioned, testable data artefacts. Adding a pack must never require
changing a core MCP tool contract, so everything a pack contributes is data:
lexicon, entities, relationships, industry codes, standards, authorities,
documents, workflows, roles, abbreviations, synonyms, jurisdiction rules,
source mappings and translation rules.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

REQUIRED_SECTIONS = (
    "lexicon",
    "entities",
    "relationships",
    "industry_codes",
    "standards",
    "authorities",
    "documents",
    "workflows",
    "roles",
    "abbreviations",
    "synonyms",
    "jurisdiction_rules",
    "source_mappings",
    "translation_rules",
)

_CORE_PACK_DIR = Path(__file__).resolve().parent / "data" / "packs"
_PACKAGES_DIR = Path(__file__).resolve().parents[2]


class PackError(ValueError):
    """Raised when a pack is structurally invalid."""


@dataclass
class LexiconEntry:
    concept: str
    pack_id: str
    pack_version: str
    type: str = "concept"
    definition: str = ""
    surfaces: Dict[str, List[str]] = field(default_factory=dict)
    abbreviations: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    ambiguous: bool = False
    ambiguity_note: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)

    def surface_for(self, locale: Optional[str], language: Optional[str] = None) -> Optional[str]:
        if locale and self.surfaces.get(locale):
            return self.surfaces[locale][0]
        language = language or (locale.split("-")[0] if locale else None)
        if language:
            for key, values in self.surfaces.items():
                if values and key.split("-")[0] == language:
                    return values[0]
        for values in self.surfaces.values():
            if values:
                return values[0]
        return None

    def all_terms(self) -> Iterable[str]:
        for values in self.surfaces.values():
            for value in values:
                yield value
        for value in list(self.abbreviations) + list(self.synonyms):
            yield value


@dataclass
class DomainPack:
    pack_id: str
    version: str
    title: str
    path: str
    data: Dict[str, Any]

    @property
    def lexicon(self) -> List[LexiconEntry]:
        entries = []
        for raw in self.data.get("lexicon") or []:
            entries.append(
                LexiconEntry(
                    concept=raw["concept"],
                    pack_id=self.pack_id,
                    pack_version=self.version,
                    type=raw.get("type", "concept"),
                    definition=raw.get("definition", ""),
                    surfaces={k: list(v) for k, v in (raw.get("surfaces") or {}).items()},
                    abbreviations=list(raw.get("abbreviations") or []),
                    synonyms=list(raw.get("synonyms") or []),
                    ambiguous=bool(raw.get("ambiguous", False)),
                    ambiguity_note=raw.get("ambiguity_note", ""),
                    attributes=dict(raw.get("attributes") or {}),
                )
            )
        return entries

    def section(self, name: str) -> List[Any]:
        value = self.data.get(name)
        if isinstance(value, dict):
            return [{"key": k, "value": v} for k, v in value.items()]
        return list(value or [])

    def jurisdiction_rules(self, jurisdiction: Optional[str]) -> List[Dict[str, Any]]:
        rules = []
        for rule in self.data.get("jurisdiction_rules") or []:
            scope = rule.get("jurisdiction", "*")
            if scope == "*" or (jurisdiction and (scope == jurisdiction or jurisdiction.startswith(scope + "-"))):
                rules.append(rule)
        return rules

    def supported_jurisdictions(self) -> List[str]:
        return sorted(
            {
                rule.get("jurisdiction")
                for rule in self.data.get("jurisdiction_rules") or []
                if rule.get("jurisdiction") and rule.get("jurisdiction") != "*"
            }
        )

    def authority_for(self, jurisdiction: Optional[str]) -> List[Dict[str, Any]]:
        return [
            authority
            for authority in self.data.get("authorities") or []
            if jurisdiction and authority.get("jurisdiction") in (jurisdiction, "*")
        ]


def _validate(raw: Dict[str, Any], path: Path) -> None:
    for key in ("pack_id", "version", "title"):
        if not raw.get(key):
            raise PackError(f"{path}: missing required field '{key}'")
    missing = [section for section in REQUIRED_SECTIONS if section not in raw]
    if missing:
        raise PackError(f"{path}: pack '{raw['pack_id']}' missing sections: {', '.join(missing)}")
    concepts = set()
    for entry in raw.get("lexicon") or []:
        if "concept" not in entry:
            raise PackError(f"{path}: lexicon entry without 'concept'")
        if entry["concept"] in concepts:
            raise PackError(f"{path}: duplicate concept '{entry['concept']}'")
        concepts.add(entry["concept"])


def load_pack(path: Path) -> DomainPack:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    _validate(raw, path)
    return DomainPack(
        pack_id=raw["pack_id"],
        version=str(raw["version"]),
        title=raw["title"],
        path=str(path),
        data=raw,
    )


def _installed_pack_paths() -> List[Path]:
    """Discover ``atg_packs_*`` distributions on the import path.

    Packs ship as data-only importable packages so they resolve identically
    from a source checkout and from an installed wheel.
    """

    found: List[Path] = []
    for module in pkgutil.iter_modules():
        if not module.name.startswith("atg_packs_"):
            continue
        try:
            imported = importlib.import_module(module.name)
        except ImportError:
            continue
        for location in getattr(imported, "__path__", []):
            candidate = Path(location) / "pack.yaml"
            if candidate.is_file():
                found.append(candidate)
    return sorted(found)


def default_pack_paths() -> List[Path]:
    paths: List[Path] = sorted(_CORE_PACK_DIR.glob("*/pack.yaml"))
    installed = _installed_pack_paths()
    paths += installed or sorted(_PACKAGES_DIR.glob("atg-packs-*/*/pack.yaml"))
    extra = os.environ.get("ATG_PACK_PATH", "")
    for item in filter(None, extra.split(os.pathsep)):
        candidate = Path(item)
        if candidate.is_dir():
            paths += sorted(candidate.glob("*/pack.yaml"))
        elif candidate.is_file():
            paths.append(candidate)
    return paths


class PackRegistry:
    """Loads packs and exposes lexicon/concept lookups across them."""

    def __init__(self, packs: Optional[Iterable[DomainPack]] = None) -> None:
        self._packs: Dict[str, DomainPack] = {}
        for pack in packs or []:
            self.add(pack)

    @classmethod
    def load_default(cls) -> "PackRegistry":
        registry = cls()
        for path in default_pack_paths():
            registry.add(load_pack(path))
        return registry

    def add(self, pack: DomainPack) -> None:
        self._packs[pack.pack_id] = pack

    def __contains__(self, pack_id: str) -> bool:
        return pack_id in self._packs

    def get(self, pack_id: str) -> Optional[DomainPack]:
        return self._packs.get(pack_id)

    def ids(self) -> List[str]:
        return sorted(self._packs)

    def versions(self, pack_ids: Optional[Iterable[str]] = None) -> Dict[str, str]:
        selected = list(pack_ids) if pack_ids is not None else self.ids()
        return {pid: self._packs[pid].version for pid in selected if pid in self._packs}

    def select(self, pack_ids: Optional[Iterable[str]] = None) -> List[DomainPack]:
        if pack_ids is None:
            return [self._packs[pid] for pid in self.ids()]
        return [self._packs[pid] for pid in pack_ids if pid in self._packs]

    def resolve_for_context(self, industry: Optional[str], profession: Optional[str] = None) -> List[str]:
        """Which packs apply to a context. COMMON always applies."""
        selected = ["COMMON"] if "COMMON" in self._packs else []
        for pack_id, pack in self._packs.items():
            if pack_id in selected:
                continue
            domains = {str(d).upper() for d in pack.data.get("domains") or []}
            domains.add(pack_id.upper())
            professions = {str(p).upper() for p in pack.data.get("roles") or [] if isinstance(p, str)}
            if industry and industry.upper() in domains or profession and profession.upper() in professions:
                selected.append(pack_id)
        return selected

    # -- lexicon indices -------------------------------------------------
    def lexicon_index(self, pack_ids: Optional[Iterable[str]] = None) -> Dict[str, List[LexiconEntry]]:
        index: Dict[str, List[LexiconEntry]] = {}
        for pack in self.select(pack_ids):
            for entry in pack.lexicon:
                for term in entry.all_terms():
                    index.setdefault(term.lower(), []).append(entry)
        return index

    def concept_index(self, pack_ids: Optional[Iterable[str]] = None) -> Dict[str, LexiconEntry]:
        index: Dict[str, LexiconEntry] = {}
        for pack in self.select(pack_ids):
            for entry in pack.lexicon:
                index[entry.concept] = entry
        return index

    def crosswalk(self, concept: str, pack_ids: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        mappings = []
        for pack in self.select(pack_ids):
            for mapping in pack.data.get("source_mappings") or []:
                if mapping.get("concept") == concept:
                    enriched = dict(mapping)
                    enriched["from_pack"] = pack.pack_id
                    enriched["from_pack_version"] = pack.version
                    mappings.append(enriched)
        return mappings

    def translation_rules(self, pack_ids: Optional[Iterable[str]] = None) -> List[Tuple[str, Dict[str, Any]]]:
        rules = []
        for pack in self.select(pack_ids):
            for rule in pack.data.get("translation_rules") or []:
                rules.append((pack.pack_id, rule))
        return rules
