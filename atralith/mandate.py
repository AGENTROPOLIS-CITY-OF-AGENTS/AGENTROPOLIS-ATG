"""Mandate builder — produces RFC-0001-compliant ATG mandates.

Usage:
    from atralith.mandate import build_mandate

    mandate = build_mandate(
        agent_id="agent:cityflight-01",
        action_type="cityflight",
        action_stage="generation",
        scope={"max_spend_per_generation": "100.00", "max_generations_per_hour": 10},
        constraints={
            "valid_from": "2026-08-01T00:00:00Z",
            "valid_until": "2026-08-08T00:00:00Z",
        },
        enforcement="enforced",
        issued_by="principal:tony",
    )
"""

import hashlib
import json
import time
import uuid

from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts"
SCHEMA_PATH = SCHEMA_DIR / "core" / "mandate.schema.json"


def _load_schema() -> dict[str, Any]:
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _canonical_dumps(obj: dict[str, Any]) -> str:
    """Serialize a dict to a canonical (sorted-key) JSON string for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha256_hex(data: str) -> str:
    return f"sha256:{hashlib.sha256(data.encode()).hexdigest()}"


def build_mandate(
    agent_id: str,
    action_type: str,
    enforcement: str = "advisory",
    action_method: str | None = None,
    action_target: str | None = None,
    action_stage: str | None = None,
    scope: dict[str, Any] | None = None,
    constraints: dict[str, Any] | None = None,
    issued_by: str | None = None,
    mandate_id: str | None = None,
) -> dict[str, Any]:
    """Build and validate an ATG mandate.

    Args:
        agent_id: The agent authorized to act under this mandate.
        action_type: The action type (e.g., "transfer", "deploy", "cityflight").
        enforcement: "advisory" (default) or "enforced".
        action_method: Optional permitted method.
        action_target: Optional target resource.
        action_stage: Optional pipeline stage (CITYFLIGHT).
        scope: Optional scope constraints dict.
        constraints: Optional constraints dict.
        issued_by: Optional principal that issued this mandate.
        mandate_id: Optional override mandate_id (auto-generated if omitted).

    Returns:
        A validated mandate dict.
    """
    schema = _load_schema()

    action: dict[str, Any] = {"type": action_type}
    if action_method:
        action["method"] = action_method
    if action_target:
        action["target"] = action_target
    if action_stage:
        action["stage"] = action_stage

    mandate: dict[str, Any] = {
        "mandate_id": mandate_id or f"mdt_{uuid.uuid4().hex[:12]}",
        "agent_id": agent_id,
        "action": action,
        "enforcement": enforcement,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if scope:
        mandate["scope"] = scope
    else:
        mandate["scope"] = {}

    if constraints:
        mandate["constraints"] = constraints

    if issued_by:
        mandate["issued_by"] = issued_by

    # Compute mandate hash from canonical serialization
    mandate["mandate_hash"] = _sha256_hex(_canonical_dumps(mandate))

    # Validate against normative schema
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = list(validator.iter_errors(mandate))
    if errors:
        msgs = [f"{e.message} (path: {' → '.join(str(p) for p in e.path)})" for e in errors]
        raise ValueError(f"Mandate validation failed:\n" + "\n".join(msgs))

    return mandate
