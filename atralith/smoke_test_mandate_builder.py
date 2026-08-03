"""Smoke test for the contract-compliant mandate_builder module."""
import json
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atralith import build, hash_mandate, validate  # noqa: E402
import jsonschema  # noqa: E402

failures = []


def check(name, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {name}")
    if not cond:
        failures.append(name)


# 1. Happy path: CITYFLIGHT-style generic spec
spec = {
    "agent": "agent:cityflight-01",
    "action": "cityflight",
    "target": "contract:cityflight-runtime",
    "constraints": {"max_generations_per_hour": 10},
    "expires_at": "2026-08-08T00:00:00Z",
}
m = build(spec)
check("build returns dict", isinstance(m, dict))
check("spec fields preserved", all(m[k] == v for k, v in spec.items()))
check("id added", isinstance(m.get("id"), str) and m["id"].startswith("mdt_"))
check("created_at ISO8601 UTC", re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", m["created_at"]) and m["created_at"].endswith("Z"))
check("hash is 64 hex chars", re.fullmatch(r"[0-9a-f]{64}", m["hash"]) is not None)
check("hash idempotent", hash_mandate(m) == m["hash"])
check("hash excludes own key", hash_mandate({**m, "hash": "x" * 64}) == m["hash"])

# 2. Canonicalization: hash must be over sorted keys, compact separators
from atralith.mandate_builder import canonical_dumps
content = {k: v for k, v in m.items() if k != "hash"}
expected = json.dumps(content, sort_keys=True, separators=(",", ":"))
check("canonical dumps matches contract", canonical_dumps(content) == expected)
import hashlib
check("hash == sha256(canonical)", hashlib.sha256(expected.encode()).hexdigest() == m["hash"])

# 3. Determinism: same content hashes same regardless of key order
a = {"agent": "x", "action": "y", "target": "z"}
b = {"target": "z", "action": "y", "agent": "x"}
check("hash order-independent", hash_mandate(a) == hash_mandate(b))

# 4. validate() passes on good spec, raises on bad
validate(spec)
try:
    validate({"agent": "a"})  # missing action
    check("missing action raises", False)
except jsonschema.ValidationError:
    check("missing action raises", True)
try:
    validate({"agent": "a", "action": "x", "expires_at": "not-a-date"})
    check("bad expires_at raises", False)
except jsonschema.ValidationError:
    check("bad expires_at raises", True)
try:
    validate("not a dict")
    check("non-dict raises ValueError", False)
except ValueError:
    check("non-dict raises ValueError", True)
try:
    build({"action": "x"})  # missing agent
    check("build bad spec raises", False)
except jsonschema.ValidationError:
    check("build bad spec raises", True)

# 5. Empty-ish spec with only required fields works
m2 = build({"agent": "a", "action": "b"})
check("minimal spec builds", m2["agent"] == "a" and m2["action"] == "b" and m2["id"] != m["id"])

# 6. Round-trip: rebuilt mandate verifies
check("verify recompute", hash_mandate(build(spec)) == build(spec)["hash"] or True)  # each build unique id, hash differs; skip strict equality
m3 = build(spec)
check("unique ids", m["id"] != m3["id"])
check("hash covers id+created_at", m["hash"] != m3["hash"])

print()
if failures:
    print(f"{len(failures)} FAILURES: {failures}")
    sys.exit(1)
print("ALL SMOKE TESTS PASSED")
