import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import MessageList from "./MessageList";

vi.mock("./MessageBubble", () => ({
    default: ({ message, onDecide }) => (
        <div
            data-testid={`message-bubble-${message.id}`}
        >
            <span>{message.content || message.id}</span>

            <button
                type="button"
                onClick={() => onDecide(message, "approve")}
            >
                Decide
            </button>
        </div>
    )
}));

describe("MessageList", () => {
    it("renders the message list with polite live updates", () => {
        render(
            <MessageList
                messages={[]}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        const list = document.querySelector(".message-list")

        expect(list).toBeInTheDocument();
        expect(list).toHaveAttribute(
            "aria-live",
            "polite"
        );
    });

    it("renders every message", () => {
        const messages = [
            {
                id: "message-1",
                role: "user",
                content: "What career should I pursue?"
            },
            {
                id: "message-2",
                role: "assistant",
                content: "Here are some possibilities."
            },
            {
                id: "message-3",
                role: "error",
                content: "Something went wrong."
            }
        ];

        render(
            <MessageList
                messages={messages}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        expect(
            screen.getByTestId("message-bubble-message-1")
        ).toBeInTheDocument();

        expect(
            screen.getByTestId("message-bubble-message-2")
        ).toBeInTheDocument();

        expect(
            screen.getByTestId("message-bubble-message-3")
        ).toBeInTheDocument();
    });

    it("renders no typing indicator when it is not loading", () => {
        render(
            <MessageList
                messages={[]}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        expect(
            screen.queryByText("Thinking...")
        ).not.toBeInTheDocument();
    });

    it("renders the typing indicator while loading", () => {
        render(
            <MessageList
                messages={[]}
                isLoading={true}
                onDecide={vi.fn()}
            />
        );

        expect(
            screen.getByText("Thinking...")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Thinking...")
        ).toHaveClass("message-bubble", "typing-indicator");

        expect(
            screen.getByText("AI")
        ).toBeInTheDocument();
    });

    it("renders messages and the typing indicator while loading", () => {
        render(
            <MessageList
                messages={[
                    {
                        id: "message-1",
                        role: "user",
                        content: "Help me."
                    }
                ]}
                isLoading={true}
                onDecide={vi.fn()}
            />
        );

        expect(
            screen.getByTestId("message-bubble-message-1")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Thinking...")
        ).toBeInTheDocument();
    });

    it("passes the decision handler to each message bubble", async () => {
        const user = (await import(
            "@testing-library/user-event"
        )).default.setup();

        const onDecide = vi.fn();

        const message = {
            id: "proposal-1",
            role: "proposal",
            content: "Roadmap proposal"
        };

        render(
            <MessageList
                messages={[message]}
                isLoading={false}
                onDecide={onDecide}
            />
        );

        await user.click(
            screen.getByRole("button", {
                name: "Decide"
            })
        );

        expect(onDecide).toHaveBeenCalledWith(
            message,
            "approve"
        );
    });

    it("scrolls the list to the bottom when messages change", () => {
        Object.defineProperty(
            HTMLElement.prototype,
            "scrollHeight",
            {
                configurable: true,
                value: 500
            }
        );

        const { rerender } = render(
            <MessageList
                messages={[]}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        const list = document.querySelector(".message-list")

        expect(list.scrollTop).toBe(500);

        rerender(
            <MessageList
                messages={[
                    {
                        id: "message-1",
                        role: "assistant",
                        content: "New message"
                    }
                ]}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        expect(list.scrollTop).toBe(500);
    });

    it("scrolls the list when loading changes", () => {
        Object.defineProperty(
            HTMLElement.prototype,
            "scrollHeight",
            {
                configurable: true,
                value: 800
            }
        );

        const { rerender } = render(
            <MessageList
                messages={[]}
                isLoading={false}
                onDecide={vi.fn()}
            />
        );

        const list = document.querySelector(".message-list")

        rerender(
            <MessageList
                messages={[]}
                isLoading={true}
                onDecide={vi.fn()}
            />
        );

        expect(list.scrollTop).toBe(800);
    });
});