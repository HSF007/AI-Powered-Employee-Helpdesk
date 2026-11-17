import { Link, useLocation, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { useApi } from "../../api/useApi";
import ErrorMessage from "../../components/common/ErrorMessage";
import TicketHeader from "../../components/common/TicketHeader";
import Timeline from "../../components/common/Timeline";

export default function TicketDetails() {
  const { id } = useParams();
  const location = useLocation();
  const { data: ticket, error, loading, reload } = useApi(() => api.getTicket(id), [id]);

  if (loading && !ticket) return <p className="muted">Loading ticket…</p>;
  if (error && !ticket) {
    return (
      <>
        <ErrorMessage error={error} />
        <Link to="/employee/tickets">Back to my tickets</Link>
      </>
    );
  }

  return (
    <>
      <Link className="back" to="/employee/tickets">Back to my tickets</Link>

      {location.state?.justCreated && (
        <div className="alert alert-ok">Ticket submitted. IT support will review it shortly.</div>
      )}
      <ErrorMessage error={error} />

      <TicketHeader
        ticket={ticket}
        pendingLabel="Awaiting review"
        actions={<button className="btn" onClick={reload}>Refresh</button>}
      />

      <div className="stack">
        <section className="panel">
          <h2>Description</h2>
          <p className="description">{ticket.description}</p>
        </section>
        <section className="panel">
          <h2>Progress and comments</h2>
          <Timeline activities={ticket.activities} />
        </section>
      </div>
    </>
  );
}