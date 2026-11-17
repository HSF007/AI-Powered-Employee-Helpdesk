import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import ErrorMessage, { fieldErrors } from "../../components/common/ErrorMessage";
import Field from "../../components/common/Field";
import { CATEGORIES } from "../../constants";
import { useLocalStorage } from "../../utils/useLocalStorage";

export default function RaiseTicket() {
  const navigate = useNavigate();
  const [savedName, setSavedName] = useLocalStorage("helpdesk.name", "");
  const [savedContact, setSavedContact] = useLocalStorage("helpdesk.contact", "");
  const [form, setForm] = useState({
    requester_name: savedName,
    requester_contact: savedContact,
    department: "",
    title: "",
    description: "",
    category: "",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const errors = fieldErrors(error);

  const update = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      // No browser-side validation on purpose: FastAPI validates and we show its messages.
      const ticket = await api.createTicket(form);
      setSavedName(ticket.requester.display_name);
      setSavedContact(ticket.requester.contact);
      navigate(`/employee/tickets/${ticket.id}`, { state: { justCreated: true } });
    } catch (err) {
      setError(err);
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Raise a ticket</h1>
          <p>Describe the problem and IT support will pick it up. You can follow progress under My tickets.</p>
        </div>
      </div>

      <form className="panel form" onSubmit={handleSubmit} noValidate>
        <ErrorMessage error={error} showFields={false} />

        <div className="form-row">
          <Field label="Your name" error={errors.requester_name}>
            <input name="requester_name" value={form.requester_name} onChange={update} autoComplete="name" />
          </Field>
          <Field label="Email or employee ID" error={errors.requester_contact} hint="Used to find your tickets later">
            <input name="requester_contact" value={form.requester_contact} onChange={update} autoComplete="email" />
          </Field>
        </div>

        <div className="form-row">
          <Field label="Department (optional)" error={errors.department}>
            <input name="department" value={form.department} onChange={update} />
          </Field>
          <Field label="Category (optional)" error={errors.category} hint="Leave as Not sure if unclear">
            <select name="category" value={form.category} onChange={update}>
              <option value="">Not sure</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="Title" error={errors.title} hint="A short summary, e.g. Wireless keyboard not responding">
          <input name="title" value={form.title} onChange={update} />
        </Field>

        <Field
          label="Description"
          error={errors.description}
          hint={`What happened, when it started, and who is affected. ${form.description.length}/5000`}
        >
          <textarea name="description" rows={6} value={form.description} onChange={update} />
        </Field>

        <div>
          <button className="btn btn-primary" type="submit" disabled={submitting}>
            {submitting ? "Submitting…" : "Submit ticket"}
          </button>
        </div>
      </form>
    </>
  );
}