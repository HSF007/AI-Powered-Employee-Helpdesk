import { Link, useNavigate } from "react-router-dom";
import { formatDate } from "../../utils/format";
import Badge from "./Badge";

export default function TicketTable({ tickets, basePath, showRequester = false, emptyText = "No tickets found." }) {
  const navigate = useNavigate();

  if (!tickets?.length) return <p className="empty">{emptyText}</p>;

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            {showRequester && <th>Requester</th>}
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id} onClick={() => navigate(`${basePath}/${t.id}`)}>
              <td><span className="ticket-id">#{t.id}</span></td>
              <td>
                <Link to={`${basePath}/${t.id}`} onClick={(e) => e.stopPropagation()}>
                  {t.title}
                </Link>
              </td>
              {showRequester && (
                <td>
                  {t.requester.display_name}
                  {t.requester.department && <div className="sub">{t.requester.department}</div>}
                </td>
              )}
              <td><Badge kind="category" value={t.category} /></td>
              <td><Badge kind="priority" value={t.priority} /></td>
              <td><Badge value={t.status} /></td>
              <td className="nowrap">{formatDate(t.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}