"""FastAPI service: python -m uvicorn main:app --port 8001."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

from agent.harness import AgentHarness
from config import Settings

app = FastAPI(
    title="Controlled Legal Retrieval Agent System based on the MCP mechanism",
    version="1.0.0",
)


class CaseRequest(BaseModel):
    fact: str = Field(min_length=1, max_length=12000)

    @field_validator("fact")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The case text must not be empty")
        return value.strip()


@app.get("/health")
def health() -> dict:
    settings = Settings()
    return {"status": "ok", "mock": settings.mock, "transport": settings.transport}


@app.post("/analyze")
def analyze(request: CaseRequest) -> dict:
    return AgentHarness().run(request.fact)
