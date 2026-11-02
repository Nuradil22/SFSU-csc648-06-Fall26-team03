export default function MessageBubble({ message }) {
    const isUser = message.role === "user";

    return (
        <div className={`message-row ${isUser ? "user-message" : "assistant-message"}`}>
            {!isUser && (
                <div className="message-avatar" aria-hidden="true">
                    AI
                </div>
            )}

            <div className="message-bubble">
                {message.content}
            </div>
        </div>
    );
}
