"""
schemas.py - Pydantic models defining exact request/response shapes.
FastAPI uses these for automatic request validation and response serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's question")
    session_id: Optional[str] = Field(
        default="default",
        description="Identifies which ongoing conversation this belongs to",
    )


class SourceCitation(BaseModel):
    title: str
    law_number: str
    page_reference: str
    category: str
    snippet: str
    distance: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[SourceCitation]
    citation_count: int
    found_context: bool
    latency_seconds: float


class HealthResponse(BaseModel):
    status: str
    ready: bool
    indexed_chunks: int