import MessageBubble from "./MessageBubble";

export default function MessageList({ messages, isLoading }) {
    return (
        <div className="message-list" aria-live="polite">
            {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
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
