"""Schemas for ticket history and support comments."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    note: str = Field(min_length=1, max_length=2000, description="Support comment text")
    performed_by: str = Field(min_length=2, max_length=100, description="Support staff name")


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    activity_type: str
    old_status: str | None
    new_status: str | None
    old_value: str | None
    new_value: str | None
    note: str | None
    performed_by: str
    created_at: datetime