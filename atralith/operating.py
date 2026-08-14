"""ATRALITH RFC-0004 operating contracts runtime.

Fail-closed helpers for Goal Contracts, Work Items, Brand Packs, Autonomy
Policies, and Capability Handles. This module never resolves raw credentials
or grants authority: authorization remains governed by RFC-0001 envelopes.
"""

from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import jsonschema
from jsonschema import FormatChecker

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "contracts" / "core"
SCHEMA_FILES = {
    "goal": "goal-contract.schema.json",
    "work": "work-item.schema.json",
    "brand": "brand-pack.schema.json",
    "autonomy": "autonomy-policy.schema.json",
    "capability": "capability-handle.schema.json",
}

AUTH_CLASS_RANK = {
    "A0_OBSERVE": 0,
    "A1_REVERSIBLE": 1,
    "A2_BOUNDED": 2,
    "A3_IRREVERSIBLE": 3,
    "A4_ROOT": 4,
}

THIRD_PARTY_ACTIONS = {
    "message", "publish", "modify", "purchase", "transfer", "sign", "delete", "admin"
}


def _load_schema(kind: str) -> dict[str, Any]:
    try:
        filename = SCHEMA_FILES[kind]
    except KeyError as exc:
        raise ValueError(f"Unknown RFC-0004 artifact kind: {kind}") from exc
    with open(SCHEMA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _format_path(error: jsonschema.ValidationError) -> str:
    path = " -> ".join(str(part) for part in error.absolute_path)
    return path or "<root>"


def validate_artifact(kind: str, artifact: Any) -> tuple[bool, list[str]]:
    schema = _load_schema(kind)
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema, format_checker=FormatChecker())
    findings = [
        f"{error.message} (path: {_format_path(error)})"
        for error in sorted(validator.iter_errors(artifact), key=lambda e: list(e.absolute_path))
    ]
    return (not findings, findings)


def require_valid(kind: str, artifact: Any) -> dict[str, Any]:
    valid, findings = validate_artifact(kind, artifact)
    if not valid:
        raise ValueError(f"{kind} validation failed:\n" + "\n".join(findings))
    if not isinstance(artifact, dict):
        raise ValueError(f"{kind} artifact must be an object")
    return artifact


def build_goal_contract(
    objective: str,
    definition_of_done: Iterable[str],
    success_tests: Iterable[dict[str, Any]],
    authority_profile: str,
    *,
    constraints: dict[str, Any] | None = None,
    goal_id: str | None = None,
    state: str = "draft",
) -> dict[str, Any]:
    goal = {
        "goal_id": goal_id or f"goal:{uuid.uuid4().hex[:12]}",
        "objective": objective,
        "definition_of_done": list(definition_of_done),
        "success_tests": list(success_tests),
        "constraints": constraints or {},
        "authority_profile": authority_profile,
        "state": state,
    }
    return require_valid("goal", goal)


def build_work_item(
    goal_id: str,
    title: str,
    owner: str,
    next_action: str,
    *,
    work_id: str | None = None,
    state: str = "queued",
    district: str | None = None,
    assigned_agents: Iterable[str] | None = None,
    dependencies: Iterable[str] | None = None,
    capability_requirements: Iterable[str] | None = None,
    approval_state: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "work_id": work_id or f"work:{uuid.uuid4().hex[:12]}",
        "goal_id": goal_id,
        "title": title,
        "state": state,
        "owner": owner,
        "next_action": next_action,
    }
    if district:
        item["district"] = district
    if assigned_agents:
        item["assigned_agents"] = list(assigned_agents)
    if dependencies:
        item["dependencies"] = list(dependencies)
    if capability_requirements:
        item["capability_requirements"] = list(capability_requirements)
    if approval_state:
        item["approval_state"] = approval_state
    return require_valid("work", item)


def _ensure_work_within_goal_constraints(goal: dict[str, Any], item: dict[str, Any]) -> None:
    constraints = goal.get("constraints") or {}
    allowed_districts = set(constraints.get("allowed_districts") or [])
    allowed_capabilities = set(constraints.get("allowed_capabilities") or [])

    district = item.get("district")
    if allowed_districts and district not in allowed_districts:
        raise ValueError(
            f"Work item {item['work_id']} district {district!r} is outside goal allowed_districts"
        )

    requested_capabilities = set(item.get("capability_requirements") or [])
    if allowed_capabilities and not requested_capabilities.issubset(allowed_capabilities):
        forbidden = sorted(requested_capabilities - allowed_capabilities)
        raise ValueError(
            f"Work item {item['work_id']} requests capabilities outside the goal: {forbidden}"
        )


def compile_goal(goal: dict[str, Any], work_specs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compile a validated goal into portable work objects; never execute them."""
    goal = copy.deepcopy(require_valid("goal", goal))
    if goal["state"] not in {"draft", "active", "blocked"}:
        raise ValueError(f"Goal state {goal['state']!r} cannot be compiled into new work")

    work_items: list[dict[str, Any]] = []
    for spec in work_specs:
        item = build_work_item(goal_id=goal["goal_id"], **spec)
        _ensure_work_within_goal_constraints(goal, item)
        work_items.append(item)

    if not work_items:
        raise ValueError("A goal compile must produce at least one work item")

    goal["work_item_ids"] = [item["work_id"] for item in work_items]
    goal["state"] = "active"
    require_valid("goal", goal)
    return {"goal": goal, "work_items": work_items}


def evaluate_goal_completion(
    goal: dict[str, Any], test_results: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Fail closed unless every required success test has passed."""
    require_valid("goal", goal)
    findings: list[str] = []

    for test in goal["success_tests"]:
        if test.get("required", True) is False:
            continue
        test_id = test["test_id"]
        if test_id not in test_results:
            findings.append(f"required success test missing: {test_id}")
            continue
        result = test_results[test_id]
        passed = result.get("passed") is True if isinstance(result, dict) else result is True
        if not passed:
            findings.append(f"required success test did not pass: {test_id}")

    return (not findings, findings)


def transition_goal(
    goal: dict[str, Any], target_state: str, *, test_results: dict[str, Any] | None = None
) -> dict[str, Any]:
    updated = copy.deepcopy(require_valid("goal", goal))
    if target_state == "complete":
        complete, findings = evaluate_goal_completion(updated, test_results or {})
        if not complete:
            raise ValueError("Goal completion rejected:\n" + "\n".join(findings))
    updated["state"] = target_state
    return require_valid("goal", updated)


def build_autonomy_policy(
    policy_id: str,
    level: str,
    action_classes: Iterable[str],
    required_authorization_class: str,
    *,
    human_approval_required: bool | None = None,
    reversibility_required: bool | None = None,
    third_party_impact_check: bool = True,
    receipt_required: bool = True,
    systems: Iterable[str] | None = None,
    recipients: Iterable[str] | None = None,
    max_value: float | None = None,
    currency: str | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    scope: dict[str, Any] = {"action_classes": list(action_classes)}
    if systems:
        scope["systems"] = list(systems)
    if recipients:
        scope["recipients"] = list(recipients)
    if max_value is not None:
        scope["max_value"] = max_value
    if currency:
        scope["currency"] = currency

    policy: dict[str, Any] = {
        "policy_id": policy_id,
        "level": level,
        "scope": scope,
        "required_authorization_class": required_authorization_class,
        "third_party_impact_check": third_party_impact_check,
        "receipt_required": receipt_required,
    }
    if human_approval_required is not None:
        policy["human_approval_required"] = human_approval_required
    if reversibility_required is not None:
        policy["reversibility_required"] = reversibility_required
    if expires_at:
        policy["expires_at"] = expires_at
    return require_valid("autonomy", policy)


def _parse_rfc3339(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def check_autonomy(
    policy: dict[str, Any],
    action_class: str,
    supplied_authorization_class: str,
    *,
    human_approved: bool = False,
    third_party_impact_checked: bool = False,
    now: datetime | None = None,
) -> tuple[bool, list[str]]:
    """Evaluate autonomy separately from authorization; never execute an action."""
    require_valid("autonomy", policy)
    findings: list[str] = []
    now = now or datetime.now(timezone.utc)

    if action_class not in policy["scope"]["action_classes"]:
        findings.append(f"action class is outside autonomy scope: {action_class}")

    required_auth = policy["required_authorization_class"]
    supplied_rank = AUTH_CLASS_RANK.get(supplied_authorization_class, -1)
    if supplied_rank < AUTH_CLASS_RANK[required_auth]:
        findings.append(
            f"authorization class {supplied_authorization_class!r} is below required {required_auth}"
        )

    level = policy["level"]
    if level == "L0_READ_ONLY" and action_class != "read":
        findings.append("L0_READ_ONLY permits only read actions")
    if level == "L1_DRAFT" and action_class not in {"read", "draft"}:
        findings.append("L1_DRAFT permits only read and draft actions")
    if level == "L2_HUMAN_APPROVAL" and action_class not in {"read", "draft"} and not human_approved:
        findings.append("L2_HUMAN_APPROVAL requires explicit human approval before execution")
    if policy.get("human_approval_required") is True and not human_approved:
        findings.append("autonomy policy requires human approval")

    if (
        policy.get("third_party_impact_check", True)
        and action_class in THIRD_PARTY_ACTIONS
        and not third_party_impact_checked
    ):
        findings.append("third-party impact check is required")

    if policy.get("expires_at") and now >= _parse_rfc3339(policy["expires_at"]):
        findings.append("autonomy policy is expired")

    return (not findings, findings)


def build_capability_handle(
    handle: str,
    capability: str,
    issuer: str,
    subject: str,
    scope: Iterable[str],
    *,
    state: str = "active",
    resource_constraints: Iterable[str] | None = None,
    credential_backend: str | None = None,
    secret_exportable: bool = False,
    issued_at: str | None = None,
    expires_at: str | None = None,
    policy_ref: str | None = None,
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "handle": handle,
        "capability": capability,
        "issuer": issuer,
        "subject": subject,
        "scope": list(scope),
        "state": state,
        "secret_exportable": secret_exportable,
    }
    if resource_constraints:
        artifact["resource_constraints"] = list(resource_constraints)
    if credential_backend:
        artifact["credential_backend"] = credential_backend
    if issued_at:
        artifact["issued_at"] = issued_at
    if expires_at:
        artifact["expires_at"] = expires_at
    if policy_ref:
        artifact["policy_ref"] = policy_ref
    return require_valid("capability", artifact)


def check_capability_handle(
    handle: dict[str, Any],
    *,
    required_capability: str | None = None,
    required_scope: Iterable[str] | None = None,
    now: datetime | None = None,
) -> tuple[bool, list[str]]:
    require_valid("capability", handle)
    findings: list[str] = []
    now = now or datetime.now(timezone.utc)

    if handle["state"] != "active":
        findings.append(f"capability handle is not active: {handle['state']}")
    if required_capability and handle["capability"] != required_capability:
        findings.append(
            f"capability mismatch: expected {required_capability!r}, got {handle['capability']!r}"
        )

    requested_scope = set(required_scope or [])
    available_scope = set(handle["scope"])
    if not requested_scope.issubset(available_scope):
        findings.append(f"required scope is not covered: {sorted(requested_scope - available_scope)}")

    if handle.get("expires_at") and now >= _parse_rfc3339(handle["expires_at"]):
        findings.append("capability handle is expired")

    return (not findings, findings)


def build_brand_pack(
    brand_id: str,
    version: str,
    name: str,
    visual_language: Iterable[str],
    forbidden_patterns: Iterable[str],
    *,
    voice: str | None = None,
    audience: str | None = None,
    typography: Iterable[str] | None = None,
    palette: Iterable[str] | None = None,
    logo_rules: Iterable[str] | None = None,
    artifact_templates: Iterable[str] | None = None,
    image_generation_rules: Iterable[str] | None = None,
    accessibility_rules: Iterable[str] | None = None,
    provenance_refs: Iterable[str] | None = None,
) -> dict[str, Any]:
    identity: dict[str, Any] = {"name": name}
    if voice:
        identity["voice"] = voice
    if audience:
        identity["audience"] = audience

    pack: dict[str, Any] = {
        "brand_id": brand_id,
        "version": version,
        "identity": identity,
        "visual_language": list(visual_language),
        "forbidden_patterns": list(forbidden_patterns),
    }
    optional_lists = {
        "typography": typography,
        "palette": palette,
        "logo_rules": logo_rules,
        "artifact_templates": artifact_templates,
        "image_generation_rules": image_generation_rules,
        "accessibility_rules": accessibility_rules,
        "provenance_refs": provenance_refs,
    }
    for key, value in optional_lists.items():
        if value:
            pack[key] = list(value)
    return require_valid("brand", pack)


def build_goal_bundle(
    objective: str,
    definition_of_done: Iterable[str],
    success_tests: Iterable[dict[str, Any]],
    authority_profile: str,
    *,
    owner: str,
    district: str | None = None,
    capability_requirements: Iterable[str] | None = None,
    constraints: dict[str, Any] | None = None,
    work_titles: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Convenience entry point for a HERMES `/goal` adapter."""
    goal = build_goal_contract(
        objective,
        definition_of_done,
        success_tests,
        authority_profile,
        constraints=constraints,
    )
    titles = list(work_titles or [objective])
    specs = [
        {
            "title": title,
            "owner": owner,
            "next_action": f"Plan and execute bounded work for: {title}",
            "district": district,
            "capability_requirements": list(capability_requirements or []),
        }
        for title in titles
    ]
    return compile_goal(goal, specs)
