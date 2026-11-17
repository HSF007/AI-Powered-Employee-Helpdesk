import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { useApi } from "../../api/useApi";
import ErrorMessage from "../../components/common/ErrorMessage";
import { CATEGORIES, PRIORITIES, STATUSES } from "../../constants";
import { slug } from "../../utils/format";

function BarList({ counts, order, filterKey }) {
  const max = Math.max(1, ...Object.values(counts));
  return (
    <ul className="bars">
      {order.map((key) => {
        const count = counts[key] ?? 0;
        const label = key === "Unassigned" ? "Not yet confirmed" : key;
        const content = (
          <>
            <span>{label}</span>
            <span className="bar-track">
              <span className={`bar-fill bar-${slug(key)}`} style={{ width: `${(count / max) * 100}%` }} />
            </span>
            <span className="bar-count">{count}</span>
          </>
        );
        return (
          <li key={key}>
            {key === "Unassigned" ? (
              <div className="bar-row">{content}</div>
            ) : (
              <Link className="bar-row" to={`/support/queue?${filterKey}=${encodeURIComponent(key)}`}>
                {content}
              </Link>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default function Dashboard() {
  const { data, error, loading, reload } = useApi(() => api.getSummary(), []);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Support dashboard</h1>
          <p>Live ticket counts. Select a number to open the matching tickets in the work queue.</p>
        </div>
        <button className="btn" onClick={reload}>Refresh</button>
      </div>

      <ErrorMessage error={error} />
      {loading && !data && <p className="muted">Loading counts…</p>}

      {data && (
        <>
          <div className="stat-row">
            <Link to="/support/queue" className="stat">
              <span className="stat-value">{data.total}</span>
              <span className="stat-label">All tickets</span>
            </Link>
            {STATUSES.map((s) => (
              <Link key={s} to={`/support/queue?status=${encodeURIComponent(s)}`} className={`stat stat-${slug(s)}`}>
                <span className="stat-value">{data.by_status[s] ?? 0}</span>
                <span className="stat-label">{s}</span>
              </Link>
            ))}
          </div>

          <div className="layout-2">
            <section className="panel">
              <h2>By priority</h2>
              <BarList counts={data.by_priority} order={[...PRIORITIES].reverse().concat("Unassigned")} filterKey="priority" />
            </section>
            <section className="panel">
              <h2>By category</h2>
              <BarList counts={data.by_category} order={[...CATEGORIES, "Unassigned"]} filterKey="category" />
            </section>
          </div>
        </>
      )}
    </>
  );
}