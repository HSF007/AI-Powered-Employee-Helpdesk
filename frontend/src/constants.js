export const CATEGORIES = ["Hardware", "Software", "Network", "Access", "Other"];
export const PRIORITIES = ["Low", "Medium", "High"];
export const STATUSES = ["New", "In Progress", "Resolved"];

// Mirrors ALLOWED_TRANSITIONS in backend ticket_service.py.
// The UI only offers valid moves; the backend still enforces them.
export const NEXT_STATUS_ACTIONS = {
  New: [{ status: "In Progress", label: "Start work" }],
  "In Progress": [
    { status: "Resolved", label: "Mark resolved" },
    { status: "New", label: "Move back to New" },
  ],
  Resolved: [{ status: "In Progress", label: "Reopen" }],
};