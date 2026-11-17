"""Ticket API tests: creation, invalid input, status updates.

API under test (app/routers/tickets.py, app/schemas/ticket.py):
  POST  /api/tickets                 {requester_name, requester_contact, title, description,
                                      department?, category?} -> 201
        The requester is looked up by contact, or created if new.
  GET   /api/tickets/{id}            -> 200 / 404
  GET   /api/tickets                 -> 200, list
  PATCH /api/tickets/{id}/status     {status, performed_by} -> 200
        allowed: New -> In Progress -> Resolved; skipping a step -> 400
  GET   /api/tickets/{id}/history    -> 200, list of activity rows
"""
import pytest

BASE = "/api/tickets"


def create(client, requester, **overrides):
    body = {"requester_name": requester.display_name, "requester_contact": requester.contact,
            "title": "Printer jam", "description": "Printer on floor 2 jams on every page.",
            **overrides}
    return client.post(BASE, json=body)


# ------------------------------------------------------------ creation
def test_create_ticket(client, requester):
    res = create(client, requester)
    assert res.status_code == 201, res.text
    t = res.json()
    assert t["status"] == "New"
    assert t["title"] == "Printer jam"
    assert t["category"] is None and t["priority"] is None  # set later by staff


def test_created_ticket_can_be_fetched_and_listed(client, requester):
    tid = create(client, requester).json()["id"]
    assert client.get(f"{BASE}/{tid}").status_code == 200
    assert any(t["id"] == tid for t in client.get(BASE).json())


def test_create_logs_created_activity(client, requester):
    tid = create(client, requester).json()["id"]
    history = client.get(f"{BASE}/{tid}/history").json()
    assert history[0]["activity_type"] == "CREATED"


# ------------------------------------------------------------ invalid input
@pytest.mark.parametrize("overrides", [
    {"title": ""},
    {"title": "   "},
    {"description": ""},
    {"title": "x" * 201},
])
def test_create_rejects_bad_fields(client, requester, overrides):
    assert create(client, requester, **overrides).status_code == 422


def test_create_rejects_missing_fields(client):
    assert client.post(BASE, json={"title": "only a title"}).status_code == 422


def test_create_rejects_contact_with_spaces(client, requester):
    assert create(client, requester, requester_contact="not an email").status_code == 422


def test_create_reuses_existing_requester_by_contact(client, requester):
    # Same contact in a different case -> same requester, not a duplicate
    res = create(client, requester, requester_contact=requester.contact.upper())
    assert res.status_code == 201, res.text
    assert res.json()["requester"]["id"] == requester.id


def test_get_unknown_ticket_is_404(client):
    assert client.get(f"{BASE}/999999").status_code == 404


# ------------------------------------------------------------ status update
def set_status(client, tid, status):
    return client.patch(f"{BASE}/{tid}/status", json={"status": status, "performed_by": "Asha"})


def test_status_flow_new_to_resolved(client, requester):
    tid = create(client, requester).json()["id"]
    assert set_status(client, tid, "In Progress").json()["status"] == "In Progress"
    assert set_status(client, tid, "Resolved").json()["status"] == "Resolved"

    changes = [h for h in client.get(f"{BASE}/{tid}/history").json()
               if h["activity_type"] == "STATUS_CHANGE"]
    assert [(c["old_status"], c["new_status"]) for c in changes] == [
        ("New", "In Progress"), ("In Progress", "Resolved")]


def test_status_invalid_value_is_422(client, requester):
    tid = create(client, requester).json()["id"]
    assert set_status(client, tid, "Closed").status_code == 422


def test_status_skipping_a_step_is_400(client, requester):
    tid = create(client, requester).json()["id"]
    assert set_status(client, tid, "Resolved").status_code == 400


def test_status_on_unknown_ticket_is_404(client):
    assert set_status(client, 999999, "In Progress").status_code == 404
