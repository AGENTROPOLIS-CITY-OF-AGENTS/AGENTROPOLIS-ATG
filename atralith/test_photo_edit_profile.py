"""Negative regression tests for the identity-preserving photo edit profile.

Each test corresponds to a review finding on PR #58; each fails without the
corresponding check in atralith/photo_edit_profile.py or the media schemas.
"""

from __future__ import annotations

import hashlib
import unittest

from atralith.photo_edit_profile import (
    INTENT_MODES,
    PROFILE_VERSION,
    SUBJECT_ATTRIBUTES,
    TRANSITIONS,
    PhotoEditProfileError,
    PhotoEditRun,
    approval_digest,
    check_receipt,
    compile_request,
    derive_constraints,
    resolve_authority,
    validate_request,
)

SOURCE_BYTES = b"original-photo-bytes"
SOURCE_HASH = hashlib.sha256(SOURCE_BYTES).hexdigest()
EDITED_BYTES = b"edited-photo-bytes"
EVIDENCE = hashlib.sha256(b"verifier-evidence").hexdigest()
HUMAN = {"id": "human:alice", "type": "human"}
AUTHORITY = {
    "principal": HUMAN,
    "mandate_ref": "M-1",
    "capability_handle_ref": "CAP-1",
    "policy_ref": "POL-1",
    "execution_envelope_ref": "EE-1",
}
RESOLVED = {"M-1": "valid", "CAP-1": "valid", "POL-1": "valid", "EE-1": "valid"}
ADAPTER = "adapter:hermes-image"


def _request(**overrides):
    kwargs = {
        "request_id": "REQ-1",
        "intent": "CAMERA_UPGRADE",
        "source_asset": {"asset_id": "asset-1", "sha256": SOURCE_HASH, "media_type": "image/png"},
        "authority": AUTHORITY,
    }
    kwargs.update(overrides)
    return compile_request(**kwargs)


def _pass(applied=("exposure",), verifier="verifier:independent", **extra):
    report = {
        "result": "PASS",
        "verifier_id": verifier,
        "independence": "independent_service",
        "evidence_digest": EVIDENCE,
        "edit_applied": True,
        "applied_domains": list(applied),
    }
    report.update(extra)
    return report


def _run_to_previewed(request=None, output=EDITED_BYTES):
    run = PhotoEditRun(request or _request())
    run.analyze()
    run.lock_subject()
    run.compile_spec()
    run.resolve_authority(RESOLVED)
    run.dispatch()
    run.preview(output)
    return run


class IntentDerivedConstraintsTests(unittest.TestCase):
    """Threads: 'Camera upgrades permit unrelated edits' / 'Restrict mutable fields to the selected intent'."""

    def test_camera_upgrade_mutable_is_exactly_the_mode_allowlist(self):
        req = _request()
        self.assertEqual(req["mutable"], list(INTENT_MODES["CAMERA_UPGRADE"]["mutable"]))
        for banned in ("lighting", "contrast", "color", "framing"):
            self.assertNotIn(banned, req["mutable"])

    def test_every_intent_derives_its_own_allowlist(self):
        for intent, mode in INTENT_MODES.items():
            with self.subTest(intent=intent):
                c = derive_constraints(intent)
                self.assertEqual(c["mutable"], list(mode["mutable"]))
                self.assertIn("identity_drift", c["forbid"])
                self.assertEqual(c["preserve"], list(SUBJECT_ATTRIBUTES))

    def test_cross_mode_union_is_rejected(self):
        req = _request()
        req["mutable"] = req["mutable"] + ["color", "lighting"]
        with self.assertRaisesRegex(PhotoEditProfileError, "outside intent CAMERA_UPGRADE"):
            validate_request(req)

    def test_preserve_includes_pose_and_surroundings(self):
        """Every attribute declared immutable is in the machine-readable preserve list."""
        req = _request()
        self.assertIn("pose", req["preserve"])
        self.assertIn("surroundings", req["preserve"])
        req["preserve"] = [a for a in req["preserve"] if a != "pose"]
        with self.assertRaises(PhotoEditProfileError):
            validate_request(req)


class ExplicitSubjectChangeTests(unittest.TestCase):
    def test_human_requested_change_moves_attribute_out_of_preserve(self):
        change = {"attribute": "hair", "requested_by": HUMAN, "request_digest": EVIDENCE}
        req = _request(explicit_subject_changes=[change])
        self.assertNotIn("hair", req["preserve"])
        self.assertIn("identity", req["preserve"])

    def test_agent_requested_change_rejected(self):
        change = {"attribute": "hair", "requested_by": {"id": "agent:x", "type": "agent"}, "request_digest": EVIDENCE}
        with self.assertRaises(PhotoEditProfileError):
            _request(explicit_subject_changes=[change])

    def test_identity_can_never_be_released(self):
        for attr in ("identity", "face_geometry", "body_proportions"):
            change = {"attribute": attr, "requested_by": HUMAN, "request_digest": EVIDENCE}
            with self.subTest(attr=attr), self.assertRaises(PhotoEditProfileError):
                _request(explicit_subject_changes=[change])


class SourceAssetAndRequestIdTests(unittest.TestCase):
    """Thread: 'Reference the source asset in the request'."""

    def test_request_without_source_asset_or_request_id_rejected(self):
        req = _request()
        for field in ("source_asset", "request_id"):
            broken = dict(req)
            del broken[field]
            with self.subTest(field=field), self.assertRaises(PhotoEditProfileError):
                validate_request(broken)

    def test_source_hash_must_be_sha256(self):
        with self.assertRaises(PhotoEditProfileError):
            _request(source_asset={"asset_id": "a", "sha256": "not-a-hash"})

    def test_receipt_bound_to_requested_source_hash(self):
        run = _run_to_previewed()
        run.verify(_pass(), ADAPTER)
        run.human_decision(approved=True, approver=HUMAN)
        receipt = run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        self.assertEqual(receipt["source_asset_hash"], SOURCE_HASH)
        forged = dict(receipt, source_asset_hash=hashlib.sha256(b"other").hexdigest())
        with self.assertRaisesRegex(PhotoEditProfileError, "source_asset_hash"):
            check_receipt(run.request, forged)


class AuthorityGateTests(unittest.TestCase):
    """Threads: 'Photo edits bypass scoped authority' / 'Gate dispatch on mandate and authority checks'."""

    def test_message_requires_every_authority_reference(self):
        for field in ("principal", "mandate_ref", "capability_handle_ref", "policy_ref", "execution_envelope_ref"):
            auth = dict(AUTHORITY)
            del auth[field]
            with self.subTest(field=field), self.assertRaises(PhotoEditProfileError):
                _request(authority=auth)

    def test_dispatch_refused_without_authority_resolution(self):
        run = PhotoEditRun(_request())
        run.analyze()
        run.lock_subject()
        run.compile_spec()
        with self.assertRaisesRegex(PhotoEditProfileError, "authority not resolved"):
            run.dispatch()
        self.assertEqual(run.state, "SPEC_COMPILED")

    def test_unresolved_or_invalid_reference_blocks_dispatch(self):
        req = _request()
        for missing in RESOLVED:
            partial = {k: v for k, v in RESOLVED.items() if k != missing}
            with self.subTest(missing=missing), self.assertRaises(PhotoEditProfileError):
                resolve_authority(req, partial)
        with self.assertRaises(PhotoEditProfileError):
            resolve_authority(req, dict(RESOLVED, **{"M-1": "revoked"}))

    def test_state_machine_has_no_direct_spec_to_dispatch_edge(self):
        self.assertNotIn(("SPEC_COMPILED", "dispatch"), TRANSITIONS)
        self.assertEqual(TRANSITIONS[("SPEC_COMPILED", "resolve_authority")], "AUTHORITY_RESOLVED")


class VerifierOutcomeTests(unittest.TestCase):
    """Threads: 'Non-identity failures lack rejection paths' / 'Reject every verifier failure outcome'."""

    def test_every_fail_outcome_transitions_to_rejected(self):
        for outcome in ("FAIL_IDENTITY_DRIFT", "FAIL_UNREQUESTED_RESHAPE", "FAIL_UNREQUESTED_BEAUTIFICATION", "FAIL_OUT_OF_SCOPE_MUTATION", "FAIL_EDIT_NOT_APPLIED"):
            with self.subTest(outcome=outcome):
                run = _run_to_previewed()
                run.verify(_pass(result=outcome), ADAPTER)
                self.assertEqual(run.state, "REJECTED")
                with self.assertRaises(PhotoEditProfileError):
                    run.human_decision(approved=True, approver=HUMAN)

    def test_unknown_outcome_rejected(self):
        run = _run_to_previewed()
        with self.assertRaises(PhotoEditProfileError):
            run.verify(_pass(result="MAYBE"), ADAPTER)


class EditActuallyOccurredTests(unittest.TestCase):
    """Thread: 'Verify that the requested edit actually occurred'."""

    def test_unchanged_output_cannot_pass(self):
        run = _run_to_previewed(output=SOURCE_BYTES)
        run.verify(_pass(), ADAPTER)
        self.assertEqual(run.verification["result"], "FAIL_EDIT_NOT_APPLIED")
        self.assertEqual(run.state, "REJECTED")

    def test_pass_without_applied_domains_or_edit_flag_downgraded(self):
        for report in (_pass(applied=()), _pass(edit_applied=False)):
            with self.subTest(report=report):
                run = _run_to_previewed()
                run.verify(report, ADAPTER)
                self.assertEqual(run.verification["result"], "FAIL_EDIT_NOT_APPLIED")

    def test_applied_domain_outside_intent_is_out_of_scope(self):
        run = _run_to_previewed()
        run.verify(_pass(applied=("exposure", "color")), ADAPTER)
        self.assertEqual(run.verification["result"], "FAIL_OUT_OF_SCOPE_MUTATION")
        self.assertEqual(run.state, "REJECTED")


class IndependentVerifierTests(unittest.TestCase):
    """Thread: 'Bind PASS to independent verification evidence'."""

    def test_adapter_self_report_rejected(self):
        run = _run_to_previewed()
        with self.assertRaisesRegex(PhotoEditProfileError, "independent"):
            run.verify(_pass(verifier=ADAPTER), ADAPTER)

    def test_missing_verifier_identity_or_evidence_rejected(self):
        for bad in ({"verifier_id": ""}, {"independence": "self"}, {"evidence_digest": ""}):
            with self.subTest(bad=bad):
                run = _run_to_previewed()
                with self.assertRaises(PhotoEditProfileError):
                    run.verify(_pass(**bad), ADAPTER)

    def test_receipt_rejects_verifier_equal_to_adapter(self):
        run = _run_to_previewed()
        run.verify(_pass(), ADAPTER)
        run.human_decision(approved=True, approver=HUMAN)
        receipt = run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        forged = dict(receipt, verification=dict(receipt["verification"], verifier_id=ADAPTER))
        with self.assertRaisesRegex(PhotoEditProfileError, "self-report"):
            check_receipt(run.request, forged)


class HumanApprovalTests(unittest.TestCase):
    """Threads: 'Policy principals can replace human approval' / 'Require human proof in human-gated receipts' / 'Add a transition for human rejection'."""

    def _verified(self, **kw):
        run = _run_to_previewed(_request(**kw))
        run.verify(_pass(), ADAPTER)
        return run

    def test_policy_principal_cannot_approve_human_gated_request(self):
        run = self._verified()
        with self.assertRaisesRegex(PhotoEditProfileError, "human_approval_required"):
            run.policy_approve("svc:policy")
        with self.assertRaises(PhotoEditProfileError):
            run.human_decision(approved=True, approver={"id": "svc:policy", "type": "service"})
        self.assertEqual(run.state, "VERIFIED")

    def test_policy_principal_allowed_only_when_human_not_required(self):
        run = self._verified(human_approval_required=False)
        run.policy_approve("svc:policy")
        self.assertEqual(run.state, "APPROVED")

    def test_receipt_requires_human_principal_and_bound_digest(self):
        run = self._verified()
        run.human_decision(approved=True, approver=HUMAN)
        receipt = run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        self.assertEqual(receipt["approval"]["approved_by"], HUMAN)
        self.assertEqual(receipt["approval"]["approval_digest"], approval_digest("REQ-1", receipt["preview_digest"], "human:alice"))
        swapped = dict(receipt, approval={"approved_by": {"id": "svc:policy", "type": "policy-authorized-principal"}, "approval_digest": receipt["approval"]["approval_digest"]})
        with self.assertRaisesRegex(PhotoEditProfileError, "human principal"):
            check_receipt(run.request, swapped)
        other_preview = dict(receipt, preview_digest=hashlib.sha256(b"other-preview").hexdigest())
        with self.assertRaisesRegex(PhotoEditProfileError, "approval_digest"):
            check_receipt(run.request, other_preview)

    def test_human_rejection_after_pass_routes_to_rejected_then_retry(self):
        run = self._verified()
        run.human_decision(approved=False, approver=HUMAN)
        self.assertEqual(run.state, "REJECTED")
        run.after_rejection()
        self.assertEqual(run.state, "RETRY_BOUNDED")
        run.dispatch()
        self.assertEqual(run.attempt, 2)


class BoundedRetryTests(unittest.TestCase):
    """Thread: 'Define an enforceable retry limit'."""

    def test_retry_budget_terminates(self):
        run = _run_to_previewed(_request(max_attempts=2))
        run.verify(_pass(result="FAIL_IDENTITY_DRIFT"), ADAPTER)
        run.after_rejection()
        self.assertEqual(run.state, "RETRY_BOUNDED")
        run.dispatch()
        run.preview(EDITED_BYTES)
        run.verify(_pass(result="FAIL_IDENTITY_DRIFT"), ADAPTER)
        run.after_rejection()
        self.assertEqual(run.state, "FAILED_TERMINAL")
        with self.assertRaises(PhotoEditProfileError):
            run.dispatch()

    def test_escalation_variant(self):
        run = _run_to_previewed(_request(max_attempts=1, on_exhausted="HUMAN_ESCALATION"))
        run.verify(_pass(result="FAIL_IDENTITY_DRIFT"), ADAPTER)
        run.after_rejection()
        self.assertEqual(run.state, "HUMAN_ESCALATION")

    def test_retry_policy_required_and_bounded(self):
        req = _request()
        del req["retry_policy"]
        with self.assertRaises(PhotoEditProfileError):
            validate_request(req)
        with self.assertRaises(PhotoEditProfileError):
            _request(max_attempts=99)

    def test_receipt_attempt_cannot_exceed_budget(self):
        run = _run_to_previewed()
        run.verify(_pass(), ADAPTER)
        run.human_decision(approved=True, approver=HUMAN)
        receipt = run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        with self.assertRaises(PhotoEditProfileError):
            check_receipt(run.request, dict(receipt, attempt=receipt["max_attempts"] + 1))


class ReceiptBeforeExportTests(unittest.TestCase):
    """Thread: 'Record the profile version in every receipt' + receipt-before-export."""

    def test_export_refused_without_committed_receipt(self):
        run = _run_to_previewed()
        run.verify(_pass(), ADAPTER)
        run.human_decision(approved=True, approver=HUMAN)
        self.assertEqual(run.state, "APPROVED")
        with self.assertRaisesRegex(PhotoEditProfileError, "no committed receipt"):
            run.export()
        self.assertNotIn(("APPROVED", "export"), TRANSITIONS)
        run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        run.export()
        self.assertEqual(run.state, "EXPORTED")

    def test_receipt_carries_profile_version(self):
        run = _run_to_previewed()
        run.verify(_pass(), ADAPTER)
        run.human_decision(approved=True, approver=HUMAN)
        receipt = run.commit_receipt(ADAPTER, "2026-09-23T00:00:00Z")
        self.assertEqual(receipt["profile_version"], PROFILE_VERSION)
        unversioned = dict(receipt)
        del unversioned["profile_version"]
        with self.assertRaises(PhotoEditProfileError):
            check_receipt(run.request, unversioned)
        with self.assertRaisesRegex(PhotoEditProfileError, "profile_version"):
            check_receipt(run.request, dict(receipt, profile_version="0.0.9"))


if __name__ == "__main__":
    unittest.main()
