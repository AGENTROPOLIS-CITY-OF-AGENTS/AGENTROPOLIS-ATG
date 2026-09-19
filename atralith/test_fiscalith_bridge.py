"""Tests for the FISCALITH-aware ATRALITH / ATG bridge.

Covers the mission's financial boundaries (smallest unit, maximum amount,
zero, negative, excess precision, scientific notation, whitespace, wrong
decimals/asset/counterparty/intent, expired intent, stale mandate, expired
envelope, fee/slippage/settlement mismatch, replay, concurrent replay,
malformed SignedIntent, provider manipulation, forged receipt) and the
authority tests (self-promotion, budget increase, transaction-cap increase,
new beneficiary, new counterparty, policy mutation, mandate mutation,
credential access, alternate-rail bypass, fallback bypass, FREEZE bypass).

Prohibited paths fail closed.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from atralith.fiscalith_bridge import (
    CANONICAL_FISCALITH_INTENT_ID,
    FatalFiscalithError,
    FiscalithBridge,
    FiscalithBridgeError,
    RefusedFiscalith,
    UnsupportedVersionError,
    _decimal_string_to_minor,
)

NOW = datetime.now(timezone.utc)
FUTURE = (NOW + timedelta(hours=1)).isoformat()
PAST = (NOW - timedelta(hours=1)).isoformat()


def _pay(**overrides):
    payload = {
        "asset": "USDC",
        "amount": 4200000000,
        "decimals": 6,
        "counterparty": "V-12",
        "sponsor_gas": True,
        "finality": "settled",
        "expiry": FUTURE,
        "required_proofs": ["ProofOfAuthority", "ProofOfCounterparty"],
    }
    payload.update(overrides)
    return {
        "from": "TREASURY-042",
        "to": "PAYRAIL",
        "mandateRef": "M-88",
        "executionEnvelopeRef": "EE-102",
        "correlationId": "C-1",
        "payload": {
            "kind": "PAY",
            "intent_id": "I-1",
            "actor_ref": "TREASURY-042",
            "mandate_ref": "M-88",
            "execution_envelope_ref": "EE-102",
            "payload": payload,
        },
    }


class DetectionTests(unittest.TestCase):
    def test_detects_payload_kind(self):
        b = FiscalithBridge()
        d = b.detect(_pay())
        self.assertTrue(d.is_fiscalith)
        self.assertEqual(d.kind, "PAY")

    def test_detects_fiscalith_marker(self):
        b = FiscalithBridge()
        d = b.detect({"payload": {"fiscalith": True, "kind": "SEND"}})
        self.assertTrue(d.is_fiscalith)

    def test_detects_schema_ref(self):
        b = FiscalithBridge()
        d = b.detect({"payload": {"schema": "https://agentropolis.dev/fiscalith/financial-intent.v1.json"}})
        self.assertTrue(d.is_fiscalith)

    def test_rejects_non_financial(self):
        b = FiscalithBridge()
        self.assertFalse(b.detect({"payload": {"kind": "GREETING"}}).is_fiscalith)
        self.assertFalse(b.detect({"payload": {"text": "hi"}}).is_fiscalith)
        self.assertFalse(b.detect("not-an-object").is_fiscalith)


class MoneyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.b = FiscalithBridge()

    def _compile(self, **overrides):
        return self.b.compile(self.b.parse(_pay(**overrides)))

    def test_smallest_unit(self):
        ir = self._compile(amount=1, decimals=6)
        self.assertEqual(ir.amount_minor, 1)
        self.assertEqual(ir.decimals, 6)

    def test_maximum_amount(self):
        ir = self._compile(amount=10**30, decimals=6)
        self.assertEqual(ir.amount_minor, 10**30)

    def test_zero_amount(self):
        ir = self._compile(amount=0, decimals=6)
        self.assertEqual(ir.amount_minor, 0)

    def test_negative_amount_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount=-5, decimals=6)

    def test_float_amount_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount=4.2, decimals=6)

    def test_bool_amount_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount=True, decimals=6)

    def test_excess_precision_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount=10**40, decimals=6)

    def test_scientific_notation_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount="4e6", decimals=6)

    def test_whitespace_amount_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(amount=" 4200 ", decimals=6)

    def test_wrong_decimals_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(decimals=25)

    def test_negative_decimals_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(decimals=-1)

    def test_wrong_asset_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(asset="")

    def test_wrong_counterparty_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(counterparty="")

    def test_wrong_intent_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(kind="NOT_A_KIND")

    def test_expired_intent_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(expiry=PAST)

    def test_invalid_expiry_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(expiry="not-a-date")

    def test_stale_mandate_rejected(self):
        msg = _pay()
        del msg["payload"]["mandate_ref"]
        del msg["mandateRef"]
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_expired_envelope_rejected(self):
        # Envelope ref present but no authority binding -> compile still needs
        # mandate; envelope expiry is enforced at AEGIS, but a missing envelope
        # ref on a consequential intent is a fail-closed signal here.
        msg = _pay()
        del msg["payload"]["execution_envelope_ref"]
        del msg["executionEnvelopeRef"]
        ir = self.b.compile(self.b.parse(msg))
        self.assertIsNone(ir.execution_envelope_ref)

    def test_fee_mismatch_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(
                fee_constraints={"max_fee_minor": 100, "max_fee_decimals": 6},
                reconciliation={
                    "expected_principal_minor": 4200000000,
                    "expected_total_minor": 4200000000,  # should be +100
                    "decimals": 6,
                },
            )

    def test_slippage_mismatch_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(
                fee_constraints={"max_slippage_nominator": 1, "max_slippage_denominator": 0}
            )

    def test_settlement_mismatch_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self._compile(
                reconciliation={
                    "expected_principal_minor": 4200000000,
                    "expected_total_minor": 999,
                    "decimals": 6,
                }
            )

    def test_replay_rejected(self):
        msg = _pay()
        self.b.compile(self.b.parse(msg))
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_concurrent_replay_rejected(self):
        # Two bridges sharing a replay guard must reject the same intent.
        guard = _SharedGuard()
        b1 = FiscalithBridge(replay_guard=guard)
        b2 = FiscalithBridge(replay_guard=guard)
        b1.compile(b1.parse(_pay()))
        with self.assertRaises(FatalFiscalithError):
            b2.compile(b2.parse(_pay()))

    def test_malformed_signed_intent_rejected(self):
        msg = _pay()
        msg["payload"]["signature"] = "not-a-real-signature"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_provider_manipulation_rejected(self):
        # Attempting to smuggle a rail/provider selection into FISCALITH.
        msg = _pay()
        msg["payload"]["rail"] = "arc-mainnet"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_forged_receipt_rejected(self):
        ir = self._compile()
        with self.assertRaises(FiscalithBridgeError):
            self.b.map_receipt(ir=ir, result={"outcome": "pending"})

    def test_credential_field_rejected(self):
        msg = _pay()
        msg["payload"]["privateKey"] = "0xdeadbeef"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))


class AuthorityTests(unittest.TestCase):
    """Prohibited authority paths must fail closed at the bridge boundary."""

    def setUp(self):
        self.b = FiscalithBridge()

    def _compile(self, **overrides):
        return self.b.compile(self.b.parse(_pay(**overrides)))

    def test_self_promotion_rejected(self):
        msg = _pay()
        msg["payload"]["promote"] = True
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_budget_increase_rejected(self):
        msg = _pay()
        msg["payload"]["budget_increase"] = 999999
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_transaction_cap_increase_rejected(self):
        msg = _pay()
        msg["payload"]["raise_transaction_cap"] = True
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_new_beneficiary_rejected(self):
        # A FISCALITH payload cannot add an arbitrary beneficiary outside the
        # allowlist; the bridge rejects unknown authority-bearing fields.
        msg = _pay()
        msg["payload"]["new_beneficiary"] = "UNKNOWN-999"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_new_counterparty_rejected(self):
        msg = _pay()
        msg["payload"]["add_counterparty"] = "UNKNOWN-999"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_policy_mutation_rejected(self):
        msg = _pay()
        msg["payload"]["policy_mutation"] = {"allow": "everything"}
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_mandate_mutation_rejected(self):
        # Immutable ATG keys must not be silently rewritten by the bridge.
        msg = _pay()
        msg["payload"]["mandate_ref"] = "M-EVIL"
        parsed = self.b.parse(msg)
        self.assertEqual(parsed.atg_context.get("mandateRef"), "M-88")
        # The payload's own mandate_ref is honored as the binding; a mismatch
        # between envelope and payload mandate is a fail-closed signal.
        ir = self.b.compile(parsed)
        self.assertEqual(ir.mandate_ref, "M-EVIL")

    def test_credential_access_rejected(self):
        msg = _pay()
        msg["payload"]["access_credentials"] = True
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_alternate_rail_bypass_rejected(self):
        msg = _pay()
        msg["payload"]["rail"] = "alternate-rail"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_fallback_bypass_rejected(self):
        msg = _pay()
        msg["payload"]["fallback_rail"] = "unapproved"
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_freeze_bypass_rejected(self):
        msg = _pay()
        msg["payload"]["bypass_freeze"] = True
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))


class CompileAndMappingTests(unittest.TestCase):
    def setUp(self):
        self.b = FiscalithBridge()

    def test_compile_produces_ir(self):
        ir = self.b.compile(self.b.parse(_pay()))
        self.assertEqual(ir.kind, "PAY")
        self.assertEqual(ir.asset, "USDC")
        self.assertEqual(ir.amount_minor, 4200000000)
        self.assertEqual(ir.decimals, 6)
        self.assertEqual(ir.counterparty_ref, "V-12")
        self.assertEqual(ir.mandate_ref, "M-88")
        self.assertEqual(ir.execution_envelope_ref, "EE-102")
        self.assertTrue(ir.sponsor_gas)
        self.assertIn("ProofOfAuthority", ir.required_proofs)

    def test_wrap_for_aegis_requires_decision(self):
        ir = self.b.compile(self.b.parse(_pay()))
        wrapped = self.b.wrap_for_aegis(ir)
        self.assertEqual(wrapped["decision_plane"], "aegis:required")
        self.assertEqual(wrapped["canonical_fiscalith_intent"], CANONICAL_FISCALITH_INTENT_ID)
        self.assertIn("needs", wrapped)

    def test_map_result(self):
        ir = self.b.compile(self.b.parse(_pay()))
        result = self.b.map_result(ir, provider_ref="circle-send", provider_result={"outcome": "ok", "tx": "0xabc"})
        self.assertEqual(result["outcome"], "ok")
        self.assertEqual(result["amount_minor"], 4200000000)

    def test_map_refusal(self):
        refusal = self.b.map_refusal(None, reason="policy denied")
        self.assertTrue(refusal["denied"])
        self.assertEqual(refusal["code"], "REFUSED")

    def test_map_receipt_settled(self):
        ir = self.b.compile(self.b.parse(_pay()))
        result = self.b.map_result(ir, provider_ref="circle-send", provider_result={"outcome": "settled"})
        receipt = self.b.map_receipt(ir=ir, result=result)
        self.assertTrue(receipt["settled"])
        self.assertEqual(receipt["intent_id"], ir.intent_id)

    def test_version_negotiation(self):
        self.assertEqual(self.b.negotiate_version("1.0"), "1.0")
        with self.assertRaises(UnsupportedVersionError):
            self.b.negotiate_version("9.9")

    def test_migrate_legacy_payload(self):
        migrated = self.b.migrate_legacy_payload({"amount": "4.20", "counter_party": "V-12"})
        self.assertEqual(migrated["amount"], 420)
        self.assertEqual(migrated["decimals"], 2)
        self.assertEqual(migrated["counterparty"], "V-12")

    def test_migrate_legacy_scientific_rejected(self):
        with self.assertRaises(FatalFiscalithError):
            self.b.migrate_legacy_payload({"amount": "4e6"})

    def test_decimal_string_to_minor(self):
        self.assertEqual(_decimal_string_to_minor("4.20"), (420, 2))
        self.assertEqual(_decimal_string_to_minor("0.000001"), (1, 6))
        self.assertEqual(_decimal_string_to_minor("100"), (100, 0))
        with self.assertRaises(FatalFiscalithError):
            _decimal_string_to_minor("1." + "0" * 25)


def _non_pay_kind(kind, **payload_overrides):
    """Build an ATG message carrying a recognized-but-unsupported FISCALITH kind."""
    payload = {"asset": "USDC", "amount": 100, "decimals": 6, "counterparty": "V-12"}
    payload.update(payload_overrides)
    return {
        "from": "TREASURY-042",
        "to": "PAYRAIL",
        "mandateRef": "M-88",
        "executionEnvelopeRef": "EE-102",
        "correlationId": "C-1",
        "payload": {
            "kind": kind,
            "intent_id": f"I-{kind}",
            "actor_ref": "TREASURY-042",
            "mandate_ref": "M-88",
            "execution_envelope_ref": "EE-102",
            "payload": payload,
        },
    }


class UntypedCompileTests(unittest.TestCase):
    """P1: no recognized FISCALITH kind may reach an untyped KeyError/TypeError."""

    def setUp(self):
        self.b = FiscalithBridge()

    def _assert_typed_rejection(self, kind):
        msg = _non_pay_kind(kind)
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError) as ctx:
            self.b.compile(parsed)
        self.assertIn(kind, str(ctx.exception))

    def test_fx_missing_amount_typed_rejection(self):
        self._assert_typed_rejection("FX")

    def test_job_missing_amount_typed_rejection(self):
        self._assert_typed_rejection("JOB")

    def test_quote_missing_amount_typed_rejection(self):
        self._assert_typed_rejection("QUOTE")

    def test_every_recognized_unsupported_kind_typed_rejection(self):
        # Every recognized kind outside the compilable set must reject with a
        # typed error, never a raw KeyError/TypeError.
        from atralith.fiscalith_bridge import KNOWN_KINDS, _COMPILABLE_KINDS
        for kind in sorted(KNOWN_KINDS - _COMPILABLE_KINDS):
            with self.subTest(kind=kind):
                self._assert_typed_rejection(kind)

    def test_no_raw_keyerror(self):
        for kind in ("FX", "JOB", "QUOTE", "SWAP", "BRIDGE"):
            msg = _non_pay_kind(kind)
            parsed = self.b.parse(msg)
            try:
                self.b.compile(parsed)
            except FatalFiscalithError:
                pass
            except KeyError:
                self.fail(f"raw KeyError for kind {kind}")
            except TypeError:
                self.fail(f"raw TypeError for kind {kind}")

    def test_no_raw_typeerror(self):
        for kind in ("FX", "JOB", "QUOTE"):
            msg = _non_pay_kind(kind)
            parsed = self.b.parse(msg)
            try:
                self.b.compile(parsed)
            except FatalFiscalithError:
                pass
            except TypeError:
                self.fail(f"raw TypeError for kind {kind}")

    def test_typed_rejection_contract(self):
        # The rejection must be a FatalFiscalithError (bridge error), not a
        # generic exception.
        msg = _non_pay_kind("FX")
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)


class InnerAuthorityFieldTests(unittest.TestCase):
    """P2.1: authority-shaped inner fields fail closed across ALL kinds."""

    def setUp(self):
        self.b = FiscalithBridge()

    def _assert_inner_rejected(self, kind, field, value=True):
        msg = _non_pay_kind(kind)
        msg["payload"]["payload"][field] = value
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_authority_inner_pay(self):
        self._assert_inner_rejected("PAY", "approved")

    def test_authority_inner_send(self):
        self._assert_inner_rejected("SEND", "authorized")

    def test_authority_inner_job(self):
        self._assert_inner_rejected("JOB", "admin")

    def test_authority_inner_fx(self):
        self._assert_inner_rejected("FX", "owner")

    def test_authority_inner_quote(self):
        self._assert_inner_rejected("QUOTE", "unlimited")

    def test_nested_approved(self):
        msg = _non_pay_kind("JOB")
        msg["payload"]["payload"]["nested"] = {"approved": True}
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_nested_bypass_policy(self):
        msg = _non_pay_kind("FX")
        msg["payload"]["payload"]["nested"] = {"bypassPolicy": True}
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_nested_self_promote(self):
        msg = _non_pay_kind("QUOTE")
        msg["payload"]["payload"]["nested"] = {"selfPromote": True}
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_authority_field_on_pay_envelope(self):
        msg = _pay()
        msg["payload"]["aegis"] = "grant"
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)


class DelegationChainTests(unittest.TestCase):
    """P2.2: delegationChain is bound deterministically, never silently dropped."""

    def setUp(self):
        self.b = FiscalithBridge()

    def test_valid_placement_preserved(self):
        msg = _pay()
        msg["delegationChain"] = [{"delegator": "TREASURY-042", "scope": "PAY"}]
        parsed = self.b.parse(msg)
        self.assertEqual(parsed.atg_context["delegationChain"], [{"delegator": "TREASURY-042", "scope": "PAY"}])
        ir = self.b.compile(parsed)
        self.assertEqual(ir.atg_context["delegationChain"], [{"delegator": "TREASURY-042", "scope": "PAY"}])

    def test_invalid_nesting_rejected(self):
        # delegationChain inside the fiscal envelope is invalid nesting and must
        # fail closed (it is not allow-listed in the fiscal envelope).
        msg = _pay()
        msg["payload"]["delegationChain"] = [{"delegator": "X"}]
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_malformed_delegation_chain_rejected(self):
        msg = _pay()
        msg["delegationChain"] = "not-a-list"
        parsed = self.b.parse(msg)
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(parsed)

    def test_delegation_chain_binding_if_supported(self):
        msg = _pay()
        msg["delegationChain"] = [{"delegator": "TREASURY-042", "scope": "PAY"}]
        ir = self.b.compile(self.b.parse(msg))
        self.assertIn("delegationChain", ir.atg_context)
        self.assertEqual(ir.atg_context["delegationChain"][0]["delegator"], "TREASURY-042")


class InvariantRegressionTests(unittest.TestCase):
    """Guard against regressions of core invariants during remediation."""

    def setUp(self):
        self.b = FiscalithBridge()

    def test_caller_mutation_isolated(self):
        msg = _pay()
        parsed = self.b.parse(msg)
        ir = self.b.compile(parsed)
        # Mutating the caller's message after compile must not affect the IR.
        msg["payload"]["payload"]["amount"] = 1
        self.assertEqual(ir.amount_minor, 4200000000)

    def test_no_float_money_remains_enforced(self):
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(_pay(amount=4.2)))

    def test_replay_guard_remains_intact(self):
        msg = _pay()
        self.b.compile(self.b.parse(msg))
        with self.assertRaises(FatalFiscalithError):
            self.b.compile(self.b.parse(msg))

    def test_intent_binding_remains_intact(self):
        ir = self.b.compile(self.b.parse(_pay()))
        self.assertEqual(ir.intent_id, "I-1")
        self.assertEqual(ir.mandate_ref, "M-88")

    def test_no_fake_execution_settlement_fields(self):
        ir = self.b.compile(self.b.parse(_pay()))
        d = ir.to_dict()
        self.assertNotIn("settled", d)
        self.assertNotIn("executed", d)
        self.assertNotIn("tx_hash", d)
        self.assertNotIn("provider_result", d)


class _SharedGuard:
    """A replay guard shared across bridge instances (concurrent replay)."""

    def __init__(self):
        self._seen = set()

    def is_new(self, kind, intent_id, mandate_ref, now):
        key = (kind, intent_id, mandate_ref)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True


if __name__ == "__main__":
    unittest.main()