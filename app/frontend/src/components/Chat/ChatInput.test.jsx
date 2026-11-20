import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInput from "./ChatInput";

const PLACEHOLDER =
    "Ask about your career goals, or ask for a roadmap...";

describe("ChatInput", () => {
    it("renders the message input and send button", () => {
        render(<ChatInput onSend={vi.fn()} />);

        expect(
            screen.getByRole("textbox", {
                name: "Message the career assistant"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Send message"
            })
        ).toBeInTheDocument();
    });

    it("starts with an empty input and disabled send button", () => {
        render(<ChatInput onSend={vi.fn()} />);

        expect(
            screen.getByRole("textbox", {
                name: "Message the career assistant"
            })
        ).toHaveValue("");

        expect(
            screen.getByRole("button", {
                name: "Send message"
            })
        ).toBeDisabled();
    });

    it("enables the send button when content is entered", async () => {
        const user = userEvent.setup();

        render(<ChatInput onSend={vi.fn()} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "Help me plan my career");

        expect(
            screen.getByRole("button", {
                name: "Send message"
            })
        ).not.toBeDisabled();
    });

    it("sends trimmed content and clears the input", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(<ChatInput onSend={onSend} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "  Help me plan my career  ");

        await user.click(
            screen.getByRole("button", {
                name: "Send message"
            })
        );

        expect(onSend).toHaveBeenCalledWith(
            "Help me plan my career"
        );

        expect(textbox).toHaveValue("");
    });

    it("does not send whitespace-only content", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(<ChatInput onSend={onSend} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "   ");

        expect(
            screen.getByRole("button", {
                name: "Send message"
            })
        ).toBeDisabled();

        await user.click(
            screen.getByRole("button", {
                name: "Send message"
            })
        );

        expect(onSend).not.toHaveBeenCalled();
    });

    it("submits when Enter is pressed", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(<ChatInput onSend={onSend} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "Send this message");
        await user.keyboard("{Enter}");

        expect(onSend).toHaveBeenCalledWith(
            "Send this message"
        );

        expect(textbox).toHaveValue("");
    });

    it("does not submit when Shift+Enter is pressed", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(<ChatInput onSend={onSend} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "First line");
        await user.keyboard("{Shift>}{Enter}{/Shift}");
        await user.type(textbox, "Second line");

        expect(onSend).not.toHaveBeenCalled();
        expect(textbox).toHaveValue(
            "First line\nSecond line"
        );
    });

    it("trims content when submitted with Enter", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(<ChatInput onSend={onSend} />);

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        await user.type(textbox, "  Career advice  ");
        await user.keyboard("{Enter}");

        expect(onSend).toHaveBeenCalledWith("Career advice");
    });

    it("disables the input and button when disabled is true", () => {
        render(
            <ChatInput
                onSend={vi.fn()}
                disabled={true}
            />
        );

        expect(
            screen.getByRole("textbox", {
                name: "Message the career assistant"
            })
        ).toBeDisabled();

        expect(
            screen.getByRole("button", {
                name: "Send message"
            })
        ).toBeDisabled();
    });

    it("does not send when disabled", async () => {
        const user = userEvent.setup();
        const onSend = vi.fn();

        render(
            <ChatInput
                onSend={onSend}
                disabled={true}
            />
        );

        const textbox = screen.getByRole("textbox", {
            name: "Message the career assistant"
        });

        expect(textbox).toBeDisabled();

        await user.click(
            screen.getByRole("button", {
                name: "Send message"
            })
        );

        expect(onSend).not.toHaveBeenCalled();
    });

    it("limits messages to 3000 characters", () => {
        render(<ChatInput onSend={vi.fn()} />);

        expect(
            screen.getByRole("textbox", {
                name: "Message the career assistant"
            })
        ).toHaveAttribute("maxLength", "3000");
    });
});