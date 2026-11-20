import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatWindow from "./ChatWindow";

const LOGIN_MESSAGE =
    "Please log in to chat with your career assistant.";

const {
    mockSendMessage,
    mockDecideRoadmapProposal,
    mockGetRoadmapProposals,
    mockGetCareerReadiness,
    mockGetCareerChatHistory,
    mockGenerateAutoRoadmap,
    mockCompareCareerModels,
    mockGetToken,
    mockRandomUUID
} = vi.hoisted(() => ({
    mockSendMessage: vi.fn(),
    mockDecideRoadmapProposal: vi.fn(),
    mockGetRoadmapProposals: vi.fn(),
    mockGetCareerReadiness: vi.fn(),
    mockGetCareerChatHistory: vi.fn(),
    mockGenerateAutoRoadmap: vi.fn(),
    mockCompareCareerModels: vi.fn(),
    mockGetToken: vi.fn(),
    mockRandomUUID: vi.fn()
}));

vi.mock("../../services/chatService", () => ({
    sendMessage: mockSendMessage
}));

vi.mock("../../lib/api", () => ({
    compareCareerModels: mockCompareCareerModels,
    decideRoadmapProposal: mockDecideRoadmapProposal,
    generateAutoRoadmap: mockGenerateAutoRoadmap,
    getCareerChatHistory: mockGetCareerChatHistory,
    getCareerReadiness: mockGetCareerReadiness,
    getRoadmapProposals: mockGetRoadmapProposals,
    getToken: mockGetToken
}));

vi.mock("./ChatInput", () => ({
    default: ({ onSend, disabled }) => (
        <div data-testid="chat-input">
            <button
                type="button"
                onClick={() => onSend("Help me plan my career")}
                disabled={disabled}
            >
                Send test message
            </button>

            <button
                type="button"
                onClick={() => onSend("   ")}
                disabled={disabled}
            >
                Send empty message
            </button>
        </div>
    )
}));

vi.mock("./MessageList", () => ({
    default: ({ messages, isLoading, onDecide }) => (
        <div data-testid="message-list">
            <span data-testid="loading">
                {String(isLoading)}
            </span>

            {messages.map((message) => (
                <div
                    key={message.id}
                    data-testid={`message-${message.id}`}
                >
                    {message.content && (
                        <span
                            data-testid={`message-${message.role}-content`}
                        >
                            {message.content}
                        </span>
                    )}

                    {message.role === "proposal" && (
                        <>
                            <span data-testid="proposal-content">
                                {JSON.stringify(message.proposal)}
                            </span>

                            {message.error && (
                                <span data-testid="proposal-error">
                                    {message.error}
                                </span>
                            )}

                            <button
                                type="button"
                                onClick={() =>
                                    onDecide(message, "approve")
                                }
                            >
                                Approve proposal
                            </button>

                            <button
                                type="button"
                                onClick={() =>
                                    onDecide(message, "reject")
                                }
                            >
                                Reject proposal
                            </button>
                        </>
                    )}
                </div>
            ))}
        </div>
    )
}));

function renderChat(props = {}) {
    return render(
        <ChatWindow
            onRoadmapApproved={vi.fn()}
            {...props}
        />
    );
}

let messageId;

beforeEach(() => {
    messageId = 0;

    mockRandomUUID.mockImplementation(
        () => `generated-message-${++messageId}`
    );

    mockGetToken.mockReturnValue(null);

    mockGetCareerReadiness.mockResolvedValue({
        ready: true,
        missing: [],
        optional_missing: []
    });

    mockGetCareerChatHistory.mockResolvedValue([]);

    mockGetRoadmapProposals.mockResolvedValue([]);

    mockGenerateAutoRoadmap.mockResolvedValue({
        status: "approved",
        portfolio_changed: false
    });

    mockCompareCareerModels.mockResolvedValue({
        models: []
    });

    mockSendMessage.mockResolvedValue({
        reply: "Here is some career advice."
    });

    mockDecideRoadmapProposal.mockResolvedValue({
        status: "approved"
    });

    vi.stubGlobal("crypto", {
        randomUUID: mockRandomUUID
    });

    vi.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
});

describe("ChatWindow", () => {
    it("renders the welcome message", () => {
        renderChat();

        expect(
            screen.getByTestId("message-assistant-content")
        ).toHaveTextContent(
            "Hi! I'm your career guide."
        );
    });

    it("renders the chat input", () => {
        renderChat();

        expect(
            screen.getByTestId("chat-input")
        ).toBeInTheDocument();
    });

    it("does not load proposals when the user is logged out", () => {
        renderChat();

        expect(mockGetToken).toHaveBeenCalled();
        expect(mockGetRoadmapProposals).not.toHaveBeenCalled();
    });

    it("loads pending proposals for a logged-in user", async () => {
        mockGetToken.mockReturnValue("test-token");

        mockGetRoadmapProposals.mockResolvedValue([
            {
                id: "newer-proposal",
                title: "Newer roadmap"
            },
            {
                id: "older-proposal",
                title: "Older roadmap"
            }
        ]);

        renderChat();

        await waitFor(() => {
            expect(
                screen.getByTestId(
                    "message-proposal-older-proposal"
                )
            ).toBeInTheDocument();
        });

        expect(
            screen.getByTestId(
                "message-proposal-newer-proposal"
            )
        ).toBeInTheDocument();

        const messageList = screen.getByTestId("message-list");
        const proposalMessages = [
            ...messageList.querySelectorAll(
                '[data-testid^="message-proposal-"]'
            )
        ];

        expect(proposalMessages[0]).toHaveAttribute(
            "data-testid",
            "message-proposal-older-proposal"
        );

        expect(proposalMessages[1]).toHaveAttribute(
            "data-testid",
            "message-proposal-newer-proposal"
        );
    });

    it("adds a login error when an unauthenticated user sends a message", async () => {
        const user = userEvent.setup();

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        expect(
            screen.getByTestId("message-user-content")
        ).toHaveTextContent("Help me plan my career");

        expect(
            screen.getByTestId("message-error-content")
        ).toHaveTextContent(LOGIN_MESSAGE);

        expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it("ignores whitespace-only messages", async () => {
        const user = userEvent.setup();

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send empty message"
            })
        );

        expect(mockSendMessage).not.toHaveBeenCalled();
        expect(
            screen.queryByTestId("message-error-content")
        ).not.toBeInTheDocument();
    });

    it("sends a message and displays the assistant reply", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        await waitFor(() => {
            expect(mockSendMessage).toHaveBeenCalledWith(
                "Help me plan my career"
            );
        });

        const assistantMessages = screen.getAllByTestId(
            "message-assistant-content"
        );

        expect(assistantMessages).toHaveLength(2);
        expect(assistantMessages[1]).toHaveTextContent(
            "Here is some career advice."
        );
    });

    it("uses a fallback when the response has no reply", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");
        mockSendMessage.mockResolvedValue({});

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        await waitFor(() => {
            const assistantMessages = screen.getAllByTestId(
                "message-assistant-content"
            );

            expect(assistantMessages[1]).toHaveTextContent(
                "I couldn't generate a response."
            );
        });
    });

    it("adds a proposal from the assistant response", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");

        mockSendMessage.mockResolvedValue({
            reply: "I drafted a roadmap for you.",
            proposal_id: "proposal-123",
            proposal: {
                title: "Software Engineering Roadmap"
            }
        });

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        const proposal = await screen.findByTestId(
            "message-proposal-proposal-123"
        );

        expect(proposal).toHaveTextContent(
            "Software Engineering Roadmap"
        );
    });

    it("shows the login message for a 401 chat error", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");

        const error = new Error("Unauthorized");
        error.status = 401;

        mockSendMessage.mockRejectedValue(error);

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        expect(
            await screen.findByTestId("message-error-content")
        ).toHaveTextContent(LOGIN_MESSAGE);
    });

    it("shows the original message for other chat errors", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");
        mockSendMessage.mockRejectedValue(
            new Error("Service unavailable")
        );

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        expect(
            await screen.findByTestId("message-error-content")
        ).toHaveTextContent("Service unavailable");
    });

    it("disables the input while a message is sending", async () => {
        const user = userEvent.setup();
        let resolveRequest;

        mockGetToken.mockReturnValue("test-token");

        mockSendMessage.mockImplementation(
            () =>
                new Promise((resolve) => {
                    resolveRequest = resolve;
                })
        );

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        expect(
            screen.getByRole("button", {
                name: "Send test message"
            })
        ).toBeDisabled();

        expect(
            screen.getByTestId("loading")
        ).toHaveTextContent("true");

        resolveRequest({
            reply: "Finished."
        });

        await waitFor(() => {
            expect(
                screen.getByRole("button", {
                    name: "Send test message"
                })
            ).not.toBeDisabled();
        });

        expect(
            screen.getByTestId("loading")
        ).toHaveTextContent("false");
    });

    it("approves a proposal and calls onRoadmapApproved", async () => {
        const user = userEvent.setup();
        const onRoadmapApproved = vi.fn();

        mockGetToken.mockReturnValue("test-token");

        mockSendMessage.mockResolvedValue({
            reply: "Here is your roadmap.",
            proposal_id: "proposal-123",
            proposal: {
                title: "Career roadmap"
            }
        });

        renderChat({ onRoadmapApproved });

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        await user.click(
            await screen.findByRole("button", {
                name: "Approve proposal"
            })
        );

        await waitFor(() => {
            expect(
                mockDecideRoadmapProposal
            ).toHaveBeenCalledWith(
                "proposal-123",
                "approve"
            );
        });

        expect(onRoadmapApproved).toHaveBeenCalledTimes(1);
    });

    it("does not call onRoadmapApproved when a proposal is rejected", async () => {
        const user = userEvent.setup();
        const onRoadmapApproved = vi.fn();

        mockGetToken.mockReturnValue("test-token");

        mockSendMessage.mockResolvedValue({
            reply: "Here is your roadmap.",
            proposal_id: "proposal-123",
            proposal: {
                title: "Career roadmap"
            }
        });

        mockDecideRoadmapProposal.mockResolvedValue({
            status: "rejected"
        });

        renderChat({ onRoadmapApproved });

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        await user.click(
            await screen.findByRole("button", {
                name: "Reject proposal"
            })
        );

        await waitFor(() => {
            expect(
                mockDecideRoadmapProposal
            ).toHaveBeenCalledWith(
                "proposal-123",
                "reject"
            );
        });

        expect(onRoadmapApproved).not.toHaveBeenCalled();
    });

    it("shows an error when deciding a proposal fails", async () => {
        const user = userEvent.setup();

        mockGetToken.mockReturnValue("test-token");

        mockSendMessage.mockResolvedValue({
            reply: "Here is your roadmap.",
            proposal_id: "proposal-123",
            proposal: {
                title: "Career roadmap"
            }
        });

        mockDecideRoadmapProposal.mockRejectedValue(
            new Error("Could not update roadmap")
        );

        renderChat();

        await user.click(
            screen.getByRole("button", {
                name: "Send test message"
            })
        );

        await user.click(
            await screen.findByRole("button", {
                name: "Approve proposal"
            })
        );

        await waitFor(() => {
            expect(
                screen.getByTestId("proposal-error")
            ).toHaveTextContent(
                "Could not update roadmap"
            );
        });
    });
});