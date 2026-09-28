"""Call one MCP read tool over HTTP with a bearer token, as an MCP client would.

Usage: python mcp_call.py <mcp url> <token>. Exits non-zero if the call is refused.
"""

import json
import sys
from urllib.request import Request, urlopen

PROTOCOL = "2025-06-18"


def post(url: str, token: str, message: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(message).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": PROTOCOL,
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read() or b"{}")


def main(url: str, token: str) -> None:
    post(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "live-browser-proof", "version": "1"},
            },
        },
    )
    result = post(
        url,
        token,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "business_records_discover",
                "arguments": {"family": "item", "limit": 3},
            },
        },
    )
    if "error" in result or result.get("result", {}).get("isError"):
        raise SystemExit(f"MCP call refused: {json.dumps(result)[:500]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
