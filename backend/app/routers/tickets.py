"""Ticket CRUD, support workflow, and history endpoints."""
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.activity import ActivityOut, CommentCreate
from app.schemas.ticket import (
    Category, Priority, Status, StatusUpdate,
    TicketCreate, TicketDetailOut, TicketOut, TicketUpdate,
)
from app.services import ticket_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

NOT_FOUND = {404: {"description": "Ticket not found"}}
TicketId = Path(gt=0, description="Ticket ID")


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED,
             summary="Raise a new ticket (employee)")
def create_ticket(data: TicketCreate, db: Session = Depends(get_db)):
    return ticket_service.create_ticket(db, data)


@router.get("", response_model=list[TicketOut],
            summary="List tickets (work queue / my tickets)")
def list_tickets(
    status_: Status | None = Query(None, alias="status"),
    category: Category | None = None,
    priority: Priority | None = None,
    requester_contact: str | None = Query(None, description="Filter to one employee's tickets"),
    db: Session = Depends(get_db),
):
    return ticket_service.list_tickets(
        db, status=status_, category=category, priority=priority, requester_contact=requester_contact
    )


@router.get("/{ticket_id}", response_model=TicketDetailOut, responses=NOT_FOUND,
            summary="Get one ticket with its history")
def get_ticket(ticket_id: int = TicketId, db: Session = Depends(get_db)):
    return ticket_service.get_ticket(db, ticket_id, with_history=True)


@router.patch("/{ticket_id}", response_model=TicketOut, responses=NOT_FOUND,
              summary="Confirm/update category and priority (support staff)")
def update_ticket(data: TicketUpdate, ticket_id: int = TicketId, db: Session = Depends(get_db)):
    return ticket_service.update_ticket_fields(db, ticket_id, data)


@router.patch("/{ticket_id}/status", response_model=TicketOut,
              responses={**NOT_FOUND, 400: {"description": "Invalid status transition"}},
              summary="Change ticket status (support staff)")
def change_status(data: StatusUpdate, ticket_id: int = TicketId, db: Session = Depends(get_db)):
    return ticket_service.change_status(db, ticket_id, data)


@router.post("/{ticket_id}/comments", response_model=ActivityOut,
             status_code=status.HTTP_201_CREATED, responses=NOT_FOUND,
             summary="Add a support comment")
def add_comment(data: CommentCreate, ticket_id: int = TicketId, db: Session = Depends(get_db)):
    return ticket_service.add_comment(db, ticket_id, data)


@router.get("/{ticket_id}/history", response_model=list[ActivityOut], responses=NOT_FOUND,
            summary="Full activity history of a ticket")
def get_history(ticket_id: int = TicketId, db: Session = Depends(get_db)):
    return ticket_service.get_history(db, ticket_id)