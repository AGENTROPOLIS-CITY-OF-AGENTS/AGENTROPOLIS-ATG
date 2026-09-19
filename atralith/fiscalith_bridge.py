"""FISCALITH-aware ATRALITH / ATG bridge.

Executable integration boundary between the ATRALITH / ATG agent language and
the FISCALITH financial language.

Role split (canonical AGENTROPOLIS boundary):

- ATG carries financial meaning; it does not own financial semantics.
- FISCALITH defines financial meaning.
- AEGIS decides whether an action is allowed.
- AQUADUCT proves safely when required.
- PAYRAIL routes approved production value.
- Receipts prove what happened.

This module implements ONLY the ATG-side bridge responsibilities:

- detect a FISCALITH payload inside an ATG message;
- parse and validate it against the FISCALITH intent contract;
- compile it into a provider-neutral FISCALITH IR (Execution Envelope candidate);
- wrap that IR ready for the AEGIS authority decision plane;
- map downstream results / refusals / receipts back to ATG.

It does NOT grant authority, choose a settlement rail, hold credentials, or
execute value. Consequential compile output MUST still pass an AEGIS
authority decision before any execution.
"""

from __future__ import annotations

import copy
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema
from jsonschema import FormatChecker

CANONICAL_FISCALITH_INTENT_ID = "https://agentropolis.dev/fiscalith/financial-intent.v1.json"

_SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts" / "fiscalith"
PAY_PAYLOAD_SCHEMA = _SCHEMA_DIR / "pay-payload.v1.json"

# FISCALITH semantic families the bridge understands. Keep in sync with the
# AGENTROPOLIS-FISCALITH canonical list; ATG must not fork the set silently.
KNOWN_KINDS = frozenset({
    "PAY", "SEND", "BRIDGE", "SWAP", "UNIFIED_BALANCE", "ONRAMP", "EARN",
    "FX", "JOB", "ESCROW", "INVOICE", "REFUND", "RECONCILE", "SETTLE",
    "QUOTE", "BID", "OFFER", "PAYROLL", "ROYALTY", "SPLIT", "BUDGET",
    "TREASURY", "CREDIT", "COLLATERAL", "SUBSCRIPTION",
})

SIGNED_NUMBER_RE = re.compile(r"^[+-]?[0-9]+$")
_SCIENTIFIC_RE = re.compile(r"[eE]")

MAX_DECIMALS = 24
MAX_INTENT_FIELD_LEN = 4096

# ATG roles: ATG defines the envelope; FISCALITH defines money. The bridge must
# not silently mutate mandate / authority / envelope references.
_IMMUTABLE_ATG_KEYS = frozenset({
    "from", "to", "mandateRef", "executionEnvelopeRef", "delegationChain",
})

# Strict allow-list for the FISCALITH envelope carried inside an ATG message.
# Any unknown top-level field is a fail-closed signal: it may be an attempt to
# smuggle authority, rail selection, credentials, or policy mutation.
_ALLOWED_ENVELOPE_KEYS = frozenset({
    "kind", "action", "intent_id", "actor_ref", "mandate_ref",
    "execution_envelope_ref", "payload", "schema", "$ref", "version",
    "required_proofs", "counterparty_ref", "signature", "correlationId",
    "from", "to", "delegationChain", "mandateRef", "executionEnvelopeRef",
    "fiscalith", "fiscalith_version",
})

_HEX_SIGNATURE_RE = re.compile(r"^0x[0-9a-fA-F]{64,}$")


class FiscalithBridgeError(Exception):
    """Base error for the FISCALITH/ATG bridge. All failures are typed so the
    bridge fails closed and never emits a fabricated economic result."""


class FatalFiscalithError(FiscalithBridgeError):
    """Malformed, failed, replay, or otherwise un-compilable intent."""


class UnsupportedVersionError(FatalFiscalithError):
    """Version negotiation could not settle on a supported FISCALITH version."""


class RefusedFiscalith(ValueError):
    """A valid parse that AEGIS or policy refused. Mapped to ATG REFUSED."""


@dataclass
class Detection:
    is_fiscalith: bool
    kind: Optional[str] = None
    reason: str = ""


@dataclass
class ParseResult:
    raw: dict[str, Any]
    kind: str
    payload: dict[str, Any]
    atg_context: dict[str, Any]


@dataclass
class ValidationOutcome:
    valid: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class FiscalithIR:
    """Provider-neutral compiled intent, ready for an AEGIS decision.

    All money is integer/fixed-unit. Human-readable decimal strings are
    presentation only and never canonical.
    """

    intent_id: str
    kind: str
    actor_ref: str
    counterparty_ref: Optional[str]
    mandate_ref: str
    execution_envelope_ref: Optional[str]
    asset: str
    amount_minor: int
    decimals: int
    sponsor_gas: bool
    finality: str
    expiry: Optional[str]
    required_proofs: list[str]
    constraints: dict[str, Any]
    atg_context: dict[str, Any]
    compiled_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "kind": self.kind,
            "actor_ref": self.actor_ref,
            "counterparty_ref": self.counterparty_ref,
            "mandate_ref": self.mandate_ref,
            "execution_envelope_ref": self.execution_envelope_ref,
            "asset": self.asset,
            "amount_minor": self.amount_minor,
            "decimals": self.decimals,
            "sponsor_gas": self.sponsor_gas,
            "finality": self.finality,
            "expiry": self.expiry,
            "required_proofs": list(self.required_proofs),
            "constraints": copy.deepcopy(self.constraints),
            "atg_context": copy.deepcopy(self.atg_context),
            "compiled_at": self.compiled_at,
        }


class _JsonValidator:
    def __init__(self) -> None:
        self._schema: dict[str, Any] = _load_json(PAY_PAYLOAD_SCHEMA)
        jsonschema.validators.validator_for(self._schema).check_schema(self._schema)
        self._validator = jsonschema.Draft202012Validator(
            self._schema, format_checker=FormatChecker()
        )

    def validate_payload(self, payload: dict[str, Any]) -> ValidationOutcome:
        errors: list[str] = []
        for err in self._validator.iter_errors(payload):
            path = ".".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"{path}: {err.message}")
        return ValidationOutcome(valid=not errors, errors=errors)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class FiscalithBridge:
    """Compile ATG-carried financial intent into a FISCALITH IR.

    Fail-closed: any malformed, unparseable, unsupported, or replay intent is
    rejected with a typed error. No fabricated economic evidence is emitted.
    """

    MAX_DECIMALS = MAX_DECIMALS

    def __init__(
        self,
        *,
        supported_versions: Optional[set[str]] = None,
        clock: Optional[Any] = None,
        replay_guard: Optional[Any] = None,
    ) -> None:
        self.supported_versions = set(supported_versions or {"1.0"})
        self._clock = clock or _utc_now
        self._validator = _JsonValidator()
        self._replay = replay_guard or _InMemoryReplayGuard()

    # ------------------------------------------------------------------ #
    # 1. FINANCIAL PAYLOAD DETECTOR
    # ------------------------------------------------------------------ #
    def detect(self, message: Any) -> Detection:
        """Detect whether an ATG message carries a FISCALITH payload.

        Detection is a three-way test:
        a) an explicit financial payload envelope marker, OR
        b) an explicit ``kind`` known to FISCALITH, OR
        c) a negotiation payload carrying a FISCALITH schema reference.
        """
        if not isinstance(message, dict):
            return Detection(False, reason="not-an-object")
        payload = message.get("payload")
        if isinstance(payload, dict):
            kind = payload.get("kind")
            if isinstance(kind, str) and kind.upper() in KNOWN_KINDS:
                return Detection(True, kind=kind.upper(), reason="payload-kind")
        if isinstance(payload, dict) and payload.get("fiscalith"):
            return Detection(True, reason="fiscalith-marker")
        if isinstance(payload, dict):
            # Version negotiation envelope
            schema_ref = payload.get("schema") or payload.get("$ref")
            if (
                isinstance(schema_ref, str)
                and "fiscalith" in schema_ref.lower()
            ):
                return Detection(True, reason="fiscalith-schema-ref")
        return Detection(False, reason="no-financial-payload")

    # ------------------------------------------------------------------ #
    # 4. FISCALITH PARSER
    # ------------------------------------------------------------------ #
    def parse(self, message: Any) -> ParseResult:
        detection = self.detect(message)
        if not detection.is_fiscalith:
            raise FatalFiscalithError(f"not a FISCALITH payload: {detection.reason}")
        if not isinstance(message, dict):
            raise FatalFiscalithError("ATG message must be an object")

        # Normalize a top-level FISCALITH payload vs. nesting under .payload.
        if isinstance(message.get("payload"), dict):
            envelope = message
            fiscal = message["payload"]
        else:
            envelope = {}
            fiscal = message

        if not isinstance(fiscal, dict):
            raise FatalFiscalithError("FISCALITH payload must be an object")

        kind_raw = fiscal.get("kind") or fiscal.get("action")
        if not isinstance(kind_raw, str):
            raise FatalFiscalithError("FISCALITH kind/action missing")
        kind = kind_raw.upper()
        if kind not in KNOWN_KINDS:
            raise FatalFiscalithError(f"unsupported FISCALITH kind: {kind}")

        atg_context: dict[str, Any] = {}
        for key in ("from", "to", "mandateRef", "executionEnvelopeRef", "delegationChain", "correlationId"):
            if envelope.get(key) is not None:
                atg_context[key] = envelope[key]

        sub = fiscal.get("payload")
        if not isinstance(sub, dict):
            sub = fiscal
        return ParseResult(raw=fiscal, kind=kind, payload=sub, atg_context=atg_context)

    # ------------------------------------------------------------------ #
    # 5. FISCALITH VALIDATOR
    # ------------------------------------------------------------------ #
    def validate(self, parsed: ParseResult) -> ValidationOutcome:
        errors: list[str] = []

        # a) Strict envelope allow-list: unknown top-level fields fail closed.
        for key in parsed.raw:
            if key not in _ALLOWED_ENVELOPE_KEYS:
                errors.append(f"forbidden envelope field: {key}")

        # b) Plan-level security/orchestration checks (fail closed).
        for key, value in parsed.raw.items():
            if isinstance(value, str) and len(value) > MAX_INTENT_FIELD_LEN:
                errors.append(f"{key}: field exceeds max length")

        # Reject attempts to smuggle authority / rail / credential semantics.
        for banned in ("rail", "provider", "signingKey", "privateKey", "secret", "token"):
            if parsed.raw.get(banned) is not None or parsed.payload.get(banned) is not None:
                errors.append(f"forbidden authority/credential field: {banned}")

        # Malformed SignedIntent: a signature, if present, must be a well-formed
        # hex digest. Anything else fails closed.
        sig = parsed.raw.get("signature")
        if sig is not None:
            if not isinstance(sig, str) or _HEX_SIGNATURE_RE.fullmatch(sig) is None:
                errors.append("signature: malformed SignedIntent signature")

        # c) Validate typed payload (PAY and SEND share the money payload shape;
        #    other intents carry a payload or are quote/negotiation shaped).
        if parsed.kind in ("PAY", "SEND"):
            result = self._validator.validate_payload(parsed.payload)
            errors.extend(result.errors)
            if result.valid:
                errors.extend(self._money_checks(parsed.payload))
        elif parsed.kind in ("QUOTE", "BID", "OFFER"):
            # Negotiation intents may be partial; still must not carry floats.
            for key in ("amount", "max_fee_minor", "expected_total_minor"):
                if key in parsed.payload:
                    errors.extend(_integer_field_errors(key, parsed.payload[key]))
        else:
            # Other kinds: no typed validator yet, but enforce generic money
            # discipline on any numeric money field present.
            for key in ("amount", "amount_minor", "decimals", "max_fee_minor"):
                if key in parsed.payload:
                    errors.extend(_integer_field_errors(key, parsed.payload[key]))

        return ValidationOutcome(valid=not errors, errors=errors)

    def _money_checks(self, p: dict[str, Any]) -> list[str]:
        errors: list[str] = []

        amount = p.get("amount")
        decimals = p.get("decimals")
        if not isinstance(amount, int) or isinstance(amount, bool):
            errors.append("amount: must be an integer (no float money)")
        if not isinstance(decimals, int) or isinstance(decimals, bool):
            errors.append("decimals: must be an integer")
        else:
            if not (0 <= decimals <= self.MAX_DECIMALS):
                errors.append(f"decimals: out of range 0..{self.MAX_DECIMALS}")
            if isinstance(amount, int) and not isinstance(amount, bool):
                # excess precision: absolute amount must fit within scale bounds
                limit = 10 ** decimals
                if decimals > 0 and abs(amount) >= limit * (10 ** 30):
                    errors.append("amount: excess precision for scale")

        if p.get("counterparty") in (None, ""):
            errors.append("counterparty: required")

        expiry = p.get("expiry")
        if expiry is not None:
            try:
                dt = _parse_datetime(expiry)
                if dt <= self._clock():
                    errors.append("expiry: intent is expired")
            except ValueError:
                errors.append("expiry: invalid date-time")

        fee = p.get("fee_constraints") or {}
        if fee.get("max_fee_minor") is not None:
            errors.extend(_integer_field_errors("fee_constraints.max_fee_minor", fee["max_fee_minor"]))
        recon = p.get("reconciliation") or {}
        if recon.get("expected_principal_minor") is not None:
            errors.extend(
                _integer_field_errors("reconciliation.expected_principal_minor", recon["expected_principal_minor"])
            )
        if recon.get("expected_total_minor") is not None:
            errors.extend(_integer_field_errors("reconciliation.expected_total_minor", recon["expected_total_minor"]))

        # Exact reconciliation: principal + fee == total when all present.
        exp_p = recon.get("expected_principal_minor")
        exp_t = recon.get("expected_total_minor")
        max_fee = fee.get("max_fee_minor")
        if exp_p is not None and exp_t is not None and max_fee is not None:
            if exp_p + max_fee != exp_t:
                errors.append("reconciliation: principal + max_fee != expected_total")
        elif exp_p is not None and exp_t is not None:
            # No fee declared: total must equal principal (no hidden fee).
            if exp_p != exp_t:
                errors.append("reconciliation: principal != expected_total (no fee declared)")

        return errors

    # ------------------------------------------------------------------ #
    # 6. FISCALITH IR / COMPILER
    # ------------------------------------------------------------------ #
    def compile(self, parsed: ParseResult) -> FiscalithIR:
        outcome = self.validate(parsed)
        if not outcome.valid:
            raise FatalFiscalithError("; ".join(outcome.errors))

        p = parsed.payload
        amount = int(p["amount"])
        decimals = int(p["decimals"])
        actor_ref = parsed.raw.get("actor_ref") or parsed.atg_context.get("from")
        mandate_ref = parsed.raw.get("mandate_ref") or parsed.atg_context.get("mandateRef")
        envelope_ref = parsed.raw.get("execution_envelope_ref") or parsed.atg_context.get("executionEnvelopeRef")
        counterparty = p.get("counterparty")

        if not actor_ref or not isinstance(actor_ref, str):
            raise FatalFiscalithError("actor_ref is required")
        if not mandate_ref or not isinstance(mandate_ref, str):
            raise FatalFiscalithError("mandate_ref is required (authority binding)")

        intent_id = str(parsed.raw.get("intent_id") or f"FISCALITH-{uuid.uuid4().hex}")
        now = self._clock()
        if not self._replay.is_new(parsed.kind, intent_id, mandate_ref, now):
            raise FatalFiscalithError("replay: intent_id already seen")

        expiry = p.get("expiry")
        finality = p.get("finality", "best_effort")
        required_proofs = list(p.get("required_proofs") or [])
        sponsor_gas = bool(p.get("sponsor_gas", False))

        constraints: dict[str, Any] = {}
        if p.get("fee_constraints") is not None:
            constraints["fee"] = copy.deepcopy(p["fee_constraints"])
        if p.get("budget_constraints") is not None:
            constraints["budget"] = copy.deepcopy(p["budget_constraints"])
        if p.get("reconciliation") is not None:
            constraints["reconciliation"] = copy.deepcopy(p["reconciliation"])

        return FiscalithIR(
            intent_id=intent_id,
            kind=parsed.kind,
            actor_ref=actor_ref,
            counterparty_ref=counterparty,
            mandate_ref=mandate_ref,
            execution_envelope_ref=envelope_ref,
            asset=p["asset"],
            amount_minor=amount,
            decimals=decimals,
            sponsor_gas=sponsor_gas,
            finality=finality,
            expiry=expiry,
            required_proofs=required_proofs,
            constraints=constraints,
            atg_context=copy.deepcopy(parsed.atg_context),
        )

    # ------------------------------------------------------------------ #
    # 2. ATG WRAPPER (Execution Envelope candidate for AEGIS)
    # ------------------------------------------------------------------ #
    def wrap_for_aegis(self, ir: FiscalithIR) -> dict[str, Any]:
        """Produce the object handed to the AEGIS authority decision plane.

        This is a candidate, NOT authority. AEGIS decides allow/deny. The
        bridge never marks a decision as granted by itself.
        """
        return {
            "schema": "agentropolis.fiscalith.ir.v1",
            "canonical_fiscalith_intent": CANONICAL_FISCALITH_INTENT_ID,
            "intent": ir.to_dict(),
            "needs": ["ProofOfAuthority", "ProofOfControl"],
            "decision_plane": "aegis:required",
            "compiled_by": "atg.fiscalith-bridge",
        }

    # ------------------------------------------------------------------ #
    # 7. RESPONSE / REFUSAL / RECEIPT MAPPERS
    # ------------------------------------------------------------------ #
    def map_result(self, ir: FiscalithIR, *, provider_ref: str, provider_result: Any) -> dict[str, Any]:
        """Normalize a provider execution result into a FISCALITH result
        object that the ATG layer can render as an ATG.RECEIPT."""
        outcome = str(provider_result.get("outcome") if isinstance(provider_result, dict) else "ok")
        return {
            "schema": "agentropolis.fiscalith.result.v1",
            "intent_id": ir.intent_id,
            "kind": ir.kind,
            "outcome": outcome,
            "provider_ref": provider_ref,  # opaque; never an authority claim
            "amount_minor": ir.amount_minor,
            "decimals": ir.decimals,
            "asset": ir.asset,
            "provider_result": copy.deepcopy(provider_result) if isinstance(provider_result, dict) else {"detail": str(provider_result)},
        }

    def map_refusal(self, ir: Optional[FiscalithIR], *, reason: str, code: str = "REFUSED") -> dict[str, Any]:
        return {
            "schema": "agentropolis.atg.refusal.v1",
            "intent_id": ir.intent_id if ir else None,
            "code": code,
            "reason": reason,
            "denied": True,
        }

    def map_receipt(self, *, ir: FiscalithIR, result: dict[str, Any], signatures: Optional[list[str]] = None) -> dict[str, Any]:
        """Build an ATG.RECEIPT that references FISCALITH result state.

        Receipts prove what happened. Never fabricate economic evidence here:
        the caller must pass verified result state from AEGIS/AQUADUCT and the
        approved execution plane.
        """
        if result.get("outcome") != "settled":
            raise FiscalithBridgeError("cannot mint a settlement receipt for an unsettled result")
        return {
            "schema": "agentropolis.atg.receipt.v1",
            "intent_id": ir.intent_id,
            "kind": ir.kind,
            "mandate_ref": ir.mandate_ref,
            "execution_envelope_ref": ir.execution_envelope_ref,
            "asset": ir.asset,
            "amount_minor": ir.amount_minor,
            "decimals": ir.decimals,
            "sponsor_gas": ir.sponsor_gas,
            "result": copy.deepcopy(result),
            "settled": True,
            "signatures": list(signatures or []),
            "receipted_at": _utc_now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    # 8. VERSION NEGOTIATION
    # ------------------------------------------------------------------ #
    def negotiate_version(self, requested: Any) -> str:
        if isinstance(requested, dict):
            requested = requested.get("fiscalith_version") or requested.get("version")
        if requested is None:
            requested = "1.0"
        if not isinstance(requested, str):
            raise UnsupportedVersionError("version must be a string")
        requested = requested.strip()
        if requested in self.supported_versions:
            return requested
        raise UnsupportedVersionError(
            f"unsupported FISCALITH version {requested!r}; supported: {sorted(self.supported_versions)}"
        )

    # ------------------------------------------------------------------ #
    # 9. COMPATIBILITY MIGRATION LAYER
    # ------------------------------------------------------------------ #
    MIGRATIONS = {
        # Legacy placeholders -> canonical FISCALITH field names.
        "agentity_entity_ref": "actor_ref",
        "agentity_ref": "actor_ref",
        "entity": "actor_ref",
        "amountDecimal": "amount",       # legacy float string -> parsed below
        "counter_party": "counterparty",
        "gas_sponsored": "sponsor_gas",
    }

    def migrate_legacy_payload(self, raw: Any) -> Any:
        """Best-effort, fail-closed migration of legacy ATG economic payloads
        to the current FISCALITH payload shape. Unknown legacy shapes raise
        rather than silently compiling to a wrong intent."""
        if not isinstance(raw, dict):
            raise FatalFiscalithError("legacy payload must be an object")
        migrated: dict[str, Any] = {}
        for key, value in raw.items():
            canonical = self.MIGRATIONS.get(key, key)
            if isinstance(value, dict):
                migrated[canonical] = self.migrate_legacy_payload(value)
            else:
                migrated[canonical] = value
        # Legacy float-string amounts ("4.20") -> integer minor + scale.
        amount_raw = migrated.get("amount")
        if isinstance(amount_raw, str) and _SCIENTIFIC_RE.search(amount_raw) is not None:
            raise FatalFiscalithError("amount: scientific notation is forbidden")
        if isinstance(amount_raw, str) and _is_numeric_decimal(amount_raw):
            try:
                amount_minor, dec = _decimal_string_to_minor(amount_raw)
                migrated["amount"] = amount_minor
                migrated["decimals"] = dec
            except ValueError as exc:
                raise FatalFiscalithError(str(exc)) from exc
        return migrated


# ---------------------------------------------------------------------- #
# helpers
# ---------------------------------------------------------------------- #
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_numeric_decimal(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", value))


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _integer_field_errors(where: str, value: Any) -> list[str]:
    if isinstance(value, bool):
        return [f"{where}: bool is not a valid money value"]
    if isinstance(value, float):
        return [f"{where}: float money is forbidden (use integer minor units)"]
    if isinstance(value, int):
        return []
    if isinstance(value, str):
        if _SCIENTIFIC_RE.search(value):
            return [f"{where}: scientific notation is forbidden"]
        if SIGNED_NUMBER_RE.fullmatch(value):
            return []
        return [f"{where}: malformed numeric string"]
    return [f"{where}: not an integer monetary value"]


def _decimal_string_to_minor(value: str) -> tuple[int, int]:
    """Convert a decimal string like '4.20' to (minor_int, decimals).

    The stated scale is preserved: '4.20' -> (420, 2), '4.2' -> (42, 1).
    Trailing zeros are NOT stripped so the explicit decimal scale survives.
    """
    sign = -1 if value.startswith("-") else 1
    unsigned = value.lstrip("+-")
    if "." in unsigned:
        whole, frac = unsigned.split(".", 1)
        if not frac:
            frac = "0"
        decimals = len(frac)
    else:
        whole, frac = unsigned, ""
        decimals = 0
    if not whole:
        whole = "0"
    whole = whole.lstrip("0") or "0"
    if decimals > MAX_DECIMALS:
        raise FatalFiscalithError(f"excess precision: {decimals} > {MAX_DECIMALS}")
    minor = int(whole + frac)
    return sign * minor, decimals


# ---------------------------------------------------------------------- #
# Replay guard
# ---------------------------------------------------------------------- #
class ReplayGuard:
    def is_new(self, kind: str, intent_id: str, mandate_ref: str, now: datetime) -> bool:
        raise NotImplementedError


class _InMemoryReplayGuard(ReplayGuard):
    def __init__(self) -> None:
        self._seen: set[tuple[str, str, str]] = set()

    def is_new(self, kind: str, intent_id: str, mandate_ref: str, now: datetime) -> bool:
        key = (kind, intent_id, mandate_ref)
        if key in self._seen:
            return False
        self._seen.add(key)
        return True