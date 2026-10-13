"""Offline retrieval building blocks, plus a DashScope client with explicit degradation markers."""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.request
from collections import Counter
from typing import Any


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\w]+", text.casefold()))


def tokens(text: str) -> list[str]:
    """Single- and double-character features for CJK text and whole words for
    English; does not rely on a networked tokenizer."""
    parts = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]+", text.lower())
    result = []
    for part in parts:
        if "\u4e00" <= part[0] <= "\u9fff":
            result.extend(part)
            result.extend(part[i : i + 2] for i in range(len(part) - 1))
        else:
            result.append(part)
    return result


def embedding(text: str, dimension: int = 256) -> list[float]:
    """Stable hash vectors are for Mock use only and are not claimed to be
    equivalent to a semantic model."""
    vector = [0.0] * dimension
    for token, count in Counter(tokens(text)).items():
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        vector[index] += count * (1 if digest[4] % 2 else -1)
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vector dimensions do not match")
    norm = math.sqrt(sum(x * x for x in left) * sum(x * x for x in right))
    return sum(a * b for a, b in zip(left, right)) / norm if norm else 0.0


def bm25_scores(query: str, documents: list[str]) -> list[float]:
    corpus = [tokens(text) or ["__empty__"] for text in documents]
    if not corpus:
        return []
    try:
        from rank_bm25 import BM25Plus

        return [float(x) for x in BM25Plus(corpus).get_scores(tokens(query))]
    except ImportError:
        # Use positive IDF like BM25Plus, to make the demo work on small samples.
        average = sum(map(len, corpus)) / len(corpus)
        output = []
        for doc in corpus:
            counts = Counter(doc)
            score = 0.0
            for token in tokens(query):
                frequency = counts[token]
                if not frequency:
                    continue
                df = sum(token in item for item in corpus)
                idf = math.log(1 + (len(corpus) - df + 0.5) / (df + 0.5))
                denominator = frequency + 1.5 * (0.25 + 0.75 * len(doc) / average)
                score += idf * frequency * 2.5 / denominator
            output.append(score)
        return output


def rrf(rankings: list[list[str]], constant: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        # Duplicate IDs within the same ranking must not be scored twice.
        for rank, key in enumerate(dict.fromkeys(ranking), start=1):
            scores[key] = scores.get(key, 0.0) + 1 / (constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


class QwenClient:
    def __init__(self, key: str, base_url: str, model: str, mock: bool) -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.mock = mock

    def post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.base_url + endpoint,
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + self.key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)

    def chat(self, system: str, user: str) -> tuple[str | None, str]:
        if self.mock or not self.key:
            return None, "mock:disabled_or_missing_key"
        try:
            result = self.post(
                "/chat/completions",
                {
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            value = result["choices"][0]["message"]["content"]
            if not isinstance(value, str) or not value.strip():
                raise ValueError("empty model response")
            return value, "qwen"
        except Exception as error:
            return None, "mock:api_error:" + type(error).__name__


def parse_json(text: str) -> Any:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value)
    return json.loads(value)
