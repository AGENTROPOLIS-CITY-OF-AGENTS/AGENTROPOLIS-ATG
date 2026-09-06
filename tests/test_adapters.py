"""Adapter seam tests: ontology, utility grid, intelligence router."""

from __future__ import annotations

from atg_core import ContextVector, Representation, parse
from atg_ontology_adapter import OntologyAdapter, PackOntologyAdapter
from atg_router_adapter import IntelligenceRouterAdapter, PolicyRouterAdapter, ReasoningRequest
from atg_utility_adapter import Capability, StaticUtilityGridAdapter, UtilityGridAdapter

TEXT = Representation(kind="human_text", name="natural_language", version="1")


def test_pack_ontology_adapter_satisfies_the_protocol_and_resolves_relations():
    adapter = PackOntologyAdapter()
    assert isinstance(adapter, OntologyAdapter)
    node = adapter.get_concept("re.concept.escrow")
    assert node is not None and node.pack == "REAL_ESTATE" and node.pack_version
    assert adapter.describe()["concepts"] > 0
    assert adapter.neighbors("legal.concept.governing_law")


def test_utility_grid_denies_capabilities_that_violate_region_and_residency():
    adapter = StaticUtilityGridAdapter(
        [
            Capability(id="eu-compute", kind="compute", name="eu-compute", regions=["DE", "EU"], data_residency="EU"),
            Capability(id="us-compute", kind="compute", name="us-compute", regions=["US"], data_residency="US"),
        ]
    )
    assert isinstance(adapter, UtilityGridAdapter)
    envelope = parse("Store the customer record.", TEXT, ContextVector(region="DE", locale="de-DE", industry="TECH"))
    decision = adapter.select(envelope, ContextVector(region="DE", locale="de-DE", industry="TECH"))
    assert [c.id for c in decision.allowed] == ["eu-compute"]
    assert decision.denied and decision.denied[0]["id"] == "us-compute"


def test_router_sends_blocking_escalation_to_human_and_high_impact_to_frontier():
    router = PolicyRouterAdapter()
    assert isinstance(router, IntelligenceRouterAdapter)

    ambiguous = parse("Please check the title.", TEXT, ContextVector(locale="en-US", industry="TECH"))
    assert router.route(ReasoningRequest(envelope=ambiguous)).tier == "human"

    tax = parse(
        "Charge value added tax on the taxable event.",
        TEXT,
        ContextVector(locale="en-GB", industry="TAX", jurisdiction="GB"),
    )
    assert router.route(ReasoningRequest(envelope=tax)).tier == "frontier"

    tech = parse("Deployment must support rollback.", TEXT, ContextVector(locale="en-US", industry="TECH", region="US"))
    decision = router.route(ReasoningRequest(envelope=tech))
    assert decision.tier == "local"
    assert decision.signals["pack_versions"]

    deterministic = router.route(ReasoningRequest(envelope=tech, requires_determinism=True))
    assert deterministic.tier == "deterministic"
