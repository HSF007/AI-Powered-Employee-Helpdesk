import { useState } from "react";
import { sendFeedback } from "../../api/ai";
import { CATEGORIES, PRIORITIES } from "../../constants";
import ErrorMessage from "../common/ErrorMessage";
import Field from "../common/Field";

// Staff accept the AI suggestion as-is, or change category/priority (= corrected).
// The confirmed values are written to the ticket by the backend.
export default function FeedbackForm({ ticketId, suggestion, staffName = "", onSubmitted }) {
  const [category, setCategory] = useState(suggestion.suggested_category);
  const [priority, setPriority] = useState(suggestion.suggested_priority);
  const [isUseful, setIsUseful] = useState(null);
  const [formError, setFormError] = useState("");
  const [apiError, setApiError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(null);

  const accepted =
    category === suggestion.suggested_category && priority === suggestion.suggested_priority;

  async function handleSubmit(e) {
    e.preventDefault();
    setApiError(null);
    if (staffName.trim().length < 2) return setFormError('Enter your name in the "Your name" box first.');
    if (isUseful === null) return setFormError("Please say whether the suggestion was useful.");
    setFormError("");
    setSaving(true);
    try {
      const result = await sendFeedback(ticketId, {
        suggestion_id: suggestion.id,
        is_useful: isUseful,
        final_category: category,
        final_priority: priority,
        staff_name: staffName.trim(),
      });
      setDone(result);
      onSubmitted?.(result);
    } catch (err) {
      setApiError(err);
    } finally {
      setSaving(false);
    }
  }

  if (done) {
    return (
      <p className="alert alert-ok">
        Saved: {done.action === "ACCEPTED" ? "suggestion accepted" : "suggestion corrected"} (
        {done.final_category} / {done.final_priority}).
      </p>
    );
  }

  return (
    <form className="ai-feedback stack" onSubmit={handleSubmit} noValidate>
      <h3 className="ai-subhead">Confirm or correct</h3>
      <div className="form-row">
        <Field label="Category">
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="Priority">
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </Field>
      </div>

      <fieldset className="ai-useful">
        <legend className="field-label">Was the suggestion useful?</legend>
        <label>
          <input type="radio" name={`useful-${suggestion.id}`} checked={isUseful === true} onChange={() => setIsUseful(true)} />
          Yes
        </label>
        <label>
          <input type="radio" name={`useful-${suggestion.id}`} checked={isUseful === false} onChange={() => setIsUseful(false)} />
          No
        </label>
      </fieldset>

      {formError && <p className="alert alert-error">{formError}</p>}
      <ErrorMessage error={apiError} />
      <div>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? "Saving…" : accepted ? "Accept suggestion" : "Save correction"}
        </button>
      </div>
    </form>
  );
}
