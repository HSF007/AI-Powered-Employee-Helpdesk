"""AI endpoints: analyze a ticket, get the latest suggestion, record staff feedback.

Mount in main.py with:  app.include_router(ai.router)

Contract with P1 (db/models.py, db/session.py):
  * get_db()        - yields a SQLAlchemy Session
  * Ticket          - id, title, description, category, priority, updated_at
  * TicketActivity  - ticket_id, activity_type, old_value, new_value, note, performed_by
  * AISuggestion    - ticket_id, suggested_category, suggested_priority, reason,
                      troubleshooting_steps (JSONB list), model_name, created_at
  * AIFeedback      - suggestion_id, ticket_id, action, is_useful, final_category,
                      final_priority, staff_name
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import AIFeedback, AISuggestion, Ticket, TicketActivity
from app.db.session import get_db
from app.schemas.ai import AIFeedbackIn, AIFeedbackOut, AISuggestionOut
from app.services.ai.ollama_client import (
    AIInvalidResponseError,
    AIUnavailableError,
    OllamaClient,
    get_ollama_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets/{ticket_id}/ai", tags=["ai"])


def _get_ticket_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.post("/analyze", response_model=AISuggestionOut, status_code=status.HTTP_201_CREATED)
def analyze_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    ai: OllamaClient = Depends(get_ollama_client),
):
    """Ask the model for category/priority/reason/steps and store it as a suggestion.

    The ticket's own category/priority are NOT changed here - staff confirm them
    through /feedback. If the model is down the ticket is still fully usable.
    """
    ticket = _get_ticket_or_404(db, ticket_id)
    try:
        result = ai.analyze(ticket.title, ticket.description, ticket_id=ticket.id)
    except AIUnavailableError as e:
        logger.warning("AI unavailable for ticket_id=%s: %s", ticket_id, e)
        raise HTTPException(
            status_code=503,
            detail="AI assistant is unavailable right now. Please triage this ticket manually.",
        )
    except AIInvalidResponseError:
        raise HTTPException(
            status_code=503,
            detail="AI assistant gave an invalid answer. Please triage this ticket manually.",
        )

    suggestion = AISuggestion(
        ticket_id=ticket.id,
        suggested_category=result.category,
        suggested_priority=result.priority,
        reason=result.reason,
        troubleshooting_steps=result.steps,
        model_name=ai.model,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.get("/suggestion", response_model=AISuggestionOut)
def get_latest_suggestion(ticket_id: int, db: Session = Depends(get_db)):
    _get_ticket_or_404(db, ticket_id)
    suggestion = (
        db.query(AISuggestion)
        .filter(AISuggestion.ticket_id == ticket_id)
        .order_by(AISuggestion.created_at.desc(), AISuggestion.id.desc())
        .first()
    )
    if suggestion is None:
        raise HTTPException(status_code=404, detail="No AI suggestion for this ticket yet")
    return suggestion


@router.post("/feedback", response_model=AIFeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(ticket_id: int, body: AIFeedbackIn, db: Session = Depends(get_db)):
    """Staff accept or correct the suggestion. The final values go onto the ticket
    and every change is written to ticket_activity."""
    ticket = _get_ticket_or_404(db, ticket_id)
    suggestion = db.get(AISuggestion, body.suggestion_id)
    if suggestion is None or suggestion.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Suggestion not found for this ticket")

    accepted = (body.final_category == suggestion.suggested_category
                and body.final_priority == suggestion.suggested_priority)
    feedback = AIFeedback(
        suggestion_id=suggestion.id,
        ticket_id=ticket_id,
        action="ACCEPTED" if accepted else "CORRECTED",
        is_useful=body.is_useful,
        final_category=body.final_category,
        final_priority=body.final_priority,
        staff_name=body.staff_name,
    )
    db.add(feedback)

    source = "accepted AI suggestion" if accepted else "corrected AI suggestion"
    if ticket.category != body.final_category:
        db.add(TicketActivity(
            ticket_id=ticket_id, activity_type="CATEGORY_CHANGE",
            old_value=ticket.category, new_value=body.final_category,
            note=f"Category set by staff ({source})", performed_by=body.staff_name,
        ))
        ticket.category = body.final_category
    if ticket.priority != body.final_priority:
        db.add(TicketActivity(
            ticket_id=ticket_id, activity_type="PRIORITY_CHANGE",
            old_value=ticket.priority, new_value=body.final_priority,
            note=f"Priority set by staff ({source})", performed_by=body.staff_name,
        ))
        ticket.priority = body.final_priority
    if hasattr(ticket, "updated_at"):
        ticket.updated_at = func.now()

    db.commit()
    db.refresh(feedback)
    logger.info("AI feedback ticket_id=%s action=%s useful=%s",
                ticket_id, feedback.action, feedback.is_useful)
    return feedback
