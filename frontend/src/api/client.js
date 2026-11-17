// All backend calls live here. Paths are relative; Vite proxies /api to FastAPI.
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.message ?? `Request failed (HTTP ${status})`);
    this.name = "ApiError";
    this.status = status;
    this.code = body?.error ?? "unknown_error";
    this.fields = Array.isArray(body?.fields) ? body.fields : [];
  }
}

async function request(path, { method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(BASE_URL + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, {
      error: "network_error",
      message: "Cannot reach the server. Check that the backend is running.",
    });
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (!data && response.status >= 500) {
      throw new ApiError(response.status, {
        error: "server_unreachable",
        message: "The backend is not responding. Check that it is running on port 8000.",
      });
    }
    throw new ApiError(response.status, data);
  }
  return data;
}

function query(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) search.append(key, value);
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  // Tickets
  createTicket: (data) => request("/api/tickets", { method: "POST", body: data }),
  listTickets: (filters = {}) => request(`/api/tickets${query(filters)}`),
  getTicket: (id) => request(`/api/tickets/${id}`),
  updateTicket: (id, data) => request(`/api/tickets/${id}`, { method: "PATCH", body: data }),
  changeStatus: (id, data) => request(`/api/tickets/${id}/status`, { method: "PATCH", body: data }),
  addComment: (id, data) => request(`/api/tickets/${id}/comments`, { method: "POST", body: data }),
  getHistory: (id) => request(`/api/tickets/${id}/history`),

  // Dashboard
  getSummary: () => request("/api/summary"),

  // AI (advisory only - staff confirm or correct via feedback)
  analyzeTicket: (id) => request(`/api/tickets/${id}/ai/analyze`, { method: "POST" }),
  getSuggestion: (id) => request(`/api/tickets/${id}/ai/suggestion`),
  sendFeedback: (id, data) => request(`/api/tickets/${id}/ai/feedback`, { method: "POST", body: data }),
};