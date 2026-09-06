"""Domain pack tests: every pack is versioned, complete and testable."""

from __future__ import annotations

import pytest
from atg_core import ContextVector, PackRegistry, Representation, parse, translate_domain
from atg_core.packs import REQUIRED_SECTIONS

TEXT = Representation(kind="human_text", name="natural_language", version="1")
EXPECTED_PACKS = {"COMMON", "TECH", "TAX", "REAL_ESTATE", "LEGAL", "FILM"}


@pytest.fixture(scope="module")
def registry() -> PackRegistry:
    return PackRegistry.load_default()


def test_all_initial_packs_load_with_versions(registry):
    assert set(registry.ids()) >= EXPECTED_PACKS
    for pack_id, version in registry.versions().items():
        assert version, f"pack {pack_id} must declare a version"


@pytest.mark.parametrize("pack_id", sorted(EXPECTED_PACKS))
def test_pack_declares_every_required_section(registry, pack_id):
    pack = registry.get(pack_id)
    assert pack is not None
    for section in REQUIRED_SECTIONS:
        assert section in pack.data, f"{pack_id} missing section {section}"


def test_pack_selection_follows_context(registry):
    assert "TAX" in registry.resolve_for_context("TAX", None)
    assert "COMMON" in registry.resolve_for_context("TECH", None)
    assert registry.resolve_for_context(None, None) == ["COMMON"]


def test_legal_pack_keeps_jurisdiction_and_authority(registry):
    envelope = parse(
        "The firm placed the funds in a client account under the governing law.",
        TEXT,
        ContextVector(locale="en-GB", industry="LEGAL", jurisdiction="GB"),
        registry=registry,
    )
    concepts = {entity.concept for entity in envelope.entities}
    assert any(concept.startswith("legal.") for concept in concepts)
    assert any(entity.type == "authority" for entity in envelope.entities)
    assert not envelope.requires_escalation


def test_film_pack_distinguishes_roles_and_incentives(registry):
    us = parse(
        "The line producer tracked the production incentive for principal photography.",
        TEXT,
        ContextVector(locale="en-US", industry="FILM", jurisdiction="US-CA"),
        registry=registry,
    )
    gb = parse(
        "The line producer tracked the production incentive for principal photography.",
        TEXT,
        ContextVector(locale="en-GB", industry="FILM", jurisdiction="GB"),
        registry=registry,
    )
    assert {e.concept for e in us.entities} & {e.concept for e in gb.entities}
    us_rules = [c.expression for c in us.constraints]
    gb_rules = [c.expression for c in gb.constraints]
    assert us_rules != gb_rules, "incentive jurisdiction must not be flattened"


def test_domain_translation_uses_declared_crosswalks_only(registry):
    envelope = parse(
        "The escrow held the earnest money until closing.",
        TEXT,
        ContextVector(locale="en-US", industry="REAL_ESTATE", jurisdiction="US-CA"),
        registry=registry,
    )
    translated = translate_domain(envelope, "LEGAL", registry=registry)
    rule_ids = [r for t in translated.provenance.transformations for r in t.rule_ids]
    assert any(rule.startswith("atg.crosswalk") or "crosswalk" in rule for rule in rule_ids) or translated.unknowns
