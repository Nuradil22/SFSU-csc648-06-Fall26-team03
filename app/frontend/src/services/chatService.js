import { sendCareerMessage } from "../lib/api";

// The career assistant is served by the authenticated FastAPI route
// POST /career/chat (OpenAI-backed, personalized from the user's portfolio).
// Resolves to {reply, provider, proposal_id, proposal}; rejected errors carry
// .status (e.g. 401 when the user is not logged in).
export function sendMessage(message) {
    return sendCareerMessage(message);
}
