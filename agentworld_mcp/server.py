#!/usr/bin/env python3
"""AgentWorld MCP server.

Serves the 164 AgentWorld tools over stdio and proxies every call to the
hosted AgentWorld endpoint (https://agentworld.me/mcp).

Free tools need no credentials. Paid tools answer HTTP 402 with x402 terms;
set AGENTWORLD_PAYMENT to a settled x402 receipt to have it forwarded as the
X-Payment header.
"""
import json
import os
from pathlib import Path

import httpx
from mcp import types
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.server import MCPTool

REMOTE_URL = os.environ.get("AGENTWORLD_MCP_URL", "https://agentworld.me/mcp")
PAYMENT = os.environ.get("AGENTWORLD_PAYMENT", "").strip()
TOOLS = json.loads((Path(__file__).parent / "tools.json").read_text(encoding="utf-8"))

class Remote:
    """Minimal streamable-HTTP MCP client: one session, reused across calls."""

    def __init__(self):
        self.session_id = None
        self._next_id = 0

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        if PAYMENT:
            h["X-Payment"] = PAYMENT
        return h

    @staticmethod
    def _payload(raw):
        if raw.startswith("event:") or "\ndata:" in raw:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:].strip())
        return json.loads(raw)

    def rpc(self, method, params=None):
        self._next_id += 1
        body = {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}}
        with httpx.Client(timeout=90.0) as client:
            r = client.post(REMOTE_URL, json=body, headers=self._headers())
            if r.headers.get("mcp-session-id"):
                self.session_id = r.headers["mcp-session-id"]
            if r.status_code == 402:
                return None, 402, r.text[:400]
            r.raise_for_status()
            return self._payload(r.text), r.status_code, None

    def ensure_session(self):
        if self.session_id:
            return
        self.rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "agentworld-mcp", "version": "1.0.0"},
        })

    def call(self, name, arguments):
        self.ensure_session()
        data, status, err = self.rpc("tools/call", {"name": name, "arguments": arguments or {}})
        if status == 402:
            return ("This tool is paid (x402, USDC on Base). The server answered 402.\n"
                    "Settle with the AgentPay facilitator, then set AGENTWORLD_PAYMENT to the "
                    "receipt and retry.\n\n" + (err or ""))
        res = (data or {}).get("result") or {}
        parts = []
        for block in res.get("content") or []:
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
        if res.get("isError"):
            parts.append("(tool reported an error)")
        return "\n".join(p for p in parts if p) or json.dumps(res)[:2000]


remote = Remote()

class AgentWorldServer(MCPServer):
    """Serves the AgentWorld tool catalog with its real input schemas."""

    def __init__(self):
        super().__init__(name="agentworld")

    async def list_tools(self):
        return [
            MCPTool(
                name=t["name"],
                description=t["description"] or t["name"],
                input_schema=t["inputSchema"],
            )
            for t in TOOLS
        ]

    async def call_tool(self, name, arguments, context=None):
        if not any(t["name"] == name for t in TOOLS):
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="unknown tool: %s" % name)],
                is_error=True,
            )
        text = remote.call(name, arguments or {})
        return types.CallToolResult(content=[types.TextContent(type="text", text=text)])


def main():
    AgentWorldServer().run("stdio")


if __name__ == "__main__":
    main()
