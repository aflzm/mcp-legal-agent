# Functional Validation Record

Validation date: 2026-10-10 (Asia/Shanghai). This file records functional checks; it is not a model performance report.

- Environment: Windows, Python 3.12.14; the source is parsed with Python 3.10 syntax.
- `python -m unittest discover -s tests -v`: all 9 tests pass.
- Coverage: FastAPI parameter validation and the analysis endpoint, budget and deduplication, failed calls consuming budget, cross-request isolation, evidence levels not being downgraded, model JSON fallback handling, set-based Exact Match, and vector failure fallback.
- A real MCP stdio handshake and tool call have passed; the model and statute data are still Mocked.
- Fixes: in the Windows subprocess, initialize rank-bm25/NumPy first and then start the stdio thread; run synchronous retrieval in a worker thread, with a 120-second timeout on protocol calls.
- Ruff code style checks pass; basic dependency consistency checks pass.
- No ellipsis placeholders in the code; all Python files pass compilation checks.

Key validation versions: FastAPI 0.143.0, MCP 1.30.0, Pydantic 2.14.0, rank-bm25 0.2.2, NumPy 2.5.3, HTTPX 0.28.1.

Execution environment limitation: the sandbox's Windows async socketpair initialization sometimes blocked; the final HTTP and MCP tests were completed in an environment that allows local communication.
The current Starlette version emits a deprecation notice for the HTTPX test client, and the tests pass; this is a dependency migration notice, not a functional error.

Not validated: real Qwen/Embedding calls, actual Chroma indexing, real CAIL2018 accuracy, throughput, and production deployment.
The 4.46 percentage points in `evaluation/simulated_results.json` are hypothetical values and do not come from the functional tests above.