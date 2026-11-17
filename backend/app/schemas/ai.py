"""Schemas for AI suggestions and staff feedback.

The AI result is *advisory only*: it is stored in ai_suggestions and never
written straight into the tickets table. Support staff confirm or correct it
through the feedback endpoint.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["Hardware", "Software", "Network", "Access", "Other"]
Priority = Literal["Low", "Medium", "High"]


class AIResult(BaseModel):
    """What we require the model to return. Anything else is rejected."""

    category: Category
    priority: Priority
    reason: str = Field(min_length=1, max_length=1000)
    steps: List[str] = Field(min_length=1, max_length=8)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("reason must not be empty")
        return v

    @field_validator("steps")
    @classmethod
    def clean_steps(cls, v: List[str]) -> List[str]:
        cleaned = [s.strip() for s in v if isinstance(s, str) and s.strip()]
        if not cleaned:
            raise ValueError("steps must contain at least one non-empty item")
        return [s[:300] for s in cleaned]


class AISuggestionOut(BaseModel):
    """A stored suggestion, as returned to the frontend."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    suggested_category: Category
    suggested_priority: Priority
    reason: str
    troubleshooting_steps: List[str]
    model_name: str
    created_at: datetime


class AIFeedbackIn(BaseModel):
    """Staff response to a suggestion.

    If final_category / final_priority match the suggestion the action is
    ACCEPTED, otherwise CORRECTED (the server works this out).
    """

    suggestion_id: int
    is_useful: bool
    final_category: Category
    final_priority: Priority
    staff_name: str = Field(min_length=1, max_length=100)

    @field_validator("staff_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("staff_name must not be empty")
        return v


class AIFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    suggestion_id: int
    ticket_id: int
    action: Literal["ACCEPTED", "CORRECTED"]
    is_useful: bool
    final_category: Category
    final_priority: Priority
    staff_name: str
    created_at: datetime


class AIUnavailableOut(BaseModel):
    """Body of the 503 the frontend shows in the AIUnavailable component."""

    detail: str
    ai_available: bool = False
    fallback: Optional[str] = "Please triage this ticket manually."
