import { useEffect, useState } from "react";
import { analyzeTicket, getSuggestion } from "../../api/ai";
import Badge from "../common/Badge";
import ErrorMessage from "../common/ErrorMessage";
import AIUnavailable from "./AIUnavailable";
import FeedbackForm from "./FeedbackForm";
import "./ai.css";

// Used on the support TicketProcessing page.
// staffName comes from that page's "Your name" box; onFeedback reloads the ticket.
export default function AIPanel({ ticketId, staffName, onFeedback }) {
  const [suggestion, setSuggestion] = useState(null);
  const [state, setState] = useState("loading"); // loading | empty | analyzing | ready | unavailable | error
  const [error, setError] = useState(null);

  useEffect(() => {
    // The parent gives this panel key={ticketId}, so a new ticket remounts it
    // with fresh "loading" state - no reset needed here.
    let cancelled = false;
    getSuggestion(ticketId)
      .then((s) => {
        if (cancelled) return;
        setSuggestion(s);
        setState("ready");
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 404) setState("empty");
        else {
          setError(err);
          setState("error");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [ticketId]);

  async function runAnalysis() {
    setState("analyzing");
    setError(null);
    try {
      setSuggestion(await analyzeTicket(ticketId));
      setState("ready");
    } catch (err) {
      setError(err);
      // 503 = model down / timed out / invalid answer; 0 = backend unreachable
      setState(err.status === 503 || err.status === 0 ? "unavailable" : "error");
    }
  }

  return (
    <section className="panel ai-panel">
      <div className="ai-head">
        <h2>AI suggestion</h2>
        <span className="badge ai-badge">Advisory only</span>
      </div>

      {state === "loading" && <p className="muted">Loading…</p>}

      {state === "empty" && (
        <>
          <p className="hint">
            Get a suggested category, priority and first troubleshooting steps. Nothing changes on the
            ticket until you confirm it.
          </p>
          <button type="button" className="btn btn-primary" onClick={runAnalysis}>
            Analyze with AI
          </button>
        </>
      )}

      {state === "analyzing" && (
        <p className="muted" aria-live="polite">Analyzing ticket… this can take up to a minute.</p>
      )}

      {state === "unavailable" && <AIUnavailable message={error?.message} onRetry={runAnalysis} />}

      {state === "error" && (
        <>
          <ErrorMessage error={error} />
          <button type="button" className="btn" onClick={runAnalysis}>
            Retry
          </button>
        </>
      )}

      {state === "ready" && suggestion && (
        <>
          <dl className="ai-result">
            <dt>Category</dt>
            <dd><Badge value={suggestion.suggested_category} kind="category" /></dd>
            <dt>Priority</dt>
            <dd><Badge value={suggestion.suggested_priority} kind="priority" /></dd>
            <dt>Why</dt>
            <dd>{suggestion.reason}</dd>
          </dl>
          <h3 className="ai-subhead">Suggested troubleshooting steps</h3>
          <ol className="ai-steps">
            {suggestion.troubleshooting_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
          <p className="muted ai-meta">
            Model: {suggestion.model_name} ·{" "}
            <button type="button" className="ai-link" onClick={runAnalysis}>
              Re-analyze
            </button>
          </p>
          <FeedbackForm
            key={suggestion.id}
            ticketId={ticketId}
            suggestion={suggestion}
            staffName={staffName}
            onSubmitted={onFeedback}
          />
        </>
      )}
    </section>
  );
}
