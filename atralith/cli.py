#!/usr/bin/env python3
"""ATRALITH-lite CLI — build and check ATG artifacts.

Usage:
    atralith build-mandate AGENT_ID ACTION_TYPE [--enforcement enforced]
    atralith sign-envelope MANDATE_JSON PAYLOAD_JSON
    atralith generate-receipt ENVELOPE_JSON RESULT_JSON
    atralith verify RECEIPT_JSON --envelope ENVELOPE_JSON --result RESULT_JSON
"""

import argparse
import json
import sys

from atralith.mandate import build_mandate
from atralith.envelope import sign_envelope
from atralith.receipt import generate_receipt, verify_receipt


def cmd_build_mandate(args):
    mandate = build_mandate(
        agent_id=args.agent_id,
        action_type=args.action_type,
        enforcement=args.enforcement,
        action_method=args.method,
        action_target=args.target,
        action_stage=args.stage,
        issued_by=args.issued_by,
    )
    print(json.dumps(mandate, indent=2))


def cmd_sign_envelope(args):
    with open(args.mandate_json) as f:
        mandate = json.load(f)
    with open(args.payload_json) as f:
        payload = json.load(f)

    envelope = sign_envelope(
        mandate=mandate,
        payload=payload,
        authorization_class=args.auth_class,
        authorizer=args.authorizer,
        signer_type=args.signer_type,
        key_residency=args.key_residency,
        display_trust=args.display_trust,
        confirmation=args.confirmation,
    )
    print(json.dumps(envelope, indent=2))


def cmd_generate_receipt(args):
    with open(args.envelope_json) as f:
        envelope = json.load(f)
    with open(args.result_json) as f:
        result = json.load(f)

    chain = None
    if args.chain:
        chain = json.loads(args.chain)

    receipt = generate_receipt(
        envelope=envelope,
        result=result,
        verification_state=args.state,
        receipt_chain=chain,
    )
    print(json.dumps(receipt, indent=2))


def cmd_verify(args):
    with open(args.receipt_json) as f:
        receipt = json.load(f)

    envelope = None
    if args.envelope_json:
        with open(args.envelope_json) as f:
            envelope = json.load(f)

    result = None
    if args.result_json:
        with open(args.result_json) as f:
            result = json.load(f)

    valid, findings = verify_receipt(receipt, envelope, result)

    if valid:
        print("CONSISTENT — receipt structure and supplied artifact hashes/claims are consistent.")
        print("NOTE — signer identity and cryptographic authorization were not verified.")
        sys.exit(0)
    else:
        print("FAILED — receipt verification failed:")
        for f_ in findings:
            print(f"  - {f_}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="ATRALITH-lite — ATG artifact CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # build-mandate
    p = sub.add_parser("build-mandate", help="Build a mandate")
    p.add_argument("agent_id")
    p.add_argument("action_type")
    p.add_argument("--enforcement", default="advisory")
    p.add_argument("--method")
    p.add_argument("--target")
    p.add_argument("--stage")
    p.add_argument("--issued-by")
    p.set_defaults(func=cmd_build_mandate)

    # sign-envelope
    p = sub.add_parser("sign-envelope", help="Build an authorization envelope")
    p.add_argument("mandate_json")
    p.add_argument("payload_json")
    p.add_argument("--auth-class", default="A1_REVERSIBLE")
    p.add_argument("--authorizer", default="agent:atralith")
    p.add_argument("--signer-type", default="software_session")
    p.add_argument("--key-residency", default="unknown")
    p.add_argument("--display-trust", default="host_rendered")
    p.add_argument("--confirmation", default="none")
    p.set_defaults(func=cmd_sign_envelope)

    # generate-receipt
    p = sub.add_parser("generate-receipt", help="Generate a receipt")
    p.add_argument("envelope_json")
    p.add_argument("result_json")
    p.add_argument("--state", default="pending_verification")
    p.add_argument("--chain")
    p.set_defaults(func=cmd_generate_receipt)

    # verify
    p = sub.add_parser("verify", help="Check a receipt against supplied evidence")
    p.add_argument("receipt_json")
    p.add_argument("--envelope", dest="envelope_json", required=True)
    p.add_argument("--result", dest="result_json", required=True)
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
