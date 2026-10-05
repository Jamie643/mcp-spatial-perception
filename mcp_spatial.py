"""mcp-spatial-perception: an MCP server exposing spatial perception tools.

This server speaks JSON-RPC 2.0 over stdio, implementing the Model Context
Protocol so LLM agents (Cursor, Claude Code, etc.) can query edge-vision
telemetry from DePIN nodes.

Current status: the node feed is mocked. Real DePIN adapter lands later.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

__version__ = "0.1.4"

PROTOCOL_VERSION = "2024-11-05"

# --- Logging ---------------------------------------------------------------
# MCP requires stdout to carry *only* JSON-RPC messages. All diagnostics
# must go to stderr, or clients will choke on non-JSON lines.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="[mcp-spatial-perception] %(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


# --- Tools -----------------------------------------------------------------
TOOLS: list[dict[str, Any]] = [
    {
        "name": "query_spatial_feed",
        "description": (
            "Fetch real-time edge-parsed visual detection data from a physical "
            "DePIN node feed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "type": "string",
                    "description": "The DePIN node ID to query.",
                }
            },
            "required": ["node_id"],
        },
    }
]


# --- Mock node feed --------------------------------------------------------
def mock_node_feed(node_id: str) -> dict[str, Any]:
    """Return a simulated edge-vision payload for a node.

    Replace with a real DePIN query once the network adapter is wired up.
    """
    return {
        "node_id": node_id,
        "timestamp": int(time.time()),
        "location": {"lat": 9.0765, "lon": 7.3986},  # Abuja, for now
        "detections": [
            {
                "object": "delivery_truck",
                "confidence": 0.94,
                "bounding_box": [120, 80, 450, 300],
            },
            {
                "object": "person",
                "confidence": 0.88,
                "bounding_box": [50, 60, 110, 200],
            },
        ],
        "environmental": {"light_level": "daylight", "obscured": False},
    }


# --- JSON-RPC helpers ------------------------------------------------------
def _ok(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


# --- Request handling ------------------------------------------------------
def handle_mcp_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single parsed JSON-RPC request.

    Returns the response dict, or None for notifications (which by spec
    must not receive a response).
    """
    req_id = request.get("id")
    method = request.get("method")

    if method is None:
        return _err(req_id, -32600, "Invalid Request: missing method")

    # --- MCP handshake ---
    if method == "initialize":
        return _ok(
            req_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "mcp-spatial-perception",
                    "version": __version__,
                },
            },
        )

    if method in ("notifications/initialized", "initialized"):
        # Notification: no response permitted.
        return None

    # --- Tool discovery ---
    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    # --- Tool invocation ---
    if method == "tools/call":
        params = request.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}

        if name != "query_spatial_feed":
            return _err(req_id, -32602, f"Unknown tool: {name!r}")

        node_id = arguments.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            return _err(req_id, -32602, "Missing required argument: node_id")

        telemetry = mock_node_feed(node_id)
        return _ok(
            req_id,
            {"content": [{"type": "text", "text": json.dumps(telemetry)}]},
        )

    # --- Unknown method ---
    return _err(req_id, -32601, f"Method not found: {method!r}")


# --- stdio transport -------------------------------------------------------
def serve(stdin: Any = None, stdout: Any = None) -> int:
    """Run the stdio JSON-RPC loop. Returns process exit code."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    log.info("mcp-spatial-perception v%s ready on stdio", __version__)

    for line in stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            log.warning("Malformed JSON: %s", exc)
            err = _err(None, -32700, f"Parse error: {exc}")
            stdout.write(json.dumps(err) + "\n")
            stdout.flush()
            continue

        try:
            response = handle_mcp_request(request)
        except Exception as exc:  # noqa: BLE001 — top-level guard
            log.exception("Unhandled error while processing request")
            err = _err(request.get("id"), -32603, f"Internal error: {exc}")
            stdout.write(json.dumps(err) + "\n")
            stdout.flush()
            continue

        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()

    log.info("stdin closed, shutting down")
    return 0


def main() -> int:
    """Console-script entry point (see pyproject.toml [project.scripts])."""
    return serve()


if __name__ == "__main__":
    sys.exit(main())
