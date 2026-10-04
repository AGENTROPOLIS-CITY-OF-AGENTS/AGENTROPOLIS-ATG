import json
import re
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from atralith.fiscalith_bridge import (  # noqa: E402
    FISCALITH_SCHEMA_ID,
    FORBIDDEN_KEYS,
    AuthorityRequired,
    BoundaryViolation,
    BridgeError,
    CorridorHandoff,
    compile_financial_message,
    detect_financial_speech_act,
    map_result_to_atg,
)

SCHEMA_PATH = ROOT / "contracts" / "core" / "atralith-financial-message.schema.json"
BRIDGE_DOC = ROOT / "docs" / "ATRALITH-FISCALITH-BRIDGE.md"
REGISTRY = ROOT / "registries" / "fiscalith-schemas.yaml"

JSON_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def mini_validate(schema, value, path="$"):
    """Stdlib-only validator: type, enum, const, required, minLength, items, additionalProperties."""
    errors = []
    types = schema.get("type")
    if types is not None:
        allowed = tuple(JSON_TYPES[t] for t in ([types] if isinstance(types, str) else types))
        if not isinstance(value, allowed) or (isinstance(value, bool) and bool not in allowed):
            return [f"{path}: expected {types}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: not in enum")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: const mismatch")
    if isinstance(value, str) and "minLength" in schema and len(value) < schema["minLength"]:
        errors.append(f"{path}: shorter than minLength")
    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: missing {req}")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                errors.extend(mini_validate(props[key], sub, f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property {key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors.extend(mini_validate(schema["items"], item, f"{path}[{i}]"))
    return errors


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def doc_example():
    match = re.search(r"```json\n(.*?)\n```", BRIDGE_DOC.read_text(), re.S)
    return json.loads(match.group(1))


def base_message(**overrides):
    msg = {
        "speech_act": "REQUEST",
        "from_agent_entity_ref": "AGENTENTITY:TREASURY-042",
        "to_agent_entity_ref": "AGENTENTITY:VENDOR-12",
        "correlation_id": "corr-0001",
        "mandate_ref": "M-881",
        "delegation_chain": ["AGENTENTITY:CFO-01", "AGENTENTITY:TREASURY-042"],
        "capability_refs": ["cap.fiscalith.pay"],
        "execution_envelope_ref": None,
        "requested_proof_classes": ["ProofOfSettlement"],
        "fiscalith_payload": {"intent_id": "fi-1", "kind": "PAY"},
        "schema_ref": FISCALITH_SCHEMA_ID,
    }
    msg.update(overrides)
    return msg


def accept_all(payload):
    return None


class DetectTests(unittest.TestCase):
    def test_detects_payload(self):
        self.assertTrue(detect_financial_speech_act(base_message()))

    def test_non_financial(self):
        msg = base_message()
        del msg["fiscalith_payload"]
        self.assertFalse(detect_financial_speech_act(msg))
        self.assertFalse(detect_financial_speech_act("not a dict"))


class CompileTests(unittest.TestCase):
    def test_positive_compile(self):
        seen = []
        handoff = compile_financial_message(base_message(), seen.append)
        self.assertIsInstance(handoff, CorridorHandoff)
        self.assertEqual(seen, [base_message()["fiscalith_payload"]])
        self.assertEqual(handoff.next_hop, "EXECUTION_ENVELOPE")
        self.assertFalse(handoff.grants_authority)
        self.assertEqual(handoff.correlation_id, "corr-0001")
        self.assertEqual(handoff.mandate_ref, "M-881")
        self.assertEqual(handoff.fiscalith_payload, {"intent_id": "fi-1", "kind": "PAY"})
        self.assertFalse(FORBIDDEN_KEYS & set(asdict(handoff)))

    def test_grants_authority_is_constant(self):
        with self.assertRaises(TypeError):
            CorridorHandoff(
                correlation_id="c", from_agent_entity_ref="a", to_agent_entity_ref="b", mandate_ref=None,
                delegation_chain=[], capability_refs=[], execution_envelope_ref=None,
                requested_proof_classes=[], fiscalith_payload={}, grants_authority=True,
            )

    def test_missing_mandate_on_request(self):
        for act in ("REQUEST", "ACCEPT", "DELEGATE"):
            with self.assertRaises(AuthorityRequired):
                compile_financial_message(base_message(speech_act=act, mandate_ref=None), accept_all)

    def test_mandate_optional_on_non_authority_acts(self):
        handoff = compile_financial_message(base_message(speech_act="PROPOSE", mandate_ref=None), accept_all)
        self.assertIsNone(handoff.mandate_ref)

    def test_forbidden_envelope_keys_rejected(self):
        for key in ("rail", "provider", "chain", "wallet", "signer", "Provider"):
            with self.assertRaises(BoundaryViolation):
                compile_financial_message(base_message(**{key: "arc"}), accept_all)

    def test_forbidden_payload_keys_rejected(self):
        for key in ("rail", "provider", "signer", "wallet"):
            payload = {"intent_id": "fi-1", key: "arc"}
            with self.assertRaises(BoundaryViolation):
                compile_financial_message(base_message(fiscalith_payload=payload), accept_all)

    def test_payload_validator_failure_propagates(self):
        class FiscalithRejected(Exception):
            pass

        def reject(payload):
            raise FiscalithRejected("amount required")

        with self.assertRaises(FiscalithRejected):
            compile_financial_message(base_message(), reject)

    def test_payload_must_be_object(self):
        with self.assertRaises(BridgeError):
            compile_financial_message(base_message(fiscalith_payload="PAY 4200 USDC"), accept_all)

    def test_delegation_chain_preserved(self):
        chain = ["AGENTENTITY:A", "AGENTENTITY:B", "AGENTENTITY:C"]
        handoff = compile_financial_message(base_message(speech_act="DELEGATE", delegation_chain=chain), accept_all)
        self.assertEqual(handoff.delegation_chain, chain)
        self.assertIsNot(handoff.delegation_chain, chain)

    def test_delegation_chain_rejects_empty_hop(self):
        with self.assertRaises(BridgeError):
            compile_financial_message(base_message(delegation_chain=["AGENTENTITY:A", ""]), accept_all)

    def test_invalid_speech_act_and_schema_ref(self):
        with self.assertRaises(BridgeError):
            compile_financial_message(base_message(speech_act="PAY"), accept_all)
        with self.assertRaises(BridgeError):
            compile_financial_message(base_message(schema_ref="https://example.invalid/x.json"), accept_all)

    def test_missing_required_field(self):
        msg = base_message()
        del msg["correlation_id"]
        with self.assertRaises(BridgeError):
            compile_financial_message(msg, accept_all)

    def test_non_financial_message_not_compiled(self):
        msg = base_message()
        del msg["fiscalith_payload"]
        with self.assertRaises(BridgeError):
            compile_financial_message(msg, accept_all)


class ResultMappingTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema()

    def assert_mapping(self, result, expected_act):
        msg = map_result_to_atg(result, "corr-0001")
        self.assertEqual(msg["speech_act"], expected_act)
        self.assertEqual(msg["correlation_id"], "corr-0001")
        self.assertEqual(msg["fiscalith_payload"], result)
        self.assertIsNone(msg["mandate_ref"])
        self.assertEqual(msg["schema_ref"], FISCALITH_SCHEMA_ID)
        self.assertFalse(FORBIDDEN_KEYS & {k.lower() for k in msg})
        self.assertEqual(mini_validate(self.schema, msg), [])
        return msg

    def test_settled_to_receipt(self):
        self.assert_mapping({"status": "SETTLED", "settlement_ref": "S-771"}, "RECEIPT")

    def test_refused_and_failed_to_refuse(self):
        self.assert_mapping({"status": "REFUSED"}, "REFUSE")
        self.assert_mapping({"status": "FAILED"}, "REFUSE")

    def test_pending_and_partial_to_verify(self):
        self.assert_mapping({"status": "PENDING"}, "VERIFY")
        self.assert_mapping({"status": "PARTIAL"}, "VERIFY")

    def test_escalation_overrides_status(self):
        for status in ("SETTLED", "REFUSED", "FAILED", "PENDING", "PARTIAL"):
            self.assert_mapping({"status": status, "escalation_required": True}, "ESCALATE")

    def test_escalation_false_does_not_override(self):
        self.assert_mapping({"status": "SETTLED", "escalation_required": False}, "RECEIPT")

    def test_unknown_status_rejected(self):
        with self.assertRaises(BridgeError):
            map_result_to_atg({"status": "MAYBE"}, "corr-0001")

    def test_result_with_forbidden_keys_rejected(self):
        with self.assertRaises(BoundaryViolation):
            map_result_to_atg({"status": "SETTLED", "rail": "arc"}, "corr-0001")

    def test_result_never_adds_authority_fields(self):
        msg = map_result_to_atg({"status": "SETTLED"}, "corr-0001")
        self.assertNotIn("grants_authority", msg)
        self.assertNotIn("authority", msg)
        self.assertEqual(msg["capability_refs"], [])


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema()

    def test_schema_shape(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIs(self.schema["additionalProperties"], False)
        props = self.schema["properties"]
        self.assertFalse(FORBIDDEN_KEYS & set(props))
        self.assertEqual(props["schema_ref"]["const"], FISCALITH_SCHEMA_ID)
        self.assertIn(FISCALITH_SCHEMA_ID, props["fiscalith_payload"]["$comment"])
        self.assertNotIn("properties", props["fiscalith_payload"])
        self.assertEqual(
            set(props["speech_act"]["enum"]),
            {"REQUEST", "PROPOSE", "OFFER", "ACCEPT", "DELEGATE", "REFUSE", "VERIFY", "RECEIPT", "ESCALATE"},
        )

    def test_schema_contains_no_forbidden_words(self):
        text = SCHEMA_PATH.read_text().lower()
        for key in FORBIDDEN_KEYS:
            self.assertNotRegex(text, rf'"{key}"\s*:')

    def test_doc_example_validates_and_compiles(self):
        example = doc_example()
        self.assertEqual(mini_validate(self.schema, example), [])
        handoff = compile_financial_message(example, accept_all)
        self.assertEqual(handoff.delegation_chain, example["delegation_chain"])

    def test_mini_validator_rejects_bad_messages(self):
        self.assertTrue(mini_validate(self.schema, base_message(rail="arc")))
        self.assertTrue(mini_validate(self.schema, base_message(speech_act="PAY")))
        self.assertTrue(mini_validate(self.schema, base_message(fiscalith_payload="x")))
        msg = base_message()
        del msg["schema_ref"]
        self.assertTrue(mini_validate(self.schema, msg))
        self.assertEqual(mini_validate(self.schema, base_message()), [])

    def test_registry_pins_fiscalith_schema(self):
        text = REGISTRY.read_text()
        self.assertIn(f"id: {FISCALITH_SCHEMA_ID}", text)
        self.assertIn("path: schemas/financial-intent.v1.json", text)
        self.assertRegex(text, r"sha256: [0-9a-f]{64}")
        self.assertNotIn("UNVERIFIED", text)


if __name__ == "__main__":
    unittest.main()
