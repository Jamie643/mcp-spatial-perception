# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Real DePIN network adapter (replacing the mock node feed)
- `query_by_location(lat, lon)` tool
- `subscribe_to_node(node_id)` push notifications
- Frame snapshot retrieval
- Auth / signed node requests

## [0.1.4] — 2026-10-06

### Changed

- Sharpened the PyPI tagline: *"Give your AI agent eyes on the physical world — an MCP server for real-time DePIN edge-vision queries."*
- Excluded Markdown files from ruff to prevent formatting churn in documentation code blocks.

## [0.1.3] — 2026-10-05

### Added

- FAQ section to the README (MCP vs. REST, mock rationale, inference placement).
- PyPI and CI screenshots under `docs/`.

### Fixed

- Corrected `python -m mcp_spatial` → `python mcp_spatial.py` in the README.

## [0.1.2] — 2025-10-05

### Fixed

- Normalized archive member paths in wheel and sdist builds (`only-include` for hatch).
- Resolved PyPI 400 errors from `.gitignore` and `./PKG-INFO` being included in distributions.

## [0.1.1] — 2026-10-05

### Added

- PyPI Trusted Publishing workflow (`publish.yml`) using OIDC — no API tokens stored.

### Changed

- Excluded non-package files from wheel and sdist builds.

## [0.1.0] — 2026-10-05

### Added

- Initial release.
- MCP server implementing `initialize`, `tools/list`, and `tools/call`.
- `query_spatial_feed(node_id)` tool with a mocked edge-vision payload.
- Spec-compliant JSON-RPC 2.0 error responses.
- stdio transport with stderr logging.
- pytest test suite covering handshake, tools, error paths, and stdio loop.
- CI workflow: ruff (lint + format), mypy (strict), pytest on Python 3.10–3.12.

[Unreleased]: https://github.com/jamie643/mcp-spatial-perception/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/jamie643/mcp-spatial-perception/releases/tag/v0.1.4
[0.1.3]: https://github.com/jamie643/mcp-spatial-perception/releases/tag/v0.1.3
[0.1.2]: https://github.com/jamie643/mcp-spatial-perception/releases/tag/v0.1.2
[0.1.1]: https://github.com/jamie643/mcp-spatial-perception/releases/tag/v0.1.1
[0.1.0]: https://github.com/jamie643/mcp-spatial-perception/releases/tag/v0.1.0
