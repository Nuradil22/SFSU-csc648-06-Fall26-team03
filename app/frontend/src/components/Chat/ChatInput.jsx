import { useState } from "react";

export default function ChatInput({ onSend, disabled }) {
    const [content, setContent] = useState("");

    function handleSubmit(event) {
        event.preventDefault();

        if (!content.trim() || disabled) return;

        onSend(content.trim());
        setContent("");
    }

    return (
        <form className="chat-input-form" onSubmit={handleSubmit}>
            <textarea
                value={content}
                onChange={(event) => setContent(event.target.value)}
                placeholder="Ask about your career goals..."
                aria-label="Message the career assistant"
                rows={2}
                disabled={disabled}
                onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        event.currentTarget.form.requestSubmit();
                    }
                }}
            />

            <button
                type="submit"
                disabled={disabled || !content.trim()}
                aria-label="Send message"
            >
                <span>Send</span>
                <span aria-hidden="true">➤</span>
            </button>
        </form>
    );
}
