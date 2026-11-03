import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function MessageList({ messages, isLoading, onDecide }) {
    const listRef = useRef(null);

    // Keep the newest message in view. Scrolls only the list itself, so the
    // page does not jump when the chat sits below other content.
    useEffect(() => {
        const list = listRef.current;
        if (list) list.scrollTop = list.scrollHeight;
    }, [messages, isLoading]);

    return (
        <div className="message-list" aria-live="polite" ref={listRef}>
            {messages.map((message) => (
                <MessageBubble
                    key={message.id}
                    message={message}
                    onDecide={onDecide}
                />
            ))}

            {isLoading && (
                <div className="message-row assistant-message">
                    <div className="message-avatar">AI</div>
                    <div className="message-bubble typing-indicator">
                        Thinking...
                    </div>
                </div>
            )}
        </div>
    );
}
