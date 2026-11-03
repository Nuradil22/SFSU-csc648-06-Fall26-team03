import { useState } from "react";

// Matches the backend ChatRequest limit (max_length=3000).
const MAX_LENGTH = 3000;

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    if (!text.trim() || disabled) return;

    onSend(text.trim());
    setText("");
  }

  function handleKeyDown(event) {
    // Enter sends; Shift+Enter adds a new line.
    if (event.key === "Enter" && !event.shiftKey) {
      handleSubmit(event);
    }
  }

  return (
    <form className="chat-composer" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={event => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about career paths, skills, or a roadmap…"
        aria-label="Message your career guide"
        maxLength={MAX_LENGTH}
        rows={2}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !text.trim()}>
        Send
      </button>
    </form>
  );
}
