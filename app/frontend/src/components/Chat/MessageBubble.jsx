import RoadmapProposalCard from "./RoadmapProposalCard";

// role is "user", "assistant", "error", or "proposal".
export default function MessageBubble({ message, onDecide }) {
    if (message.role === "proposal") {
        return <RoadmapProposalCard message={message} onDecide={onDecide} />;
    }

    const isUser = message.role === "user";
    const rowClass = isUser
        ? "user-message"
        : `assistant-message${message.role === "error" ? " error-message" : ""}`;

    return (
        <div className={`message-row ${rowClass}`}>
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
