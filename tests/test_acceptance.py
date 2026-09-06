"""The ten ATG acceptance tests.

Each test maps 1:1 to an acceptance criterion for ATG as Layer-1 semantic
infrastructure. They assert semantic preservation, not fluency.
"""

from __future__ import annotations

import sqlite3

import pytest
from atg_core import (
    ContextVector,
    PackRegistry,
    Representation,
    build_evidence_packet,
    localize,
    normalize,
    parse,
    resolve_context,
    roundtrip,
    translate_code,
    translate_human,
)
from atg_core.code import shell_semantics
from atg_core.provenance import provenance_record

TEXT = Representation(kind="human_text", name="natural_language", version="1")


@pytest.fixture(scope="module")
def registry() -> PackRegistry:
    return PackRegistry.load_default()


# 1 -------------------------------------------------------------------------
def test_us_and_uk_english_share_canonical_intent_but_not_output(registry):
    us = normalize(
        parse(
            "Take the elevator to the apartment and post the check by zip code.",
            TEXT,
            ContextVector(locale="en-US", industry="TECH"),
            registry=registry,
        ),
        registry=registry,
    )
    uk = normalize(
        parse(
            "Take the lift to the flat and post the cheque by postcode.",
            TEXT,
            ContextVector(locale="en-GB", industry="TECH"),
            registry=registry,
        ),
        registry=registry,
    )

    assert us.core_hash() == uk.core_hash(), "same meaning must share a locale-free core signature"
    assert {e.concept for e in us.entities} == {e.concept for e in uk.entities}

    rendered_uk = translate_human(us, ContextVector(locale="en-GB", industry="TECH"), registry=registry)
    rendered_us = translate_human(uk, ContextVector(locale="en-US", industry="TECH"), registry=registry)
    assert "lift" in rendered_uk.rendered and "elevator" not in rendered_uk.rendered
    assert "elevator" in rendered_us.rendered and "lift" not in rendered_us.rendered
    # Region remains an execution difference even when meaning matches.
    assert us.canonical_hash() != uk.canonical_hash()


# 2 -------------------------------------------------------------------------
def test_real_estate_terminology_preserves_transaction_and_contract_concepts(registry):
    envelope = parse(
        "The buyer deposited earnest money into escrow before closing.",
        TEXT,
        ContextVector(locale="en-US", industry="REAL_ESTATE", jurisdiction="US-CA"),
        registry=registry,
    )
    concepts = {e.concept for e in envelope.entities}
    assert {"re.concept.earnest_money", "re.concept.escrow", "re.concept.closing"} <= concepts

    uk = translate_human(
        envelope,
        ContextVector(locale="en-GB", industry="REAL_ESTATE", jurisdiction="GB"),
        registry=registry,
    )
    # Surfaces change; the transaction concepts do not.
    assert {e.concept for e in uk.entities} >= {"re.concept.escrow", "re.concept.closing"}
    assert "completion" in uk.rendered
    assert any(c.kind == "obligation" or "escrow" in c.expression for c in envelope.constraints)


# 3 -------------------------------------------------------------------------
def test_tax_authority_and_jurisdiction_attach_and_unsupported_jurisdiction_escalates(registry):
    gb = parse(
        "Charge value added tax on the taxable event.",
        TEXT,
        ContextVector(locale="en-GB", industry="TAX", jurisdiction="GB"),
        registry=registry,
    )
    assert "authority.hmrc" in {e.concept for e in gb.entities}
    assert not gb.requires_escalation

    unsupported = parse(
        "Charge value added tax on the taxable event.",
        TEXT,
        ContextVector(locale="en-GB", industry="TAX", jurisdiction="ZZ-NOWHERE"),
        registry=registry,
    )
    assert unsupported.requires_escalation
    assert any(u.kind == "unsupported_jurisdiction" and u.blocking for u in unsupported.unknowns)

    missing = parse(
        "Charge value added tax on the taxable event.",
        TEXT,
        ContextVector(locale="en-GB", industry="TAX"),
        registry=registry,
    )
    assert missing.requires_escalation, "high-impact domains must never assume a jurisdiction"


# 4 -------------------------------------------------------------------------
PYTHON_SOURCE = '''
def average_price(prices: list[float], tax_rate: float) -> float:
    if len(prices) == 0:
        raise ValueError("prices must not be empty")
    total = sum(prices)
    return (total / len(prices)) * (1 + tax_rate)
'''


def test_python_to_typescript_preserves_contracts_and_roundtrips(registry):
    result = roundtrip(
        PYTHON_SOURCE,
        Representation(kind="code", name="python", version="3.11"),
        Representation(kind="code", name="typescript", version="5.4"),
        ContextVector(programming_language="python", industry="TECH"),
        ContextVector(programming_language="typescript", industry="TECH"),
        registry=registry,
    )
    assert "export function averagePrice" in result.rendered
    assert "throw new Error" in result.rendered
    assert result.passed
    assert result.validation.semantic_equivalence == 1.0
    assert result.roundtrip_score >= 0.99
    # Integer/number widening is recorded rather than hidden.
    notes = [n for t in result.target_envelope.provenance.transformations for n in t.notes]
    assert any("IEEE-754" in note or "widen" in note.lower() for note in notes) or not any(
        p.get("type") == "integer"
        for c in result.source_envelope.contracts
        for p in c.signature.get("params", [])
    )


# 5 -------------------------------------------------------------------------
POSTGRES_DDL = """
CREATE TABLE listing (
  id SERIAL PRIMARY KEY,
  payload JSONB NOT NULL,
  price NUMERIC(12,2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  active BOOLEAN NOT NULL
);
"""


def test_postgres_to_sqlite_handles_dialect_constructs_explicitly(registry):
    source = Representation(kind="code", name="sql", version="2016", dialect="postgresql")
    target = Representation(kind="code", name="sql", version="3", dialect="sqlite")
    envelope = parse(
        POSTGRES_DDL,
        source,
        ContextVector(programming_language="sql", programming_dialect="postgresql", industry="TECH"),
        registry=registry,
    )
    rendered, translated = translate_code(envelope, target, registry=registry)

    assert "INTEGER PRIMARY KEY AUTOINCREMENT" in rendered
    sqlite3.connect(":memory:").execute(rendered)  # emitted DDL must actually execute

    rule_ids = [r for t in translated.provenance.transformations for r in t.rule_ids]
    assert "sql.pg_sqlite.jsonb" in rule_ids
    assert "sql.pg_sqlite.timestamptz" in rule_ids
    assert translated.requires_escalation, "JSONB/TIMESTAMPTZ loss must be visible, not assumed equivalent"
    assert translated.is_lossy()


# 6 -------------------------------------------------------------------------
def test_powershell_is_not_posix_shell(registry):
    bash = Representation(kind="code", name="shell", version="5.2", dialect="bash")
    powershell = Representation(kind="code", name="shell", version="7.4", dialect="powershell")
    envelope = parse(
        "ls | grep foo | awk",
        bash,
        ContextVector(programming_language="shell", programming_dialect="bash"),
        registry=registry,
    )
    rendered, translated = translate_code(envelope, powershell, registry=registry)

    assert shell_semantics.pipeline_model("bash") == "byte-stream"
    assert shell_semantics.pipeline_model("powershell") == "object-stream"
    assert "Get-ChildItem" in rendered
    assert translated.requires_escalation
    assert any(u.kind == "execution_model_divergence" for u in translated.unknowns)


# 7 -------------------------------------------------------------------------
def test_region_changes_execution_assumptions_not_only_strings(registry):
    envelope = parse(
        "Store the customer record and charge value added tax.",
        TEXT,
        ContextVector(locale="en-US", region="US", industry="TECH", jurisdiction="US"),
        registry=registry,
    )
    result = localize(
        envelope,
        ContextVector(locale="de-DE", region="DE", industry="TECH", jurisdiction="DE"),
        registry=registry,
    )
    changed = set(result.changed_execution_fields)
    assert {"currency", "units", "date_format", "regulations", "data_residency"} <= changed
    assert result.execution_assumptions["currency"] == "EUR"
    assert any("GDPR" in regulation for regulation in result.execution_assumptions["regulations"])
    assert any(c.origin.startswith("region:") for c in result.envelope.constraints)


# 8 -------------------------------------------------------------------------
def test_every_transform_yields_lineage_pack_versions_and_confidence(registry):
    result = roundtrip(
        PYTHON_SOURCE,
        Representation(kind="code", name="python", version="3.11"),
        Representation(kind="code", name="typescript", version="5.4"),
        ContextVector(programming_language="python", industry="TECH"),
        registry=registry,
    )
    record = provenance_record(result.target_envelope, result.validation.to_dict())

    tools = [t["tool"] for t in record["transformations"]]
    assert "atg.parse" in tools and "atg.normalize" in tools and "atg.translate.code" in tools
    assert record["pack_versions"], "pack versions must be recorded on every transform chain"
    assert record["source"]["representation"]["name"] == "python"
    assert record["target"]["representation"]["name"] == "typescript"
    assert 0.0 <= record["confidence"] <= 1.0
    assert record["validation"]["passed"] is True
    for transformation in record["transformations"]:
        assert "confidence" in transformation and "at" in transformation


# 9 -------------------------------------------------------------------------
def test_ambiguous_term_requires_escalation(registry):
    envelope = parse(
        "Please check the title before we proceed.",
        TEXT,
        ContextVector(locale="en-US", industry="TECH"),
        registry=registry,
    )
    assert envelope.requires_escalation
    ambiguity = [u for u in envelope.unknowns if u.kind == "ambiguity"]
    assert ambiguity and len(ambiguity[0].candidates) > 1

    disambiguated = parse(
        "Please check the title before we proceed.",
        TEXT,
        ContextVector(locale="en-US", industry="REAL_ESTATE", jurisdiction="US-CA"),
        registry=registry,
    )
    assert "re.concept.title_ownership" in {e.concept for e in disambiguated.entities}


# 10 ------------------------------------------------------------------------
LARGE_DOCUMENT = (
    "The vendor operates a managed platform. "
    "Deployment happens every weekday and rollback must complete within fifteen minutes. "
    "Personal data is stored in the primary region and residency requirements apply. "
    "Unrelated marketing copy about our journey and our people. "
    "More unrelated narrative filler about company culture and offsites. "
    "The service level agreement defines an incident response target. "
) * 12


def test_large_context_reduces_to_evidence_packet(registry):
    packet = build_evidence_packet(
        LARGE_DOCUMENT,
        ContextVector(locale="en-US", region="US", industry="TECH", jurisdiction="US"),
        registry=registry,
    )
    data = packet.to_dict()

    assert data["claims"], "evidence packet must retain concept-bearing claims"
    assert packet.packet_chars < packet.source_chars
    assert packet.reduction_ratio > 0.5
    assert data["pack_versions"] and 0.0 <= data["confidence"] <= 1.0
    assert all(len(claim["source_span"]) == 2 for claim in data["claims"])
    concepts = {claim["concept"] for claim in data["claims"]}
    assert any(concept.startswith("tech.") for concept in concepts)


# context resolution guardrail -----------------------------------------------
def test_resolve_context_infers_region_but_not_high_impact_jurisdiction():
    resolved = resolve_context(ContextVector(locale="en-GB"))
    assert resolved.context.region == "GB" and resolved.context.language == "en"
    assert resolved.context.currency == "GBP"

    tax = resolve_context(ContextVector(locale="en-GB", industry="TAX"))
    assert tax.requires_escalation
    assert any(u["kind"] == "missing_jurisdiction" for u in tax.unknowns)
