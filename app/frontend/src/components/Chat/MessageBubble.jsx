import RoadmapProposalCard from "./RoadmapProposalCard";

// role is "user", "assistant", "error", or "proposal".
export default function MessageBubble({ message, onDecide }) {
  if (message.role === "proposal") {
    return <RoadmapProposalCard message={message} onDecide={onDecide} />;
  }

  return (
    <div className={`chat-bubble chat-bubble-${message.role}`}>
      {message.content}
    </div>
  );
}
