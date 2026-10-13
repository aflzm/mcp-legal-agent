"""Environment variable configuration; fully offline by default."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    mock: bool = os.getenv("MOCK_MODE", "true").lower() == "true"
    api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    base_url: str = os.getenv(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model: str = os.getenv("QWEN_MODEL", "qwen-plus")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    max_searches: int = int(os.getenv("MAX_SEARCHES", "3"))
    top_k: int = int(os.getenv("TOP_K", "5"))
    corpus: str = os.getenv("LAW_CORPUS", str(ROOT / "data/laws.json"))
    transport: str = os.getenv("TOOL_TRANSPORT", "local")

    def __post_init__(self) -> None:
        if not 1 <= self.max_searches <= 10 or not 1 <= self.top_k <= 20:
            raise ValueError(
                "The search budget must be between 1 and 10, and TOP_K must be between 1 and 20"
            )
        if self.transport not in {"local", "stdio"}:
            raise ValueError("TOOL_TRANSPORT must be local or stdio")
