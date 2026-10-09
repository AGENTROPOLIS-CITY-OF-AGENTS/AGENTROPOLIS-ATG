"""Contract smoke tests without third-party dependencies; run: python3 -m unittest discover -s tests -p 'test_browser_fleet_contract.py'"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "contracts/profiles/browser-fleet-action-v1.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/browser-fleet-readonly.example.json").read_text())

class BrowserFleetContractTests(unittest.TestCase):
    def test_critical_requirements(self):
        self.assertEqual(SCHEMA["additionalProperties"], False)
        self.assertEqual(SCHEMA["properties"]["sandbox"]["properties"]["whole_process"]["const"], True)
        self.assertEqual(SCHEMA["properties"]["adapter"]["properties"]["profile_type"]["const"], "ephemeral-agent")
        for required in ("mandate_ref", "authorization", "sandbox", "receipt", "principal_ref"):
            self.assertIn(required, SCHEMA["required"])
    def test_example(self):
        self.assertEqual(EXAMPLE["profile"], SCHEMA["properties"]["profile"]["const"])
        self.assertEqual(EXAMPLE["adapter"]["profile_type"], "ephemeral-agent")
        self.assertTrue(EXAMPLE["sandbox"]["whole_process"])
        self.assertTrue(EXAMPLE["receipt"]["required"])
        self.assertNotIn("private_key", json.dumps(EXAMPLE))

if __name__ == "__main__":
    unittest.main()
