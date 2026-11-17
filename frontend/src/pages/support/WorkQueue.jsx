import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { useApi } from "../../api/useApi";
import ErrorMessage from "../../components/common/ErrorMessage";
import Field from "../../components/common/Field";
import TicketTable from "../../components/common/TicketTable";
import { CATEGORIES, PRIORITIES, STATUSES } from "../../constants";

export default function WorkQueue() {
  // Filters live in the URL, so dashboard links work and a refresh keeps them
  const [params, setParams] = useSearchParams();
  const filters = {
    status: params.get("status") ?? "",
    category: params.get("category") ?? "",
    priority: params.get("priority") ?? "",
  };

  const { data: tickets, error, loading, reload } = useApi(
    () => api.listTickets(filters),
    [filters.status, filters.category, filters.priority]
  );

  function setFilter(name, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    setParams(next);
  }

  const hasFilters = filters.status || filters.category || filters.priority;

  const select = (name, label, options) => (
    <Field label={label}>
      <select value={filters[name]} onChange={(e) => setFilter(name, e.target.value)}>
        <option value="">Any</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </Field>
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Work queue</h1>
          <p>All tickets, newest first. Open one to set priority, add notes and change its status.</p>
        </div>
        <button className="btn" onClick={reload}>Refresh</button>
      </div>

      <div className="filters">
        {select("status", "Status", STATUSES)}
        {select("category", "Category", CATEGORIES)}
        {select("priority", "Priority", PRIORITIES)}
        {hasFilters && (
          <button className="btn" onClick={() => setParams({})}>Clear filters</button>
        )}
      </div>

      <ErrorMessage error={error} />

      {loading && !tickets ? (
        <p className="muted">Loading tickets…</p>
      ) : (
        <>
          {tickets && <p className="result-count">{tickets.length} ticket{tickets.length === 1 ? "" : "s"}</p>}
          <TicketTable
            tickets={tickets}
            basePath="/support/tickets"
            showRequester
            emptyText={hasFilters ? "No tickets match these filters." : "No tickets yet."}
          />
        </>
      )}
    </>
  );
}