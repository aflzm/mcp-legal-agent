"""Set-based Exact Match over a CAIL JSONL set; simulated reports are strictly
separated from actual computation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.harness import AgentHarness
from agent.retriever import HybridRetriever
from config import ROOT, Settings


def exact_match(prediction: list[int], reference: list[int]) -> float:
    return float(set(prediction) == set(reference))


def evaluate(path: Path, settings: Settings) -> dict:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not rows:
        raise ValueError("The evaluation set must not be empty")
    harness = AgentHarness(settings)
    retriever = HybridRetriever(settings)
    baseline = 0.0
    controlled = 0.0
    details = []
    covered = {int(doc["id"]) for doc in retriever.documents}
    uncovered: set[int] = set()
    for row in rows:
        labels = [int(value) for value in row["meta"]["relevant_articles"]]
        uncovered.update(set(labels) - covered)
        ranked, backend = retriever.vector_rank(row["fact"])
        prediction = harness.run(row["fact"])["articles"]
        top_one = [int(ranked[0])] if ranked else []
        baseline += exact_match(top_one, labels)
        controlled += exact_match(prediction, labels)
        details.append(
            {
                "reference": labels,
                "baseline": top_one,
                "agent": prediction,
                "vector_backend": backend,
            }
        )
    return {
        "kind": "computed",
        "dataset": str(path),
        "count": len(rows),
        "mock_mode": settings.mock,
        "baseline_exact_match": baseline / len(rows),
        "agent_exact_match": controlled / len(rows),
        "improvement_percentage_points": (controlled - baseline) * 100 / len(rows),
        "uncovered_articles": sorted(uncovered),
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "data/cail_mock.jsonl")
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = (
        json.loads((ROOT / "evaluation/simulated_results.json").read_text(encoding="utf-8"))
        if args.simulate
        else evaluate(args.data, Settings())
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
