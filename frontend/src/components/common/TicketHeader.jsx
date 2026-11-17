import { formatDate } from "../../utils/format";
import Badge from "./Badge";

export default function TicketHeader({ ticket, pendingLabel = "Unassigned", actions }) {
  const r = ticket.requester;
  return (
    <header className="ticket-head">
      <div className="ticket-head-main">
        <span className="ticket-id ticket-id-lg">#{ticket.id}</span>
        <h1>{ticket.title}</h1>
        <div className="badges">
          <Badge value={ticket.status} />
          <Badge kind="category" prefix="Category" value={ticket.category} emptyLabel={pendingLabel} />
          <Badge kind="priority" prefix="Priority" value={ticket.priority} emptyLabel={pendingLabel} />
        </div>
        <p className="meta">
          Raised by {r.display_name} ({r.contact}){r.department ? `, ${r.department}` : ""} on{" "}
          {formatDate(ticket.created_at)}. Last updated {formatDate(ticket.updated_at)}.
        </p>
      </div>
      {actions && <div className="ticket-head-actions">{actions}</div>}
    </header>
  );
}