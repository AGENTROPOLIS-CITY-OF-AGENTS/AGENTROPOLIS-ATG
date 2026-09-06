"""ATG MCP server package: the twelve canonical ATG tool contracts."""

from .server import PROTOCOL_VERSION, AtgMcpServer, run
from .tools import TOOL_CONTRACTS, TOOL_NAMES, TOOLS, ToolContract, call_tool, server_info

__all__ = [
    "AtgMcpServer",
    "PROTOCOL_VERSION",
    "TOOLS",
    "TOOL_CONTRACTS",
    "TOOL_NAMES",
    "ToolContract",
    "call_tool",
    "run",
    "server_info",
]
