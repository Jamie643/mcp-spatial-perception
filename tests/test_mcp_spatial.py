"""Tests for mcp_spatial: the MCP server for spatial perception queries."""

from __future__ import annotations

import io
import json
from typing import Any

import pytest

import mcp_spatial
from mcp_spatial import (
    PROTOCOL_VERSION,
    TOOLS,
    handle_mcp_request,
    mock_node_feed,
    serve,
)


# --- helpers ---------------------------------------------------------------
def rpc(method: str, params: dict[str, Any] | None = None, req_id: int = 1) -> dict[str, Any]:
    """Build a minimal JSON-RPC 2.0 request object."""
    req: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        req["params"] = params
    return req


# --- mock_node_feed --------------------------------------------------------
def test_mock_node_feed_shape() -> None:
    feed = mock_node_feed("node_abc")
    assert feed["node_id"] == "node_abc"
    assert isinstance(feed["timestamp"], int)
    assert "lat" in feed["location"] and "lon" in feed["location"]
    assert isinstance(feed["detections"], list) and feed["detections"]
    for det in feed["detections"]:
        assert {"object", "confidence", "bounding_box"} <= det.keys()


def test_mock_node_feed_echoes_node_id() -> None:
    assert mock_node_feed("x")["node_id"] == "x"
    assert mock_node_feed("y")["node_id"] == "y"


# --- initialize handshake --------------------------------------------------
def test_initialize_returns_protocol_version() -> None:
    resp = handle_mcp_request(rpc("initialize", req_id=42))
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 42
    assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION
    assert resp["result"]["serverInfo"]["name"] == "mcp-spatial-perception"
    assert resp["result"]["serverInfo"]["version"] == mcp_spatial.__version__
    assert "tools" in resp["result"]["capabilities"]


def test_initialized_notification_returns_none() -> None:
    # Notifications MUST NOT receive a response.
    assert handle_mcp_request({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    assert handle_mcp_request({"jsonrpc": "2.0", "method": "initialized"}) is None


# --- tools/list ------------------------------------------------------------
def test_tools_list_exposes_query_spatial_feed() -> None:
    resp = handle_mcp_request(rpc("tools/list"))
    assert resp is not None
    tools = resp["result"]["tools"]
    assert tools == TOOLS
    names = [t["name"] for t in tools]
    assert "query_spatial_feed" in names


def test_tools_list_schema_requires_node_id() -> None:
    schema = TOOLS[0]["inputSchema"]
    assert schema["type"] == "object"
    assert schema["required"] == ["node_id"]
    assert "node_id" in schema["properties"]


# --- tools/call: happy path ------------------------------------------------
def test_tools_call_query_spatial_feed_returns_telemetry() -> None:
    resp = handle_mcp_request(
        rpc("tools/call", params={"name": "query_spatial_feed", "arguments": {"node_id": "n1"}})
    )
    assert resp is not None
    content = resp["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    telemetry = json.loads(content[0]["text"])
    assert telemetry["node_id"] == "n1"
    assert "detections" in telemetry


# --- tools/call: error paths ----------------------------------------------
def test_tools_call_unknown_tool_returns_error() -> None:
    resp = handle_mcp_request(
        rpc("tools/call", params={"name": "does_not_exist", "arguments": {}})
    )
    assert resp is not None
    assert resp["error"]["code"] == -32602
    assert "Unknown tool" in resp["error"]["message"]


def test_tools_call_missing_node_id_returns_error() -> None:
    resp = handle_mcp_request(
        rpc("tools/call", params={"name": "query_spatial_feed", "arguments": {}})
    )
    assert resp is not None
    assert resp["error"]["code"] == -32602
    assert "node_id" in resp["error"]["message"]


def test_tools_call_empty_node_id_returns_error() -> None:
    resp = handle_mcp_request(
        rpc("tools/call", params={"name": "query_spatial_feed", "arguments": {"node_id": ""}})
    )
    assert resp is not None
    assert resp["error"]["code"] == -32602


# --- protocol-level errors -------------------------------------------------
def test_missing_method_returns_invalid_request() -> None:
    resp = handle_mcp_request({"jsonrpc": "2.0", "id": 7})
    assert resp is not None
    assert resp["error"]["code"] == -32600
    assert resp["id"] == 7


def test_unknown_method_returns_method_not_found() -> None:
    resp = handle_mcp_request(rpc("does/not/exist", req_id=99))
    assert resp is not None
    assert resp["error"]["code"] == -32601
    assert resp["id"] == 99


# --- stdio transport -------------------------------------------------------
def _run_serve(*lines: str) -> list[dict[str, Any]]:
    """Feed lines into serve() and return parsed JSON responses."""
    stdin = io.StringIO("\n".join(lines) + "\n")
    stdout = io.StringIO()
    exit_code = serve(stdin=stdin, stdout=stdout)
    assert exit_code == 0
    out_lines = [ln for ln in stdout.getvalue().splitlines() if ln.strip()]
    return [json.loads(ln) for ln in out_lines]


def test_serve_handles_single_request() -> None:
    resp = _run_serve(json.dumps(rpc("initialize", req_id=1)))
    assert len(resp) == 1
    assert resp[0]["id"] == 1
    assert "result" in resp[0]


def test_serve_handles_multiple_requests() -> None:
    resp = _run_serve(
        json.dumps(rpc("initialize", req_id=1)),
        json.dumps(rpc("tools/list", req_id=2)),
        json.dumps(
            rpc(
                "tools/call",
                params={"name": "query_spatial_feed", "arguments": {"node_id": "n"}},
                req_id=3,
            )
        ),
    )
    assert [r["id"] for r in resp] == [1, 2, 3]


def test_serve_skips_blank_lines() -> None:
    resp = _run_serve("", "   ", json.dumps(rpc("tools/list", req_id=1)))
    assert len(resp) == 1


def test_serve_returns_parse_error_for_malformed_json() -> None:
    resp = _run_serve("not json at all")
    assert len(resp) == 1
    assert resp[0]["error"]["code"] == -32700
    assert resp[0]["id"] is None


def test_serve_notification_produces_no_output() -> None:
    resp = _run_serve(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
    assert resp == []


# --- public API sanity -----------------------------------------------------
def test_version_is_string() -> None:
    assert isinstance(mcp_spatial.__version__, str)
    assert mcp_spatial.__version__.count(".") >= 1


def test_main_is_callable() -> None:
    assert callable(mcp_spatial.main)
