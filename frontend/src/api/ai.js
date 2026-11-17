// AI API calls. They live in client.js with the other endpoints (same proxy and
// error handling); this file just re-exports them for the AI components.
import { api } from "./client";

export { ApiError } from "./client";

export const analyzeTicket = api.analyzeTicket;
export const getSuggestion = api.getSuggestion;
export const sendFeedback = api.sendFeedback;
