"""MCP server skeleton for ATG.

Implements the JSON-RPC subset MCP clients need (``initialize``,
``tools/list``, ``tools/call``) over stdio with no vendor SDK dependency, so the
same tool contracts can be hosted by any transport.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Iterable, Optional, TextIO

from .tools import TOOL_CONTRACTS, TOOLS, call_tool, server_info

PROTOCOL_VERSION = "2024-11-05"


class AtgMcpServer:
    def __init__(self, protocol_version: str = PROTOCOL_VERSION) -> None:
        self.protocol_version = protocol_version

    # -- request handling ------------------------------------------------
    def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}

        if method == "initialize":
            return self._result(request_id, {
                "protocolVersion": self.protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": server_info(),
            })
        if method in ("notifications/initialized", "initialized"):
            return None
        if method == "tools/list":
            return self._result(request_id, {"tools": [c.to_mcp() for c in TOOL_CONTRACTS]})
        if method == "tools/call":
            name = params.get("name", "")
            if name not in TOOLS:
                return self._error(request_id, -32601, f"unknown tool '{name}'")
            try:
                payload = call_tool(name, params.get("arguments") or {})
            except Exception as error:  # surfaced to the client, never swallowed
                return self._result(request_id, {
                    "isError": True,
                    "content": [{"type": "text", "text": f"{type(error).__name__}: {error}"}],
                })
            return self._result(request_id, {
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "structuredContent": payload,
                "isError": False,
            })
        if method == "ping":
            return self._result(request_id, {})
        return self._error(request_id, -32601, f"unknown method '{method}'")

    def serve(self, stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError as error:
                self._write(stdout, self._error(None, -32700, f"parse error: {error}"))
                continue
            response = self.handle(request)
            if response is not None:
                self._write(stdout, response)

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _result(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    @staticmethod
    def _write(stdout: TextIO, payload: Dict[str, Any]) -> None:
        stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        stdout.flush()


def run(argv: Optional[Iterable[str]] = None) -> int:
    AtgMcpServer().serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
