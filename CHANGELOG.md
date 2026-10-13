# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-12

### Added

- Controllable agent harness with `before_action` / `after_tool_call` hooks.
- Hard search budget that failed tool calls also consume.
- Stateless retrieval-and-verification tool exposed via both direct `local`
  calls and the real MCP `stdio` transport.
- Hybrid retrieval: BM25 + vector recall fused with Reciprocal Rank Fusion.
- Candidate verification against the original fact with `strong` / `partial` /
  `miss` grading and monotonic evidence memory.
- Evidence-grounded output that reports only validated article IDs, with a
  full per-request audit trace.
- Exact-match evaluation over a CAIL-format JSONL set, and a clearly labeled
  simulated report sample.
- FastAPI service (`/health`, `/analyze`) with request validation.
- Offline, dependency-free demo (`demo.py`).
- Unit tests covering budget, deduplication, isolation, evidence ordering,
  model-output fallback, vector fallback, and the MCP transport.

[1.0.0]: https://github.com/<you>/mcp-legal-agent/releases/tag/v1.0.0