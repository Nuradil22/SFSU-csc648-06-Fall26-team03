import RoadmapProposalCard from "./RoadmapProposalCard";
import ResourceList from "../Roadmap/ResourceList";

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
                {/* Verified links found by live research for this reply. */}
                <ResourceList resources={message.resources} />
            </div>
        </div>
    );
}
