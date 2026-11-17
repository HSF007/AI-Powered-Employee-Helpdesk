import { useState } from "react";
import { api } from "../../api/client";
import { useApi } from "../../api/useApi";
import ErrorMessage from "../../components/common/ErrorMessage";
import Field from "../../components/common/Field";
import TicketTable from "../../components/common/TicketTable";
import { useLocalStorage } from "../../utils/useLocalStorage";

export default function MyTickets() {
  const [contact, setContact] = useLocalStorage("helpdesk.contact", "");
  const [draft, setDraft] = useState(contact);

  const { data: tickets, error, loading, reload } = useApi(
    () => (contact ? api.listTickets({ requester_contact: contact }) : Promise.resolve(null)),
    [contact]
  );

  function handleSubmit(e) {
    e.preventDefault();
    const value = draft.trim().toLowerCase();
    if (value === contact) reload();
    else setContact(value);
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>My tickets</h1>
          <p>Tickets you have raised, newest first. Open one to see its progress.</p>
        </div>
      </div>

      <form className="inline-form" onSubmit={handleSubmit}>
        <Field label="Email or employee ID">
          <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="priya.sharma@company.com" />
        </Field>
        <button className="btn btn-primary" type="submit">Show my tickets</button>
      </form>

      <ErrorMessage error={error} />

      {!contact ? (
        <p className="empty">Enter the email or employee ID you used when raising a ticket.</p>
      ) : loading && !tickets ? (
        <p className="muted">Loading tickets…</p>
      ) : (
        <TicketTable
          tickets={tickets}
          basePath="/employee/tickets"
          emptyText="No tickets for this contact yet. Raise one from Raise a ticket."
        />
      )}
    </>
  );
}