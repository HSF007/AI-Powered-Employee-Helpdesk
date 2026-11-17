// Shown when Ollama is down, times out, or gives an invalid answer.
// The ticket is still fully usable - staff triage it by hand.
export default function AIUnavailable({ message, onRetry }) {
  return (
    <div className="alert ai-unavailable" role="alert">
      <strong>AI assistant unavailable</strong>
      <p>{message || "The AI assistant could not be reached."}</p>
      <p className="ai-unavailable-hint">
        You can still set the category and priority yourself and work on this ticket as normal.
      </p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
