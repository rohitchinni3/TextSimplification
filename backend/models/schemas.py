"""Pydantic request/response schemas for the Text Simplification API."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SimplifyRequest(BaseModel):
    """Request body for POST /api/v1/simplify."""

    text: str = Field(..., min_length=1, description="Source text to simplify.")
    target_fk_grade: float = Field(
        default=6.0,
        ge=1.0,
        le=18.0,
        description="Target Flesch–Kincaid Grade Level (1–18). Default 6.",
    )
    max_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum simplification retries. Default 5.",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must contain at least one non-whitespace character.")
        return v


class SimplifyResponse(BaseModel):
    """Response body from POST /api/v1/simplify."""

    simplified_text: str
    original_fk_grade: float
    final_fk_grade: float
    target_fk_grade: float
    target_met: bool
    attempts: int
    provider_mode: str
    notes: Optional[str] = None
