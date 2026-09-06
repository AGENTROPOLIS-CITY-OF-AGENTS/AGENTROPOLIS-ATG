"""MCP surface tests: the twelve contracts, over the JSON-RPC skeleton."""

from __future__ import annotations

import io
import json

import pytest
from atg_mcp import TOOL_NAMES, AtgMcpServer, call_tool

EXPECTED_TOOLS = [
    "atg.parse",
    "atg.normalize",
    "atg.context.resolve",
    "atg.translate.human",
    "atg.translate.domain",
    "atg.translate.code",
    "atg.localize",
    "atg.validate",
    "atg.roundtrip",
    "atg.explain_mapping",
    "atg.pack.resolve",
    "atg.provenance",
]


def test_all_twelve_contracts_are_exposed():
    assert TOOL_NAMES == EXPECTED_TOOLS


def test_tools_list_returns_json_schemas():
    response = AtgMcpServer().handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = response["result"]["tools"]
    assert [tool["name"] for tool in tools] == EXPECTED_TOOLS
    for tool in tools:
        assert tool["inputSchema"]["type"] == "object"
        assert tool["description"]


def test_stdio_roundtrip_of_a_tool_call():
    server = AtgMcpServer()
    request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "atg.parse",
            "arguments": {
                "content": "Take the lift to the flat.",
                "representation": {"kind": "human_text", "name": "natural_language", "version": "1"},
                "context": {"locale": "en-GB", "industry": "TECH"},
            },
        },
    }
    stdout = io.StringIO()
    server.serve(io.StringIO(json.dumps(request) + "\n"), stdout)
    payload = json.loads(stdout.getvalue())["result"]["structuredContent"]
    assert payload["envelope"]["atg_version"]
    assert {"common.building.elevator", "common.building.apartment"} <= {
        entity["concept"] for entity in payload["envelope"]["entities"]
    }


def test_unknown_tool_is_rejected():
    response = AtgMcpServer().handle(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "atg.nope"}}
    )
    assert response["error"]["code"] == -32601
    with pytest.raises(KeyError):
        call_tool("atg.nope", {})


def test_pack_resolve_and_provenance_are_linked_by_message_id():
    packs = call_tool("atg.pack.resolve", {"context": {"industry": "FILM", "locale": "en-US"}})
    assert "FILM" in [pack["pack_id"] for pack in packs["packs"]]
    assert all(pack["version"] for pack in packs["packs"])

    parsed = call_tool(
        "atg.parse",
        {
            "content": "The first assistant director issued the call sheet for principal photography.",
            "representation": {"kind": "human_text", "name": "natural_language", "version": "1"},
            "context": {"locale": "en-US", "industry": "FILM", "region": "US"},
        },
    )
    message_id = parsed["envelope"]["message_id"]
    record = call_tool("atg.provenance", {"message_id": message_id})
    assert record["found"] is True
    assert record["pack_versions"]
    assert record["transformations"]


def test_translate_code_over_mcp_reports_loss():
    parsed = call_tool(
        "atg.parse",
        {
            "content": "CREATE TABLE t (id SERIAL PRIMARY KEY, payload JSONB NOT NULL);",
            "representation": {"kind": "code", "name": "sql", "version": "2016", "dialect": "postgresql"},
            "context": {"programming_language": "sql", "programming_dialect": "postgresql"},
        },
    )
    translated = call_tool(
        "atg.translate.code",
        {
            "envelope": parsed["envelope"],
            "target": {"kind": "code", "name": "sql", "version": "3", "dialect": "sqlite"},
        },
    )
    assert translated["lossy"] is True
    assert translated["envelope"]["requires_escalation"] is True


def test_explain_mapping_exposes_rule_ids():
    explanation = call_tool(
        "atg.explain_mapping",
        {"construct": "json_storage", "source_dialect": "postgresql", "target_dialect": "sqlite"},
    )
    assert explanation["rule_id"] == "sql.pg_sqlite.jsonb"
    assert explanation["equivalence"] == "none"
