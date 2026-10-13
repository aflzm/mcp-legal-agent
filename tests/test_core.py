"""Functional tests for control constraints and the service protocol, not a
model accuracy benchmark."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.evaluator import CandidateEvaluator
from agent.harness import AgentHarness, RunState
from agent.mcp_tool import ToolClient
from agent.retriever import HybridRetriever
from config import Settings
from evaluation.evaluate import exact_match


class BrokenTool:
    def call(self, query: str, fact: str) -> dict:
        raise RuntimeError("simulated tool failure")


class CoreTests(unittest.TestCase):
    def test_budget_and_duplicate_hooks(self) -> None:
        harness = AgentHarness(Settings(mock=True, max_searches=2))
        state = RunState()
        self.assertTrue(harness.before_action(state, "theft, property"))
        self.assertFalse(harness.before_action(state, "theft property"))
        self.assertEqual(state.searches, 1)
        self.assertTrue(harness.before_action(state, "theft amount"))
        self.assertFalse(harness.before_action(state, "other query"))
        self.assertEqual(state.stop_reason, "budget_exhausted")

    def test_failures_consume_budget(self) -> None:
        harness = AgentHarness(Settings(mock=True, max_searches=2), tool=BrokenTool())
        result = harness.run("unknown case")
        self.assertEqual(result["searches"], 2)
        self.assertEqual(result["stop_reason"], "budget_exhausted")
        self.assertEqual(result["articles"], [])

    def test_request_isolation_and_abstention(self) -> None:
        harness = AgentHarness(Settings(mock=True))
        first = harness.run("secretly stole another person's property in a relatively large amount")
        second = harness.run("unknown case")
        self.assertEqual(first["articles"], [264])
        self.assertEqual(second["articles"], [])
        self.assertLessEqual(second["searches"], 3)
        self.assertNotIn("264", [x["id"] for x in second["evidence"]])

    def test_memory_cannot_downgrade(self) -> None:
        harness = AgentHarness(Settings(mock=True))
        state = RunState()
        for label in ("strong", "partial", "miss"):
            harness.after_tool_call(state, {"candidates": [{"id": "264", "label": label}]})
        self.assertEqual(state.memory["264"]["label"], "strong")

    def test_invalid_llm_output_falls_back(self) -> None:
        evaluator = CandidateEvaluator(Settings(mock=True))
        candidate = {"id": "264", "keyword_groups": [["theft"]]}
        with patch.object(evaluator.client, "chat", return_value=('[{"id":"999"}]', "qwen")):
            result = evaluator.evaluate("theft", [candidate])
        self.assertEqual(result[0]["label"], "strong")
        self.assertEqual(result[0]["evaluator_backend"], "mock:invalid_evaluator_json")

    def test_exact_match_is_set_based(self) -> None:
        self.assertEqual(exact_match([264], [264, 263]), 0)
        self.assertEqual(exact_match([263, 264], [264, 263]), 1)

    def test_vector_api_failure_is_explicit(self) -> None:
        retriever = HybridRetriever(Settings(mock=False, api_key="test-only"))
        with patch.object(retriever.client, "post", side_effect=TimeoutError):
            ranked, backend = retriever.vector_rank("theft")
        self.assertTrue(ranked)
        self.assertTrue(backend.startswith("mock:vector_error:"))

    def test_real_mcp_stdio_transport(self) -> None:
        result = ToolClient(Settings(mock=True, transport="stdio")).call(
            "theft", "secretly stole property in a relatively large amount"
        )
        self.assertIn("candidates", result)
        self.assertTrue(any(item["id"] == "264" for item in result["candidates"]))

    def test_api_validation(self) -> None:
        from fastapi.testclient import TestClient

        from main import app

        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            self.assertEqual(client.post("/analyze", json={"fact": " "}).status_code, 422)
            response = client.post(
                "/analyze", json={"fact": "secretly stole property in a relatively large amount"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(264, response.json()["articles"])


if __name__ == "__main__":
    unittest.main()
