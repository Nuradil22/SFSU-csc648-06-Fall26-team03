import { useCallback, useEffect, useState } from "react";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import PortfolioReadinessNotice from "./PortfolioReadinessNotice";
import { sendMessage } from "../../services/chatService";
import {
    decideRoadmapProposal,
    getCareerChatHistory,
    getCareerReadiness,
    getRoadmapProposals,
    getToken
} from "../../lib/api";
import "./Chat.css";

const LOGIN_MESSAGE = "Please log in to chat with your career assistant.";

function proposalMessage(id, proposal) {
    return {
        id: `proposal-${id}`,
        role: "proposal",
        proposalId: id,
        proposal,
        status: "pending",
        busy: false,
        error: null
    };
}

// Career assistant backed by POST /career/chat (OpenAI, personalized from the
// user's portfolio). Roadmaps the AI generates arrive as pending proposals;
// nothing becomes the official roadmap until the user approves it.
//
// onRoadmapApproved is called after a proposal is approved so the host page
// can reload the official roadmap.
export default function ChatWindow({ onRoadmapApproved }) {
    const [messages, setMessages] = useState([
        {
            id: "welcome",
            role: "assistant",
            content:
                "Hi! I'm your career guide. Ask me about career paths, university courses, certifications, or ways to improve your portfolio. Ask for a roadmap and I'll draft one for you to approve."
        }
    ]);

    const [isLoading, setIsLoading] = useState(false);

    // {ready, missing, optional_missing} from GET /career/readiness; null
    // until loaded (or if it fails; the backend still enforces the check).
    const [readiness, setReadiness] = useState(null);
    const [readinessSettled, setReadinessSettled] = useState(false);
    const isBlocked = Boolean(readiness && !readiness.ready);

    // The welcome invites the student to chat, so it is only shown once the
    // portfolio is known to be ready (or the check could not run; logged-out
    // visitors keep the usual welcome). Prevents it flashing before the notice.
    const showWelcome = !getToken() || (readinessSettled && !isBlocked);
    const visibleMessages = showWelcome
        ? messages
        : messages.filter((m) => m.id !== "welcome");

    const refreshReadiness = useCallback(() => {
        if (!getToken()) return;

        getCareerReadiness()
            .then(setReadiness)
            .catch((error) => console.error("Portfolio readiness error:", error))
            .finally(() => setReadinessSettled(true));
    }, []);

    // Check on open, and again whenever the student returns to this tab
    // (e.g. after saving portfolio details in another tab).
    useEffect(() => {
        refreshReadiness();
        window.addEventListener("focus", refreshReadiness);
        return () => window.removeEventListener("focus", refreshReadiness);
    }, [refreshReadiness]);

    function addMessage(role, content) {
        setMessages((previous) => [
            ...previous,
            { id: crypto.randomUUID(), role, content }
        ]);
    }

    // Adds proposals, skipping any already shown (avoids duplicates when the
    // initial load and a new chat reply overlap).
    function addProposals(items) {
        setMessages((previous) => {
            const shown = new Set(previous.map((m) => m.id));
            const fresh = items.filter((m) => !shown.has(m.id));
            return fresh.length ? [...previous, ...fresh] : previous;
        });
    }

    function patchMessage(id, fields) {
        setMessages((previous) =>
            previous.map((m) => (m.id === id ? { ...m, ...fields } : m))
        );
    }

    // On open: restore the saved conversation (the same history the AI sees),
    // then show any proposals still awaiting the user's review.
    useEffect(() => {
        if (!getToken()) return;

        let active = true;

        Promise.allSettled([getCareerChatHistory(), getRoadmapProposals()])
            .then(([history, proposals]) => {
                if (!active) return;

                if (history.status === "fulfilled") {
                    const past = history.value.map((m) => ({
                        id: `history-${m.id}`,
                        role: m.role,
                        content: m.content
                    }));

                    // Keep the welcome first and anything sent since opening last.
                    setMessages((previous) => {
                        const [welcome, ...rest] = previous;
                        const shown = new Set(rest.map((m) => m.id));
                        return [welcome, ...past.filter((m) => !shown.has(m.id)), ...rest];
                    });
                } else {
                    console.error("Chat history error:", history.reason);
                }

                if (proposals.status === "fulfilled") {
                    // API returns newest first; show oldest first like a conversation.
                    addProposals(
                        [...proposals.value].reverse().map((p) => proposalMessage(p.id, p))
                    );
                } else {
                    console.error("Roadmap proposals error:", proposals.reason);
                }
            });

        return () => {
            active = false;
        };
    }, []);

    async function handleSend(content) {
        if (!content.trim() || isLoading) return;

        addMessage("user", content);

        if (!getToken()) {
            addMessage("error", LOGIN_MESSAGE);
            return;
        }

        setIsLoading(true);

        try {
            const response = await sendMessage(content);

            addMessage(
                "assistant",
                response?.reply || "I couldn't generate a response."
            );

            // A roadmap generated by the AI and validated + stored by the
            // backend as a pending proposal.
            if (response?.proposal_id && response.proposal) {
                addProposals([
                    proposalMessage(response.proposal_id, response.proposal)
                ]);
            }
        } catch (error) {
            console.error("Career assistant error:", error);

            if (error.status === 409) {
                // Portfolio incomplete: show the notice with dashboard links.
                refreshReadiness();
            } else {
                addMessage(
                    "error",
                    error.status === 401 ? LOGIN_MESSAGE : error.message
                );
            }
        } finally {
            setIsLoading(false);
        }
    }

    async function handleDecide(message, decision) {
        patchMessage(message.id, { busy: true, error: null });

        try {
            const result = await decideRoadmapProposal(message.proposalId, decision);
            patchMessage(message.id, { busy: false, status: result.status });

            if (result.status === "approved") {
                onRoadmapApproved?.();
            }
        } catch (error) {
            console.error("Roadmap decision error:", error);
            patchMessage(message.id, {
                busy: false,
                error: error.status === 401 ? LOGIN_MESSAGE : error.message
            });
        }
    }

    return (
        <div className="chat-window">
            {/* Incomplete portfolio: only the notice pointing to the existing
                dashboard options; the conversation returns once unlocked. */}
            {isBlocked ? (
                <PortfolioReadinessNotice missing={readiness.missing} />
            ) : (
                <>
                    <MessageList
                        messages={visibleMessages}
                        isLoading={isLoading}
                        onDecide={handleDecide}
                    />

                    <ChatInput
                        onSend={handleSend}
                        disabled={isLoading}
                    />
                </>
            )}
        </div>
    );
}
