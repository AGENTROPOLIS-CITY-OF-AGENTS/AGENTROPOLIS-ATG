"""Synthetic offline envelope gate. Not a production protocol or SwaT mapper."""
import hashlib
import hmac
import json
import math
import struct
import unittest

KEY = b"public-synthetic-test-key"
MAX_BYTES = 4096
SCOPE = {"protocol": "synapse54-test-v0", "sender": "test:A",
         "receiver": "test:B", "task": "fixture", "mandate": "offline",
         "source_model": "synthetic:A:v1", "target_model": "synthetic:B:v1",
         "mapper": "synthetic:A-to-B:v1", "layout": "flat-f32le",
         "classification": "synthetic", "policy": "no-egress",
         "provenance": "generated-fixture"}
FIELDS = set(SCOPE) | {"nonce", "expiry", "shape", "length", "digest", "signature"}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sign(meta):
    unsigned = {k: v for k, v in meta.items() if k != "signature"}
    return hmac.new(KEY, canonical(unsigned), hashlib.sha256).hexdigest()

def fixture(payload, nonce="n1"):
    meta = dict(SCOPE, nonce=nonce, expiry=110, shape=[len(payload)//4],
                length=len(payload), digest=digest(payload))
    return dict(meta, signature=sign(meta))

class Gate:
    def __init__(self):
        self.seen = set()

    def inspect(self, meta, payload, now=100):
        reason = "schema"
        try:
            if type(meta) is not dict or set(meta) != FIELDS or type(payload) is not bytes:
                raise ValueError()
            if len(canonical(meta)) > 4096:
                raise ValueError()
            reason = "scope"
            if any(meta[k] != v for k, v in SCOPE.items()):
                raise ValueError()
            reason = "signature"
            if not isinstance(meta["signature"], str) or not hmac.compare_digest(sign(meta), meta["signature"]):
                raise ValueError()
            reason = "expiry"
            if type(meta["expiry"]) is not int or not now < meta["expiry"] <= now+60:
                raise ValueError()
            reason = "nonce"
            nonce = meta["nonce"]
            if type(nonce) is not str or not 1 <= len(nonce) <= 64 or nonce in self.seen:
                raise ValueError()
            reason = "size"
            shape = meta["shape"]
            if type(shape) is not list or len(shape) != 1 or type(shape[0]) is not int:
                raise ValueError()
            if type(meta["length"]) is not int or not 0 < len(payload) <= MAX_BYTES or len(payload) != meta["length"] or shape[0]*4 != len(payload):
                raise ValueError()
            reason = "digest"
            if meta["digest"] != digest(payload):
                raise ValueError()
            reason = "nonfinite"
            if not all(math.isfinite(v[0]) for v in struct.iter_unpack("<f", payload)):
                raise ValueError()
            self.seen.add(nonce)
            reason = "accepted"
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            pass
        try:
            request_digest = digest(canonical(meta)) if type(meta) is dict else None
        except (ValueError, TypeError, OverflowError, RecursionError):
            request_digest = None
        receipt = {"request_digest": request_digest,
                   "payload_digest": digest(payload) if type(payload) is bytes else None,
                   "receiver": SCOPE["receiver"], "time": now,
                   "decision": "allow" if reason == "accepted" else "deny",
                   "reason": reason, "execution_authorized": False, "fallback": False}
        return receipt

class Tests(unittest.TestCase):
    def setUp(self):
        self.p = struct.pack("<2f", 1, 2)
        self.g = Gate()

    def check(self, reason, changes=None, payload=None, resign=True):
        m = fixture(self.p)
        m.update(changes or {})
        if resign:
            m["signature"] = sign(m)
        r = self.g.inspect(m, self.p if payload is None else payload)
        self.assertEqual(r["reason"], reason)
        self.assertFalse(r["execution_authorized"])
        self.assertFalse(r["fallback"])

    def test_valid(self): self.check("accepted")
    def test_replay(self):
        self.check("accepted")
        self.check("nonce")
    def test_signature(self): self.check("signature", {"signature": "bad"}, resign=False)
    def test_expired(self): self.check("expiry", {"expiry": 100})
    def test_scope(self): self.check("scope", {"classification": "secret"})
    def test_pair(self): self.check("scope", {"target_model": "other"})
    def test_layout(self): self.check("scope", {"layout": "pickle"})
    def test_shape(self): self.check("size", {"shape": [4]})
    def test_digest(self): self.check("digest", payload=b"12345678")
    def test_missing(self):
        m = fixture(self.p)
        del m["signature"]
        self.assertEqual(self.g.inspect(m, self.p)["decision"], "deny")
    def test_large(self):
        p = bytes(MAX_BYTES+4)
        self.assertEqual(self.g.inspect(fixture(p), p)["reason"], "size")
    def test_nonfinite(self):
        p = struct.pack("<f", float("nan"))
        self.assertEqual(self.g.inspect(fixture(p), p)["reason"], "nonfinite")

if __name__ == "__main__":
    unittest.main()
