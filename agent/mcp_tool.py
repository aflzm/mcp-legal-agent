"""A stateless tool invocable via a local adapter or real MCP stdio."""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from dataclasses import asdict
from typing import Any

from agent.evaluator import CandidateEvaluator
from agent.retriever import HybridRetriever
from config import ROOT, Settings


def retrieve_and_verify(
    query: str, fact: str, top_k: int = 5, settings: Settings | None = None
) -> dict[str, Any]:
    if not query.strip() or not fact.strip() or not 1 <= top_k <= 20:
        raise ValueError("Query/case must not be empty, and top_k must be between 1 and 20")
    if len(query) > 12000 or len(fact) > 12000:
        raise ValueError("input too long")
    config = settings or Settings()
    candidates, backend = HybridRetriever(config).search(query, top_k)
    return {
        "candidates": CandidateEvaluator(config).evaluate(fact, candidates),
        "retrieval_backend": backend,
    }


class ToolClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def call(self, query: str, fact: str) -> dict[str, Any]:
        if self.settings.transport == "local":
            return retrieve_and_verify(query, fact, self.settings.top_k, self.settings)
        return asyncio.run(self._bounded_stdio(query, fact))

    async def _bounded_stdio(self, query: str, fact: str) -> dict[str, Any]:
        return await asyncio.wait_for(self._stdio(query, fact), timeout=120)

    async def _stdio(self, query: str, fact: str) -> dict[str, Any]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT)
        env.setdefault("OPENBLAS_NUM_THREADS", "1")
        env.setdefault("OMP_NUM_THREADS", "1")
        # Explicitly pass the settings so the subprocess and host share the same semantics.
        env["LEGAL_SETTINGS_JSON"] = json.dumps(asdict(self.settings))
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "agent.mcp_tool"], env=env
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool(
                    "legal_search",
                    {
                        "query": query,
                        "fact": fact,
                        "top_k": self.settings.top_k,
                    },
                )
                if response.isError:
                    raise RuntimeError("MCP tool call failed")
                text = "".join(item.text for item in response.content if item.type == "text")
                return json.loads(text)


def serve() -> None:
    from mcp.server.fastmcp import FastMCP

    # On Windows, initialize NumPy first, then start the stdio reader thread,
    # to avoid lazy-loading lock contention.
    try:
        importlib.import_module("rank_bm25")
    except ImportError:
        pass

    server = FastMCP("Controlled Legal Search", stateless_http=True)
    config = (
        Settings(**json.loads(os.environ["LEGAL_SETTINGS_JSON"]))
        if "LEGAL_SETTINGS_JSON" in os.environ
        else Settings()
    )

    @server.tool()
    async def legal_search(query: str, fact: str, top_k: int = 5) -> str:
        """Retrieve statutes via multiple channels and verify their relevance
        to the original case."""
        # Move synchronous model and vector store operations off the protocol
        # event loop so that cancellation and timeouts take effect.
        result = await asyncio.to_thread(retrieve_and_verify, query, fact, top_k, config)
        return json.dumps(result, ensure_ascii=False)

    server.run(transport="stdio")


if __name__ == "__main__":
    serve()
