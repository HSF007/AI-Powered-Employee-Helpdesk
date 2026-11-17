"""Ticket business logic: creation, transition rules, activity log, summary.

Routers stay thin; every rule lives here so it's testable without HTTP.
Logging rule: ticket IDs and field names only - never titles/descriptions.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.core.errors import InvalidTransitionError, NotFoundError
from app.core.logging import get_logger
from app.db.models import CATEGORIES, PRIORITIES, STATUSES, Requester, Ticket, TicketActivity
from app.schemas.activity import CommentCreate
from app.schemas.ticket import StatusUpdate, TicketCreate, TicketUpdate

logger = get_logger("tickets")

# Allowed status moves. Anything else -> 400 invalid_transition.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "New": {"In Progress"},
    "In Progress": {"Resolved", "New"},
    "Resolved": {"In Progress"},  # re-open
}


def _log_activity(db: Session, ticket: Ticket, activity_type: str, performed_by: str, **fields) -> TicketActivity:
    activity = TicketActivity(
        ticket_id=ticket.id, activity_type=activity_type, performed_by=performed_by, **fields
    )
    db.add(activity)
    return activity


# ---------------- Reads ----------------
def get_ticket(db: Session, ticket_id: int, *, with_history: bool = False) -> Ticket:
    stmt = select(Ticket).options(joinedload(Ticket.requester)).where(Ticket.id == ticket_id)
    if with_history:
        stmt = stmt.options(selectinload(Ticket.activities))
    ticket = db.scalars(stmt).first()
    if ticket is None:
        raise NotFoundError(f"Ticket {ticket_id} not found.")
    return ticket


def list_tickets(
    db: Session,
    *,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    requester_contact: str | None = None,
) -> list[Ticket]:
    # Explicit JOIN tickets -> requesters (also lets us filter by contact)
    stmt = select(Ticket).join(Ticket.requester).options(contains_eager(Ticket.requester))
    if status:
        stmt = stmt.where(Ticket.status == status)
    if category:
        stmt = stmt.where(Ticket.category == category)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if requester_contact:
        stmt = stmt.where(Requester.contact == requester_contact.strip().lower())
    stmt = stmt.order_by(Ticket.created_at.desc(), Ticket.id.desc())
    return list(db.scalars(stmt))


def get_history(db: Session, ticket_id: int) -> list[TicketActivity]:
    get_ticket(db, ticket_id)  # 404 if missing
    stmt = (
        select(TicketActivity)
        .where(TicketActivity.ticket_id == ticket_id)
        .order_by(TicketActivity.created_at, TicketActivity.id)
    )
    return list(db.scalars(stmt))


# ---------------- Writes ----------------
def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    requester = db.scalars(select(Requester).where(Requester.contact == data.requester_contact)).first()
    if requester is None:
        requester = Requester(
            display_name=data.requester_name,
            contact=data.requester_contact,
            department=data.department,
        )
        db.add(requester)
        db.flush()  # get requester.id

    ticket = Ticket(
        requester_id=requester.id,
        title=data.title,
        description=data.description,
        category=data.category,
        status="New",
    )
    db.add(ticket)
    db.flush()  # get ticket.id

    _log_activity(db, ticket, "CREATED", requester.display_name, new_status="New", note="Ticket created")
    db.commit()

    logger.info("Ticket %s created (requester_id=%s)", ticket.id, requester.id)
    return get_ticket(db, ticket.id)


def update_ticket_fields(db: Session, ticket_id: int, data: TicketUpdate) -> Ticket:
    ticket = get_ticket(db, ticket_id)
    changed: list[str] = []

    if data.category is not None and data.category != ticket.category:
        _log_activity(db, ticket, "CATEGORY_CHANGE", data.performed_by,
                      old_value=ticket.category, new_value=data.category)
        ticket.category = data.category
        changed.append("category")

    if data.priority is not None and data.priority != ticket.priority:
        _log_activity(db, ticket, "PRIORITY_CHANGE", data.performed_by,
                      old_value=ticket.priority, new_value=data.priority)
        ticket.priority = data.priority
        changed.append("priority")

    if changed:
        db.commit()
        db.refresh(ticket)
        logger.info("Ticket %s updated: %s", ticket.id, ", ".join(changed))
    return ticket


def change_status(db: Session, ticket_id: int, data: StatusUpdate) -> Ticket:
    ticket = get_ticket(db, ticket_id)
    old = ticket.status

    if data.status == old:
        raise InvalidTransitionError(f"Ticket {ticket_id} is already '{old}'.")
    allowed = ALLOWED_TRANSITIONS.get(old, set())
    if data.status not in allowed:
        raise InvalidTransitionError(
            f"Cannot move a ticket from '{old}' to '{data.status}'. "
            f"Allowed next status: {', '.join(sorted(allowed))}."
        )

    _log_activity(db, ticket, "STATUS_CHANGE", data.performed_by,
                  old_status=old, new_status=data.status, note=data.note)
    ticket.status = data.status
    db.commit()
    db.refresh(ticket)

    logger.info("Ticket %s status %s -> %s", ticket.id, old, data.status)
    return ticket


def add_comment(db: Session, ticket_id: int, data: CommentCreate) -> TicketActivity:
    ticket = get_ticket(db, ticket_id)
    activity = _log_activity(db, ticket, "COMMENT", data.performed_by, note=data.note)
    db.commit()
    db.refresh(activity)
    logger.info("Ticket %s comment added (activity_id=%s)", ticket.id, activity.id)
    return activity


# ---------------- Dashboard ----------------
def get_summary(db: Session) -> dict:
    def grouped(column, keys, none_label="Unassigned") -> dict[str, int]:
        rows = db.execute(select(column, func.count(Ticket.id)).group_by(column)).all()
        counts = {k: 0 for k in keys}
        for value, count in rows:
            counts[value if value is not None else none_label] = count
        return counts

    return {
        "total": db.scalar(select(func.count(Ticket.id))) or 0,
        "by_status": grouped(Ticket.status, STATUSES),
        "by_priority": grouped(Ticket.priority, PRIORITIES),
        "by_category": grouped(Ticket.category, CATEGORIES),
    }