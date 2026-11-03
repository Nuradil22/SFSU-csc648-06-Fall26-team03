import RoadmapTimeline from "../Roadmap/RoadmapTimeline";

// An AI-generated roadmap proposal awaiting the student's decision.
// Nothing becomes the official roadmap until "Approve" succeeds on the backend.
export default function RoadmapProposalCard({ message, onDecide }) {
  const { proposal, status, busy, error } = message;

  return (
    <div className="chat-proposal">
      <div className="chat-proposal-label">
        Proposed roadmap
        {status !== "pending" && (
          <span className={`chat-proposal-status is-${status}`}>
            {status === "approved" ? "Approved" : "Rejected"}
          </span>
        )}
      </div>

      <RoadmapTimeline roadmap={proposal} />

      {status === "pending" && (
        <div className="chat-proposal-actions">
          <button
            type="button"
            className="chat-approve"
            disabled={busy}
            onClick={() => onDecide(message, "approve")}
          >
            Approve
          </button>
          <button
            type="button"
            className="chat-reject"
            disabled={busy}
            onClick={() => onDecide(message, "reject")}
          >
            Reject
          </button>
        </div>
      )}

      {status === "approved" && (
        <p className="chat-proposal-note">This is now your official roadmap.</p>
      )}

      {error && <p className="chat-proposal-error">{error}</p>}
    </div>
  );
}
