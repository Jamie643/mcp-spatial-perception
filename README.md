# mcp-spatial-perception

[![CI](https://github.com/jamie643/mcp-spatial-perception/actions/workflows/ci.yml/badge.svg)](https://github.com/jamie643/mcp-spatial-perception/actions/workflows/ci.yml)
[![Publish](https://github.com/jamie643/mcp-spatial-perception/actions/workflows/publish.yml/badge.svg)](https://github.com/jamie643/mcp-spatial-perception/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/mcp-spatial-perception.svg?label=PyPI&color=blue)](https://pypi.org/project/mcp-spatial-perception/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-spatial-perception.svg)](https://pypi.org/project/mcp-spatial-perception/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> **Give your AI agent eyes on the physical world.**
>
> An [MCP](https://modelcontextprotocol.io) server that exposes real-time spatial perception queries from DePIN edge-vision nodes to any LLM that speaks the Model Context Protocol — Claude Desktop, Cursor, Claude Code, or a custom agent framework.

---

## The problem

LLM agents can read files, browse the web, and call APIs — but they're blind to the physical world. They can't answer questions like:

- *"Is there foot traffic at location X right now?"*
- *"What is the live visual state of camera node #402?"*
- *"Is the loading dock clear before I dispatch the truck?"*

There's no standard way for an agent to ask those questions.

## The solution

`mcp-spatial-perception` is a small, dependency-free MCP server that sits between your agent and a DePIN network of edge-vision nodes. The agent calls a tool, the server queries the network, and structured JSON describing the scene comes back — detections, bounding boxes, confidence scores, environmental state, geolocation.

```
┌─────────────┐   MCP / JSON-RPC   ┌───────────────────────┐   DePIN query   ┌──────────────┐
│  LLM agent  │ ─────────────────► │ mcp-spatial-perception│ ──────────────► │ edge nodes   │
│ (Claude,    │ ◄───────────────── │  (this repo)          │ ◄────────────── │ (cameras,    │
│  Cursor…)   │   structured JSON  └───────────────────────┘   telemetry     │  sensors)    │
└─────────────┘                                                               └──────────────┘
```

---

## Install

```bash
pip install mcp-spatial-perception
```

Requires **Python 3.10+**. No runtime dependencies — pure standard library.

## Use with Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spatial-perception": {
      "command": "mcp-spatial-perception"
    }
  }
}
```

Restart Claude Desktop. The `query_spatial_feed` tool will appear in the tool picker.

## Use with Cursor / Claude Code / any MCP client

The server speaks JSON-RPC 2.0 over stdio. Any MCP-compatible client can launch it via the `mcp-spatial-perception` console script:

```bash
mcp-spatial-perception
```

Or directly, if you have the source checked out:

```bash
python mcp_spatial.py
```

## Use programmatically

```python
from mcp_spatial import handle_mcp_request

response = handle_mcp_request(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "query_spatial_feed", "arguments": {"node_id": "node_402"}},
    }
)

print(response["result"]["content"][0]["text"])
```

---

## The `query_spatial_feed` tool

**Input**

| Field     | Type     | Required | Description                 |
| --------- | -------- | -------- | --------------------------- |
| `node_id` | `string` | yes      | The DePIN node ID to query. |

**Output** — structured JSON describing the node's current visual state:

```json
{
  "node_id": "node_402",
  "timestamp": 1770000000,
  "location": { "lat": 9.0765, "lon": 7.3986 },
  "detections": [
    {
      "object": "delivery_truck",
      "confidence": 0.94,
      "bounding_box": [120, 80, 450, 300]
    },
    {
      "object": "person",
      "confidence": 0.88,
      "bounding_box": [50, 60, 110, 200]
    }
  ],
  "environmental": { "light_level": "daylight", "obscured": false }
}
```

| Field           | Meaning                                          |
| --------------- | ------------------------------------------------ |
| `node_id`       | Echo of the queried node.                        |
| `timestamp`     | Unix seconds when the frame was captured.        |
| `location`      | Latitude / longitude of the node.                |
| `detections`    | Objects found in the frame, with bounding boxes. |
| `environmental` | Lighting, occlusion, and other scene conditions. |

---

## FAQ

**Why an MCP server and not just a REST API?**
Because MCP is what Claude Desktop, Cursor, and Claude Code speak natively. A REST API would require each client to write a custom integration. An MCP server is a drop-in tool for every MCP-aware agent.

**Why is the feed mocked right now?**
To keep the protocol surface testable and stable while the DePIN adapter is built. The `mock_node_feed` function is a single, well-isolated seam — swapping it for a real network client doesn't touch the MCP logic.

**Does this run the vision model?**
No. Edge nodes do the frame extraction and inference on-device; this server relays the structured result. That's the point of DePIN — the compute is at the edge, not in your agent's process.

---

## Status

> ⚠️ **Alpha.** The MCP protocol surface is stable, but the node feed is currently **mocked**. A real DePIN adapter is on the roadmap.

### Roadmap

- [x] Spec-compliant MCP server (`initialize`, `tools/list`, `tools/call`)
- [x] Published to PyPI with Trusted Publishing
- [x] CI: lint (ruff), type-check (mypy strict), test (pytest) on Python 3.10–3.12
- [ ] Replace mock feed with a real DePIN adapter
- [ ] Add `query_by_location(lat, lon)` tool
- [ ] Add `subscribe_to_node(node_id)` push notifications
- [ ] Frame snapshot retrieval
- [ ] Auth / signed node requests

---

## Development

```bash
git clone https://github.com/jamie643/mcp-spatial-perception.git
cd mcp-spatial-perception
pip install -e ".[dev]"

ruff check .          # lint
ruff format --check . # format check
mypy mcp_spatial.py   # type-check (strict)
pytest                # tests + coverage
```

## Contributing

Issues and pull requests are welcome. For substantial changes, please open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE) © 2026 Jamie643
