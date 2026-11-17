"""ORM models mirroring database/schema.sql (schema.sql is the source of truth)."""
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

# Allowed values (must match CHECK constraints in schema.sql)
CATEGORIES = ("Hardware", "Software", "Network", "Access", "Other")
PRIORITIES = ("Low", "Medium", "High")
STATUSES = ("New", "In Progress", "Resolved")
ACTIVITY_TYPES = ("CREATED", "STATUS_CHANGE", "PRIORITY_CHANGE", "CATEGORY_CHANGE", "COMMENT")
FEEDBACK_ACTIONS = ("ACCEPTED", "CORRECTED")


class Base(DeclarativeBase):
    pass


class Requester(Base):
    __tablename__ = "requesters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    department: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="requester")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("requesters.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(20))   # human-confirmed
    priority: Mapped[str | None] = mapped_column(String(10))   # human-confirmed
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="New")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    requester: Mapped[Requester] = relationship(back_populates="tickets")
    activities: Mapped[list["TicketActivity"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketActivity.created_at"
    )
    suggestions: Mapped[list["AISuggestion"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="AISuggestion.created_at.desc()"
    )


class TicketActivity(Base):
    __tablename__ = "ticket_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str | None] = mapped_column(String(20))
    old_value: Mapped[str | None] = mapped_column(String(50))
    new_value: Mapped[str | None] = mapped_column(String(50))
    note: Mapped[str | None] = mapped_column(Text)
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False, server_default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="activities")


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    suggested_category: Mapped[str] = mapped_column(String(20), nullable=False)
    suggested_priority: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    troubleshooting_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="suggestions")
    feedback: Mapped[list["AIFeedback"]] = relationship(back_populates="suggestion", cascade="all, delete-orphan")


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("ai_suggestions.id", ondelete="CASCADE"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    is_useful: Mapped[bool] = mapped_column(Boolean, nullable=False)
    final_category: Mapped[str] = mapped_column(String(20), nullable=False)
    final_priority: Mapped[str] = mapped_column(String(10), nullable=False)
    staff_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    suggestion: Mapped[AISuggestion] = relationship(back_populates="feedback")