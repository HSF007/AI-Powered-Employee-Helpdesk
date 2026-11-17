import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { useApi } from "../../api/useApi";
import AIPanel from "../../components/ai/AIPanel";
import Badge from "../../components/common/Badge";
import ErrorMessage, { fieldErrors } from "../../components/common/ErrorMessage";
import Field from "../../components/common/Field";
import TicketHeader from "../../components/common/TicketHeader";
import Timeline from "../../components/common/Timeline";
import { CATEGORIES, NEXT_STATUS_ACTIONS, PRIORITIES } from "../../constants";
import { useLocalStorage } from "../../utils/useLocalStorage";

export default function TicketProcessing() {
  const { id } = useParams();
  const { data: ticket, error: loadError, loading, setData } = useApi(() => api.getTicket(id), [id]);

  const [staffName, setStaffName] = useLocalStorage("helpdesk.staffName", "");
  const [fields, setFields] = useState({ category: "", priority: "" });
  const [statusNote, setStatusNote] = useState("");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(null);       // which action is running
  const [failure, setFailure] = useState(null); // { action, error }
  const [notice, setNotice] = useState(null);   // { action, text }

  // Keep the form in sync with the confirmed values from the server
  useEffect(() => {
    if (ticket) setFields({ category: ticket.category ?? "", priority: ticket.priority ?? "" });
  }, [ticket]);

  // Runs one action, then reloads the ticket so history and badges update
  async function run(action, request, successText) {
    setBusy(action);
    setFailure(null);
    setNotice(null);
    try {
      await request();
      setData(await api.getTicket(id));
      setNotice({ action, text: successText });
      return true;
    } catch (error) {
      setFailure({ action, error });
      return false;
    } finally {
      setBusy(null);
    }
  }

  const errorFor = (action) => (failure?.action === action ? failure.error : null);
  const noticeFor = (action) =>
    notice?.action === action ? <p className="alert alert-ok">{notice.text}</p> : null;
  const staffError = fieldErrors(failure?.error).performed_by;

  function saveFields(e) {
    e.preventDefault();
    run(
      "fields",
      () =>
        api.updateTicket(id, {
          category: fields.category || null,
          priority: fields.priority || null,
          performed_by: staffName,
        }),
      "Category and priority saved."
    );
  }

  async function changeStatus(next) {
    const ok = await run(
      "status",
      () => api.changeStatus(id, { status: next, performed_by: staffName, note: statusNote || null }),
      `Status changed to ${next}.`
    );
    if (ok) setStatusNote("");
  }

  async function addComment(e) {
    e.preventDefault();
    const ok = await run(
      "comment",
      () => api.addComment(id, { note: comment, performed_by: staffName }),
      "Comment added."
    );
    if (ok) setComment("");
  }

  if (loading && !ticket) return <p className="muted">Loading ticket…</p>;
  if (loadError && !ticket) {
    return (
      <>
        <ErrorMessage error={loadError} />
        <Link to="/support/queue">Back to work queue</Link>
      </>
    );
  }

  const nextActions = NEXT_STATUS_ACTIONS[ticket.status] ?? [];

  return (
    <>
      <Link className="back" to="/support/queue">Back to work queue</Link>
      <TicketHeader ticket={ticket} />

      <div className="layout-process">
        <div className="stack">
          <section className="panel">
            <h2>Description</h2>
            <p className="description">{ticket.description}</p>
          </section>

          <AIPanel
            key={ticket.id}
            ticketId={ticket.id}
            staffName={staffName}
            onFeedback={async () => setData(await api.getTicket(id))}
          />

          <section className="panel">
            <h2>History</h2>
            <Timeline activities={ticket.activities} />
          </section>
        </div>

        <aside className="stack">
          <section className="panel">
            <Field label="Your name" error={staffError} hint="Recorded on every change you make">
              <input value={staffName} onChange={(e) => setStaffName(e.target.value)} placeholder="Ravi Kumar (IT)" />
            </Field>
          </section>

          <section className="panel">
            <h2>Status</h2>
            <p>Currently <Badge value={ticket.status} /></p>
            <div style={{ marginTop: 12 }}>
              <Field label="Note (optional)">
                <textarea rows={2} value={statusNote} onChange={(e) => setStatusNote(e.target.value)} />
              </Field>
            </div>
            <div className="btn-row">
              {nextActions.map((a) => (
                <button
                  key={a.status}
                  className={a.status === "Resolved" ? "btn btn-primary" : "btn"}
                  disabled={busy !== null}
                  onClick={() => changeStatus(a.status)}
                >
                  {busy === "status" ? "Saving…" : a.label}
                </button>
              ))}
            </div>
            <ErrorMessage error={errorFor("status")} />
            {noticeFor("status")}
          </section>

          <section className="panel">
            <h2>Category and priority</h2>
            <p className="hint">The confirmed values the support team works from.</p>
            <form className="stack" onSubmit={saveFields} noValidate>
              <Field label="Category">
                <select value={fields.category} onChange={(e) => setFields((f) => ({ ...f, category: e.target.value }))}>
                  <option value="">Not set</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
              <Field label="Priority">
                <select value={fields.priority} onChange={(e) => setFields((f) => ({ ...f, priority: e.target.value }))}>
                  <option value="">Not set</option>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </Field>
              <div>
                <button className="btn btn-primary" type="submit" disabled={busy !== null}>
                  {busy === "fields" ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
            <ErrorMessage error={errorFor("fields")} />
            {noticeFor("fields")}
          </section>

          <section className="panel">
            <h2>Add a comment</h2>
            <form className="stack" onSubmit={addComment} noValidate>
              <Field label="Comment" error={fieldErrors(errorFor("comment")).note}>
                <textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
              </Field>
              <div>
                <button className="btn" type="submit" disabled={busy !== null}>
                  {busy === "comment" ? "Adding…" : "Add comment"}
                </button>
              </div>
            </form>
            <ErrorMessage error={errorFor("comment")} showFields={false} />
            {noticeFor("comment")}
          </section>
        </aside>
      </div>
    </>
  );
}