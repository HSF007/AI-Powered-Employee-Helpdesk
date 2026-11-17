import { formatDate } from "../../utils/format";

function describe(a) {
  switch (a.activity_type) {
    case "CREATED":
      return "Ticket created";
    case "STATUS_CHANGE":
      return `Status changed from ${a.old_status} to ${a.new_status}`;
    case "PRIORITY_CHANGE":
      return `Priority set to ${a.new_value}${a.old_value ? ` (was ${a.old_value})` : ""}`;
    case "CATEGORY_CHANGE":
      return `Category set to ${a.new_value}${a.old_value ? ` (was ${a.old_value})` : ""}`;
    case "COMMENT":
      return "Support comment";
    default:
      return a.activity_type;
  }
}

export default function Timeline({ activities }) {
  if (!activities?.length) return <p className="muted">No activity yet.</p>;

  return (
    <ol className="timeline">
      {activities.map((a) => (
        <li key={a.id} className={`timeline-item t-${a.activity_type.toLowerCase()}`}>
          <div className="timeline-head">
            <span className="timeline-title">{describe(a)}</span>
            <time dateTime={a.created_at}>{formatDate(a.created_at)}</time>
          </div>
          {a.note && a.activity_type !== "CREATED" && <p className="timeline-note">{a.note}</p>}
          <span className="timeline-by">by {a.performed_by}</span>
        </li>
      ))}
    </ol>
  );
}