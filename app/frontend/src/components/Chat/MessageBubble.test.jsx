import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageBubble from "./MessageBubble";

vi.mock("./RoadmapProposalCard", () => ({
    default: ({ message, onDecide }) => (
        <div data-testid="roadmap-proposal-card">
            <span data-testid="proposal-message-id">
                {message.id}
            </span>

            <button
                type="button"
                onClick={() => onDecide(message, "approve")}
            >
                Mock approve
            </button>
        </div>
    )
}));

describe("MessageBubble", () => {
    it("renders a user message", () => {
        render(
            <MessageBubble
                message={{
                    id: "message-1",
                    role: "user",
                    content: "Help me choose a career."
                }}
                onDecide={vi.fn()}
            />
        );

        const bubble = screen.getByText(
            "Help me choose a career."
        );

        expect(bubble).toBeInTheDocument();

        expect(
            bubble.closest(".message-row")
        ).toHaveClass(
            "message-row",
            "user-message"
        );

        expect(
            screen.queryByText("AI")
        ).not.toBeInTheDocument();
    });

    it("renders an assistant message with the AI avatar", () => {
        render(
            <MessageBubble
                message={{
                    id: "message-1",
                    role: "assistant",
                    content: "Here are some career options."
                }}
                onDecide={vi.fn()}
            />
        );

        expect(
            screen.getByText("Here are some career options.")
        ).toBeInTheDocument();

        expect(
            screen.getByText("AI")
        ).toBeInTheDocument();

        const bubble = screen.getByText(
            "Here are some career options."
        );

        expect(
            bubble.closest(".message-row")
        ).toHaveClass(
            "message-row",
            "assistant-message"
        );

        expect(
            bubble.closest(".message-row")
        ).not.toHaveClass("error-message");
    });

    it("renders an error message with assistant and error classes", () => {
        render(
            <MessageBubble
                message={{
                    id: "message-1",
                    role: "error",
                    content: "Something went wrong."
                }}
                onDecide={vi.fn()}
            />
        );

        const bubble = screen.getByText(
            "Something went wrong."
        );

        expect(
            bubble.closest(".message-row")
        ).toHaveClass(
            "message-row",
            "assistant-message",
            "error-message"
        );

        expect(
            screen.getByText("AI")
        ).toBeInTheDocument();
    });

    it("renders a roadmap proposal card for proposal messages", () => {
        const onDecide = vi.fn();

        render(
            <MessageBubble
                message={{
                    id: "proposal-1",
                    role: "proposal",
                    proposalId: "roadmap-1",
                    proposal: {
                        title: "Software Engineering Roadmap"
                    },
                    status: "pending"
                }}
                onDecide={onDecide}
            />
        );

        expect(
            screen.getByTestId("roadmap-proposal-card")
        ).toBeInTheDocument();

        expect(
            screen.getByTestId("proposal-message-id")
        ).toHaveTextContent("proposal-1");

        expect(
            screen.queryByText("AI")
        ).not.toBeInTheDocument();
    });

    it("passes the decision handler to the proposal card", async () => {
        const user = (await import(
            "@testing-library/user-event"
        )).default.setup();

        const onDecide = vi.fn();

        const proposal = {
            id: "proposal-1",
            role: "proposal",
            proposalId: "roadmap-1",
            proposal: {
                title: "Software Engineering Roadmap"
            },
            status: "pending"
        };

        render(
            <MessageBubble
                message={proposal}
                onDecide={onDecide}
            />
        );

        await user.click(
            screen.getByRole("button", {
                name: "Mock approve"
            })
        );

        expect(onDecide).toHaveBeenCalledWith(
            proposal,
            "approve"
        );
    });

    it("renders unknown roles as assistant messages", () => {
        render(
            <MessageBubble
                message={{
                    id: "message-1",
                    role: "system",
                    content: "System message"
                }}
                onDecide={vi.fn()}
            />
        );

        const bubble = screen.getByText("System message");

        expect(
            bubble.closest(".message-row")
        ).toHaveClass(
            "message-row",
            "assistant-message"
        );

        expect(
            screen.getByText("AI")
        ).toBeInTheDocument();
    });
});