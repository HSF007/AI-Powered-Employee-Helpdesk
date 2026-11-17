const FIELD_LABELS = {
  title: "Title",
  description: "Description",
  requester_name: "Your name",
  requester_contact: "Email or employee ID",
  department: "Department",
  category: "Category",
  priority: "Priority",
  status: "Status",
  note: "Note",
  performed_by: "Your name",
  request: "Request",
};

export function fieldLabel(field) {
  return FIELD_LABELS[field] ?? field;
}

// Turns the API's fields list into { fieldName: "message" } for inline display.
export function fieldErrors(error) {
  const map = {};
  for (const f of error?.fields ?? []) {
    if (!map[f.field]) map[f.field] = f.message;
  }
  return map;
}

export default function ErrorMessage({ error, showFields = true }) {
  if (!error) return null;
  return (
    <div className="alert alert-error" role="alert">
      <strong>{error.message}</strong>
      {showFields && error.fields?.length > 0 && (
        <ul>
          {error.fields.map((f, i) => (
            <li key={i}>
              {fieldLabel(f.field)}: {f.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}