#!/usr/bin/env python3
"""ATG:LIVING-GAME profile conformance.

Run: python3 -m unittest tests/test_living_game_profile.py
Requires the `jsonschema` package.
"""

import copy
import json
import os
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE_SCHEMA = json.loads((ROOT / "contracts/core/execution-envelope.schema.json").read_text())
EXTENSION_SCHEMA = json.loads((ROOT / "contracts/profiles/living-game-extension.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/living-game-reward-envelope.example.json").read_text())

envelope_validator = Draft202012Validator(ENVELOPE_SCHEMA)
extension_validator = Draft202012Validator(EXTENSION_SCHEMA)


def validate(envelope):
    """Validate the canonical envelope and its living_game extension; return error messages."""
    errors = [e.message for e in envelope_validator.iter_errors(envelope)]
    if "living_game" not in envelope.get("must_understand", []):
        errors.append("must_understand must list living_game")
    ext = envelope.get("extensions", {}).get("living_game")
    if ext is None:
        errors.append("extensions.living_game missing")
    else:
        errors.extend(e.message for e in extension_validator.iter_errors(ext))
    return errors


def with_ext(**changes):
    env = copy.deepcopy(EXAMPLE)
    env["extensions"]["living_game"].update(changes)
    return env


class LivingGameProfileTest(unittest.TestCase):
    def test_extension_is_not_a_second_envelope(self):
        self.assertNotEqual(EXTENSION_SCHEMA["$id"], ENVELOPE_SCHEMA["$id"])
        for key in ("envelope_id", "mandate", "authority", "risk", "dispatch"):
            self.assertNotIn(key, EXTENSION_SCHEMA["properties"], f"extension must not redefine {key}")
        self.assertFalse(EXTENSION_SCHEMA["additionalProperties"])

    def test_example_envelope_conforms(self):
        self.assertEqual(validate(EXAMPLE), [])

    def test_evidence_cannot_claim_authority(self):
        env = copy.deepcopy(EXAMPLE)
        env["extensions"]["living_game"]["evidence_refs"][0]["grants_authority"] = True
        self.assertTrue(any("False" in m for m in validate(env)))

    def test_face_recognition_cannot_be_enabled(self):
        env = with_ext(privacy={"face_recognition": True, "public_broadcast_authorized": False})
        self.assertTrue(validate(env))

    def test_tap_to_spend_and_auto_transfer_invariants_are_constant(self):
        inv = copy.deepcopy(EXAMPLE["extensions"]["living_game"]["invariants"])
        inv["tap_to_spend"] = True
        self.assertTrue(validate(with_ext(invariants=inv)))
        inv = copy.deepcopy(EXAMPLE["extensions"]["living_game"]["invariants"])
        inv["automatic_ownership_transfer"] = True
        self.assertTrue(validate(with_ext(invariants=inv)))

    def test_reward_requires_rules_engine_verification(self):
        env = copy.deepcopy(EXAMPLE)
        del env["extensions"]["living_game"]["rules_engine"]
        self.assertTrue(any("rules_engine" in m for m in validate(env)))

    def test_public_broadcast_requires_lease_and_authorization(self):
        env = with_ext(
            action_class="publish.public_broadcast",
            session_ref={"session_id": "s1", "mode": "public"},
            privacy={"face_recognition": False, "public_broadcast_authorized": False},
        )
        errors = validate(env)
        self.assertTrue(any("lease_id" in m for m in errors))
        self.assertTrue(any("True" in m for m in errors))
        ok = with_ext(
            action_class="publish.public_broadcast",
            session_ref={"session_id": "s1", "mode": "public", "lease_id": "lease_1"},
            privacy={"face_recognition": False, "public_broadcast_authorized": True},
        )
        self.assertEqual(validate(ok), [])

    def test_social_publish_requires_human_signal_entity_consent(self):
        env = with_ext(action_class="publish.social")
        self.assertTrue(any("human_signal_entity" in m for m in validate(env)))

    def test_wallet_cannot_be_required_every_step(self):
        env = with_ext(accessibility={"alternatives_available": True, "wallet_required_every_step": True})
        self.assertTrue(validate(env))

    def test_envelope_without_must_understand_is_rejected(self):
        env = copy.deepcopy(EXAMPLE)
        env["must_understand"] = []
        self.assertIn("must_understand must list living_game", validate(env))

    def test_canonical_schema_ids_match_gaming_district(self):
        schema_dir = os.environ.get("LIVING_GAME_SCHEMA_DIR")
        if not schema_dir:
            self.skipTest("LIVING_GAME_SCHEMA_DIR not set")
        consts = EXTENSION_SCHEMA["properties"]["canonical_schemas"]["properties"]
        for key, rel in (("living_game_object", "schemas/living-game-object-v1.schema.json"),
                         ("live_reality_session", "schemas/live-reality-session-v1.schema.json")):
            canonical = json.loads((Path(schema_dir) / rel).read_text())
            self.assertEqual(consts[key]["const"], canonical["$id"])
        lgo = json.loads((Path(schema_dir) / "schemas/living-game-object-v1.schema.json").read_text())
        self.assertEqual(
            EXTENSION_SCHEMA["properties"]["object_refs"]["items"]["properties"]["assurance_tier"]["enum"],
            lgo["properties"]["physical"]["properties"]["assuranceTier"]["enum"],
        )
        lrs = json.loads((Path(schema_dir) / "schemas/live-reality-session-v1.schema.json").read_text())
        self.assertEqual(EXTENSION_SCHEMA["properties"]["session_ref"]["properties"]["mode"]["enum"], lrs["properties"]["mode"]["enum"])


if __name__ == "__main__":
    unittest.main()
