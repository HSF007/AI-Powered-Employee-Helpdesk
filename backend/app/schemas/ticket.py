"""Ticket request/response schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models import CATEGORIES, PRIORITIES, STATUSES
from app.schemas.activity import ActivityOut

# Literal types built from the same tuples as the DB CHECK constraints
Category = Literal[CATEGORIES]  # "Hardware" | "Software" | "Network" | "Access" | "Other"
Priority = Literal[PRIORITIES]  # "Low" | "Medium" | "High"
Status = Literal[STATUSES]      # "New" | "In Progress" | "Resolved"


class _Input(BaseModel):
    """Base for request bodies: trims whitespace, rejects unknown fields."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


# ---------------- Requests ----------------
class TicketCreate(_Input):
    title: str = Field(min_length=5, max_length=200, examples=["Wireless keyboard not responding"])
    description: str = Field(
        min_length=10, max_length=5000,
        examples=["My wireless keyboard stopped typing this morning. Mouse still works."],
    )
    requester_name: str = Field(min_length=2, max_length=100, examples=["Priya Sharma"])
    requester_contact: str = Field(
        min_length=3, max_length=150, description="Email or employee ID",
        examples=["priya.sharma@company.com"],
    )
    department: str | None = Field(default=None, max_length=100, examples=["Finance"])
    category: Category | None = Field(default=None, description="Optional - employee's guess")

    @field_validator("category", "department", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        # The React form sends "" for an unselected dropdown
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("requester_contact")
    @classmethod
    def _normalise_contact(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Contact must be an email address or employee ID without spaces.")
        return v.lower()


class TicketUpdate(_Input):
    """Fields support staff may change. Title/description are immutable after submission."""
    category: Category | None = None
    priority: Priority | None = None
    performed_by: str = Field(min_length=2, max_length=100, description="Support staff name")

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if self.category is None and self.priority is None:
            raise ValueError("Provide a category and/or priority to update.")
        return self


class StatusUpdate(_Input):
    status: Status
    performed_by: str = Field(min_length=2, max_length=100, description="Support staff name")
    note: str | None = Field(default=None, max_length=2000)


# ---------------- Responses ----------------
class RequesterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    contact: str
    department: str | None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester: RequesterOut
    title: str
    description: str
    category: str | None   # human-confirmed (None until staff confirm)
    priority: str | None   # human-confirmed (None until staff confirm)
    status: str
    created_at: datetime
    updated_at: datetime


class TicketDetailOut(TicketOut):
    activities: list[ActivityOut] = []


class SummaryOut(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_category: dict[str, int]