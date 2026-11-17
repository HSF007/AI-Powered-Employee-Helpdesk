"""Dashboard counts."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ticket import SummaryOut
from app.services import ticket_service

router = APIRouter(prefix="/api/summary", tags=["dashboard"])


@router.get("", response_model=SummaryOut, summary="Ticket counts by status, priority and category")
def get_summary(db: Session = Depends(get_db)):
    return ticket_service.get_summary(db)