"""BM25 + Qwen Embedding/Chroma multi-channel fusion retrieval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from common import QwenClient, bm25_scores, cosine, embedding, rrf
from config import Settings


class HybridRetriever:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.documents = json.loads(Path(settings.corpus).read_text(encoding="utf-8"))
        ids = [doc["id"] for doc in self.documents]
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("The statute corpus must not be empty and IDs must be unique")
        self.client = QwenClient(settings.api_key, settings.base_url, settings.model, settings.mock)

    def vector_rank(self, query: str) -> tuple[list[str], str]:
        texts = [doc["text"] for doc in self.documents]
        if not self.settings.mock and self.settings.api_key:
            try:
                import chromadb

                vectors = []
                # Batch the requests to avoid exceeding the single-batch Embedding limit.
                for start in range(0, len(texts) + 1, 10):
                    batch = (texts + [query])[start : start + 10]
                    response = self.client.post(
                        "/embeddings",
                        {
                            "model": self.settings.embedding_model,
                            "input": batch,
                        },
                    )
                    vectors.extend(
                        row["embedding"]
                        for row in sorted(response["data"], key=lambda x: x["index"])
                    )
                client = chromadb.EphemeralClient()
                # A per-call local index keeps the tool session-free.
                import uuid

                collection = client.create_collection(
                    "laws-" + uuid.uuid4().hex,
                    metadata={"hnsw:space": "cosine"},
                )
                try:
                    collection.add(
                        ids=[doc["id"] for doc in self.documents],
                        embeddings=vectors[:-1],
                        documents=texts,
                    )
                    result = collection.query(query_embeddings=[vectors[-1]], n_results=len(texts))
                    return result["ids"][0], "qwen_embedding+chroma"
                finally:
                    client.delete_collection(collection.name)
            except Exception as error:
                backend = "mock:vector_error:" + type(error).__name__
        else:
            backend = "mock:hash_vector"
        vector = embedding(query)
        scored = [(doc["id"], cosine(vector, embedding(doc["text"]))) for doc in self.documents]
        return [key for key, _ in sorted(scored, key=lambda x: -x[1])], backend

    def search(self, query: str, top_k: int) -> tuple[list[dict[str, Any]], str]:
        dense, backend = self.vector_rank(query)
        lexical = bm25_scores(query, [doc["text"] for doc in self.documents])
        sparse = [
            self.documents[i]["id"] for i in sorted(range(len(lexical)), key=lambda i: -lexical[i])
        ]
        by_id = {doc["id"]: doc for doc in self.documents}
        result = [
            {**by_id[key], "retrieval_score": score} for key, score in rrf([dense, sparse])[:top_k]
        ]
        return result, backend
