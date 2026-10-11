"""Reference compiler / state machine / receipt checks for the ATG profile
``atg.media.photo_edit.identity_preserving``.

ATG transports the edit contract and the authority references. It does not
grant authority, does not run generation, and does not choose a provider.
Every prohibited path here fails closed with ``PhotoEditProfileError``.

See docs/ATG-PROFILE-IDENTITY-PRESERVING-PHOTO-EDIT.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema
from jsonschema import FormatChecker

PROFILE = "atg.media.photo_edit.identity_preserving"
PROFILE_VERSION = "0.2.0"

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts" / "media"
REQUEST_SCHEMA = "photo-edit-request.v1.schema.json"
RECEIPT_SCHEMA = "photo-edit-receipt.v1.schema.json"

DEFAULT_MAX_ATTEMPTS = 3
HARD_MAX_ATTEMPTS = 5

SUBJECT_ATTRIBUTES = (
    "identity",
    "face_geometry",
    "body_proportions",
    "expression",
    "pose",
    "hair",
    "clothing",
    "skin_texture",
    "surroundings",
)
NEVER_MUTABLE_SUBJECT_ATTRIBUTES = frozenset({"identity", "face_geometry", "body_proportions"})

BASE_FORBID = ("identity_drift", "face_reshape", "body_reshape", "beautification", "plastic_skin", "unrequested_regeneration")

INTENT_MODES: dict[str, dict[str, tuple[str, ...]]] = {
    "CAMERA_UPGRADE": {
        "mutable": ("exposure", "optical_depth", "sharpness", "lens_rendering", "background_separation"),
        "forbid": ("identity_drift", "face_reshape", "body_reshape", "beautification", "feature_regeneration"),
    },
    "LIGHTING_REPAIR": {
        "mutable": ("shadow_balance", "highlight_recovery", "dark_area_recovery", "skin_tone_rendering", "directional_light"),
        "forbid": ("beauty_filter", "artificial_glow", "skin_smoothing", "identity_drift"),
    },
    "CINEMATIC_GRADE": {
        "mutable": ("tonal_contrast", "color_grade", "atmosphere", "depth"),
        "forbid": ("fake_haze", "excessive_effects", "oversaturation", "identity_drift"),
    },
    "PROFESSIONAL_HEADSHOT": {
        "mutable": ("framing", "exposure", "soft_directional_light", "background_separation", "clarity"),
        "forbid": ("face_reshape", "plastic_skin", "exaggerated_retouching", "identity_drift"),
    },
}

VERIFIER_OUTCOMES = (
    "PASS",
    "FAIL_IDENTITY_DRIFT",
    "FAIL_UNREQUESTED_RESHAPE",
    "FAIL_UNREQUESTED_BEAUTIFICATION",
    "FAIL_OUT_OF_SCOPE_MUTATION",
    "FAIL_EDIT_NOT_APPLIED",
)
FAIL_OUTCOMES = frozenset(o for o in VERIFIER_OUTCOMES if o != "PASS")

# State machine. Every transition is (state, event) -> next_state. Anything not
# listed is refused.
TERMINAL_STATES = frozenset({"RECEIPTED", "FAILED_TERMINAL", "HUMAN_ESCALATION"})
TRANSITIONS: dict[tuple[str, str], str] = {
    ("REQUEST", "analyze"): "ANALYZED",
    ("ANALYZED", "lock_subject"): "SUBJECT_LOCKED",
    ("SUBJECT_LOCKED", "compile_spec"): "SPEC_COMPILED",
    ("SPEC_COMPILED", "resolve_authority"): "AUTHORITY_RESOLVED",
    ("AUTHORITY_RESOLVED", "dispatch"): "DISPATCHED",
    ("DISPATCHED", "preview"): "PREVIEWED",
    ("PREVIEWED", "verify_pass"): "VERIFIED",
    ("PREVIEWED", "verify_fail"): "REJECTED",
    ("VERIFIED", "human_approve"): "APPROVED",
    ("VERIFIED", "human_reject"): "REJECTED",
    ("APPROVED", "commit_receipt"): "RECEIPTED",
    ("RECEIPTED", "export"): "EXPORTED",
    ("REJECTED", "retry"): "RETRY_BOUNDED",
    ("REJECTED", "exhaust"): "RETRY_EXHAUSTED",
    ("RETRY_BOUNDED", "dispatch"): "DISPATCHED",
    ("RETRY_EXHAUSTED", "fail_terminal"): "FAILED_TERMINAL",
    ("RETRY_EXHAUSTED", "escalate"): "HUMAN_ESCALATION",
}


class PhotoEditProfileError(ValueError):
    """Fail-closed rejection of a request, transition, verification, or receipt."""


# --------------------------------------------------------------------------- #
# Schema helpers
# --------------------------------------------------------------------------- #

def _load_schema(name: str) -> dict[str, Any]:
    with open(SCHEMA_DIR / name, encoding="utf-8") as handle:
        return json.load(handle)


def _schema_findings(name: str, artifact: Any) -> list[str]:
    schema = _load_schema(name)
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema, format_checker=FormatChecker())
    return [
        f"{error.message} (path: {' -> '.join(str(p) for p in error.absolute_path) or '<root>'})"
        for error in sorted(validator.iter_errors(artifact), key=lambda e: list(e.absolute_path))
    ]


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# Compilation: mutable/preserve/forbid are derived from the intent
# --------------------------------------------------------------------------- #

def derive_constraints(intent: str, explicit_subject_changes: list[Mapping[str, Any]] | None = None) -> dict[str, list[str]]:
    if intent not in INTENT_MODES:
        raise PhotoEditProfileError(f"unknown intent: {intent}")
    changes = list(explicit_subject_changes or [])
    changed = {c["attribute"] for c in changes}
    if changed & NEVER_MUTABLE_SUBJECT_ATTRIBUTES:
        raise PhotoEditProfileError("identity, face_geometry, body_proportions can never be requested changes")
    for change in changes:
        if change.get("requested_by", {}).get("type") != "human":
            raise PhotoEditProfileError(f"subject change {change.get('attribute')} must be requested by a human")
    mode = INTENT_MODES[intent]
    preserve = [attr for attr in SUBJECT_ATTRIBUTES if attr not in changed]
    forbid = list(dict.fromkeys((*mode["forbid"], *BASE_FORBID)))
    return {"preserve": preserve, "mutable": list(mode["mutable"]), "forbid": forbid}


def compile_request(
    *,
    request_id: str,
    intent: str,
    source_asset: Mapping[str, Any],
    authority: Mapping[str, Any],
    explicit_subject_changes: list[Mapping[str, Any]] | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    on_exhausted: str = "FAILED_TERMINAL",
    human_approval_required: bool = True,
) -> dict[str, Any]:
    constraints = derive_constraints(intent, explicit_subject_changes)
    request = {
        "profile": PROFILE,
        "version": PROFILE_VERSION,
        "request_id": request_id,
        "intent": intent,
        "source_asset": dict(source_asset),
        "authority": json.loads(json.dumps(authority)),
        "subject_lock": True,
        "preserve": constraints["preserve"],
        "mutable": constraints["mutable"],
        "forbid": constraints["forbid"],
        "explicit_subject_changes": [dict(c) for c in (explicit_subject_changes or [])],
        "retry_policy": {"max_attempts": max_attempts, "on_exhausted": on_exhausted},
        "preview_required": True,
        "human_approval_required": human_approval_required,
        "receipt_required": True,
    }
    validate_request(request)
    return request


def validate_request(request: Mapping[str, Any]) -> None:
    findings = _schema_findings(REQUEST_SCHEMA, request)
    if findings:
        raise PhotoEditProfileError("request schema violation: " + "; ".join(findings))
    expected = derive_constraints(request["intent"], request.get("explicit_subject_changes"))
    if set(request["mutable"]) - set(expected["mutable"]):
        raise PhotoEditProfileError(
            f"mutable domains {sorted(set(request['mutable']) - set(expected['mutable']))} are outside intent {request['intent']}"
        )
    if set(expected["preserve"]) - set(request["preserve"]):
        raise PhotoEditProfileError("preserve must include every locked subject attribute not explicitly released by a human")
    changed = {c["attribute"] for c in request.get("explicit_subject_changes", [])}
    if changed & set(request["preserve"]):
        raise PhotoEditProfileError("an attribute cannot be both preserved and explicitly changed")
    if not set(BASE_FORBID) <= set(request["forbid"]):
        raise PhotoEditProfileError("forbid must include the base forbidden mutations")
    if request["retry_policy"]["max_attempts"] > HARD_MAX_ATTEMPTS:
        raise PhotoEditProfileError("retry budget exceeds hard maximum")


# --------------------------------------------------------------------------- #
# Authority resolution + dispatch gate
# --------------------------------------------------------------------------- #

def resolve_authority(request: Mapping[str, Any], resolved_refs: Mapping[str, str]) -> dict[str, Any]:
    """ATG-side check that every authority reference was resolved by the
    authority plane (AGENT-ENTITY / AEGIS / policy) before dispatch.

    ``resolved_refs`` is the authority plane's answer: ref -> status. Any missing
    or non-"valid" reference blocks dispatch. Possession of a syntactically valid
    message is never permission.
    """
    authority = request["authority"]
    refs = {
        "mandate_ref": authority["mandate_ref"],
        "capability_handle_ref": authority["capability_handle_ref"],
        "policy_ref": authority["policy_ref"],
        "execution_envelope_ref": authority["execution_envelope_ref"],
    }
    missing = [name for name, ref in refs.items() if resolved_refs.get(ref) != "valid"]
    if missing:
        raise PhotoEditProfileError("authority not resolved for: " + ", ".join(missing))
    return {"principal": dict(authority["principal"]), "resolved": dict(refs)}


class PhotoEditRun:
    """Deterministic state machine for one request. Enforces the authority
    gate before DISPATCHED, the bounded retry budget, the all-failures-reject
    rule, the human-rejection edge, and receipt-before-export."""

    def __init__(self, request: Mapping[str, Any]) -> None:
        validate_request(request)
        self.request = json.loads(json.dumps(request))
        self.state = "REQUEST"
        self.attempt = 0
        self.authority: dict[str, Any] | None = None
        self.preview_digest: str | None = None
        self.output_hash: str | None = None
        self.verification: dict[str, Any] | None = None
        self.approval: dict[str, Any] | None = None
        self.receipt: dict[str, Any] | None = None
        self.history: list[tuple[str, str, str]] = []

    @property
    def max_attempts(self) -> int:
        return int(self.request["retry_policy"]["max_attempts"])

    def _step(self, event: str) -> str:
        key = (self.state, event)
        if key not in TRANSITIONS:
            raise PhotoEditProfileError(f"no transition for event '{event}' from state {self.state}")
        nxt = TRANSITIONS[key]
        self.history.append((self.state, event, nxt))
        self.state = nxt
        return nxt

    def analyze(self) -> str:
        return self._step("analyze")

    def lock_subject(self) -> str:
        return self._step("lock_subject")

    def compile_spec(self) -> str:
        return self._step("compile_spec")

    def resolve_authority(self, resolved_refs: Mapping[str, str]) -> str:
        if self.state != "SPEC_COMPILED":
            raise PhotoEditProfileError(f"authority must be resolved from SPEC_COMPILED, not {self.state}")
        self.authority = resolve_authority(self.request, resolved_refs)
        return self._step("resolve_authority")

    def dispatch(self) -> str:
        if self.authority is None:
            raise PhotoEditProfileError("dispatch refused: authority not resolved")
        if self.attempt >= self.max_attempts:
            raise PhotoEditProfileError("dispatch refused: retry budget exhausted")
        self.attempt += 1
        self.preview_digest = None
        self.output_hash = None
        self.verification = None
        self.approval = None
        return self._step("dispatch")

    def preview(self, output_bytes: bytes) -> str:
        self.output_hash = sha256_hex(output_bytes)
        self.preview_digest = sha256_hex(f"{self.request['request_id']}:{self.attempt}:{self.output_hash}".encode("utf-8"))
        return self._step("preview")

    def verify(self, verification: Mapping[str, Any], adapter_id: str) -> str:
        checked = check_verification(self.request, verification, adapter_id=adapter_id, source_hash=self.request["source_asset"]["sha256"], output_hash=self.output_hash or "")
        self.verification = checked
        if checked["result"] == "PASS":
            return self._step("verify_pass")
        return self._step("verify_fail")

    def human_decision(self, *, approved: bool, approver: Mapping[str, str]) -> str:
        if self.state != "VERIFIED":
            raise PhotoEditProfileError(f"human decision only valid from VERIFIED, not {self.state}")
        if approver.get("type") != "human":
            raise PhotoEditProfileError("approval decision must come from a human principal")
        if not approved:
            return self._step("human_reject")
        self.approval = {
            "approved_by": {"id": approver["id"], "type": "human"},
            "approval_digest": approval_digest(self.request["request_id"], self.preview_digest or "", approver["id"]),
        }
        return self._step("human_approve")

    def policy_approve(self, principal_id: str) -> str:
        """Non-human approval is only valid when the request did not require a human."""
        if self.state != "VERIFIED":
            raise PhotoEditProfileError(f"approval only valid from VERIFIED, not {self.state}")
        if self.request["human_approval_required"]:
            raise PhotoEditProfileError("human_approval_required: a policy-authorized principal cannot approve")
        self.approval = {
            "approved_by": {"id": principal_id, "type": "policy-authorized-principal"},
            "approval_digest": approval_digest(self.request["request_id"], self.preview_digest or "", principal_id),
        }
        return self._step("human_approve")

    def after_rejection(self) -> str:
        if self.state != "REJECTED":
            raise PhotoEditProfileError(f"after_rejection only valid from REJECTED, not {self.state}")
        if self.attempt < self.max_attempts:
            return self._step("retry")
        self._step("exhaust")
        return self._step("escalate" if self.request["retry_policy"]["on_exhausted"] == "HUMAN_ESCALATION" else "fail_terminal")

    def commit_receipt(self, adapter_id: str, timestamp: str) -> dict[str, Any]:
        if self.state != "APPROVED":
            raise PhotoEditProfileError(f"receipt can only be committed from APPROVED, not {self.state}")
        assert self.verification is not None and self.approval is not None
        receipt = {
            "profile": PROFILE,
            "profile_version": self.request["version"],
            "request_id": self.request["request_id"],
            "source_asset_hash": self.request["source_asset"]["sha256"],
            "output_asset_hash": self.output_hash,
            "preview_digest": self.preview_digest,
            "intent": self.request["intent"],
            "subject_lock": True,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "verification": self.verification,
            "approval": self.approval,
            "adapter": adapter_id,
            "timestamp": timestamp,
        }
        check_receipt(self.request, receipt)
        self.receipt = receipt
        self._step("commit_receipt")
        return receipt

    def export(self) -> str:
        if self.receipt is None or self.state != "RECEIPTED":
            raise PhotoEditProfileError("export refused: no committed receipt")
        return self._step("export")


# --------------------------------------------------------------------------- #
# Verification + receipt checks
# --------------------------------------------------------------------------- #

def check_verification(request: Mapping[str, Any], verification: Mapping[str, Any], *, adapter_id: str, source_hash: str, output_hash: str) -> dict[str, Any]:
    """Normalise a verifier report. Independence and edit-occurred are enforced here:
    a report from the adapter itself, or a PASS on an unchanged image, is not PASS."""
    result = verification.get("result")
    if result not in VERIFIER_OUTCOMES:
        raise PhotoEditProfileError(f"unknown verifier outcome: {result}")
    verifier_id = verification.get("verifier_id")
    if not verifier_id or verifier_id == adapter_id:
        raise PhotoEditProfileError("verifier must be independent of the execution adapter")
    if verification.get("independence") not in ("independent_service", "independent_agent", "human_reviewer"):
        raise PhotoEditProfileError("verifier independence class missing")
    if not verification.get("evidence_digest"):
        raise PhotoEditProfileError("verification evidence digest missing")
    applied = list(verification.get("applied_domains", []))
    edit_applied = bool(verification.get("edit_applied", False))
    if result == "PASS":
        if not edit_applied or not applied or output_hash == source_hash:
            result = "FAIL_EDIT_NOT_APPLIED"
        elif set(applied) - set(request["mutable"]):
            result = "FAIL_OUT_OF_SCOPE_MUTATION"
    return {
        "result": result,
        "verifier_id": verifier_id,
        "independence": verification["independence"],
        "evidence_digest": verification["evidence_digest"],
        "edit_applied": edit_applied,
        "applied_domains": applied,
    }


def approval_digest(request_id: str, preview_digest: str, approver_id: str) -> str:
    return sha256_hex(f"{request_id}:{preview_digest}:{approver_id}".encode("utf-8"))


def check_receipt(request: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    findings = _schema_findings(RECEIPT_SCHEMA, receipt)
    if findings:
        raise PhotoEditProfileError("receipt schema violation: " + "; ".join(findings))
    if receipt["request_id"] != request["request_id"]:
        raise PhotoEditProfileError("receipt request_id does not match request")
    if receipt["profile_version"] != request["version"]:
        raise PhotoEditProfileError("receipt profile_version does not match request version")
    if receipt["source_asset_hash"] != request["source_asset"]["sha256"]:
        raise PhotoEditProfileError("receipt source_asset_hash is not the requested source asset")
    if receipt["intent"] != request["intent"]:
        raise PhotoEditProfileError("receipt intent does not match request")
    if receipt["attempt"] > receipt["max_attempts"] or receipt["max_attempts"] != request["retry_policy"]["max_attempts"]:
        raise PhotoEditProfileError("receipt attempt exceeds the request's retry budget")
    verification = receipt["verification"]
    if verification["result"] != "PASS":
        raise PhotoEditProfileError("receipt cannot be committed for a non-PASS verification")
    if verification["verifier_id"] == receipt["adapter"]:
        raise PhotoEditProfileError("verifier self-report: verifier_id equals adapter")
    if not verification["edit_applied"] or receipt["output_asset_hash"] == receipt["source_asset_hash"]:
        raise PhotoEditProfileError("receipt claims PASS for an output identical to the source")
    approval = receipt["approval"]
    if request["human_approval_required"] and approval["approved_by"]["type"] != "human":
        raise PhotoEditProfileError("human_approval_required: approved_by must be a human principal")
    expected = approval_digest(receipt["request_id"], receipt["preview_digest"], approval["approved_by"]["id"])
    if approval["approval_digest"] != expected:
        raise PhotoEditProfileError("approval_digest is not bound to this request, preview, and approver")
