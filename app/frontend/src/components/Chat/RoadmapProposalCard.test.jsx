import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RoadmapProposalCard from "./RoadmapProposalCard";

vi.mock("../Roadmap/RoadmapTimeline", () => ({
    default: ({ roadmap }) => (
        <div data-testid="roadmap-timeline">
            {JSON.stringify(roadmap)}
        </div>
    )
}));

const roadmap = {
    title: "Software Engineering Roadmap",
    steps: [
        {
            title: "Learn JavaScript",
            description: "Study the fundamentals."
        }
    ]
};

function renderCard(overrides = {}) {
    const message = {
        id: "proposal-message-1",
        role: "proposal",
        proposalId: "proposal-1",
        proposal: roadmap,
        status: "pending",
        busy: false,
        error: null,
        ...overrides
    };

    const onDecide = vi.fn();

    render(
        <RoadmapProposalCard
            message={message}
            onDecide={onDecide}
        />
    );

    return {
        message,
        onDecide
    };
}

describe("RoadmapProposalCard", () => {
    it("renders the proposed roadmap label", () => {
        renderCard();

        expect(
            screen.getByText("Proposed roadmap")
        ).toBeInTheDocument();
    });

    it("renders the roadmap timeline with the proposal", () => {
        renderCard();

        expect(
            screen.getByTestId("roadmap-timeline")
        ).toHaveTextContent(
            JSON.stringify(roadmap)
        );
    });

    it("renders Approve and Reject buttons for pending proposals", () => {
        renderCard();

        expect(
            screen.getByRole("button", {
                name: "Approve"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Reject"
            })
        ).toBeInTheDocument();
    });

    it("calls onDecide with approve when Approve is clicked", async () => {
        const user = userEvent.setup();
        const { message, onDecide } = renderCard();

        await user.click(
            screen.getByRole("button", {
                name: "Approve"
            })
        );

        expect(onDecide).toHaveBeenCalledWith(
            message,
            "approve"
        );
    });

    it("calls onDecide with reject when Reject is clicked", async () => {
        const user = userEvent.setup();
        const { message, onDecide } = renderCard();

        await user.click(
            screen.getByRole("button", {
                name: "Reject"
            })
        );

        expect(onDecide).toHaveBeenCalledWith(
            message,
            "reject"
        );
    });

    it("disables both action buttons while busy", () => {
        renderCard({
            busy: true
        });

        expect(
            screen.getByRole("button", {
                name: "Approve"
            })
        ).toBeDisabled();

        expect(
            screen.getByRole("button", {
                name: "Reject"
            })
        ).toBeDisabled();
    });

    it("renders the approved status", () => {
        renderCard({
            status: "approved"
        });

        expect(
            screen.getByText("Approved")
        ).toBeInTheDocument();

        expect(
            screen.getByText(
                "This is now your official roadmap."
            )
        ).toBeInTheDocument();
    });

    it("does not render action buttons after approval", () => {
        renderCard({
            status: "approved"
        });

        expect(
            screen.queryByRole("button", {
                name: "Approve"
            })
        ).not.toBeInTheDocument();

        expect(
            screen.queryByRole("button", {
                name: "Reject"
            })
        ).not.toBeInTheDocument();
    });

    it("renders the rejected status", () => {
        renderCard({
            status: "rejected"
        });

        expect(
            screen.getByText("Rejected")
        ).toBeInTheDocument();
    });

    it("does not render action buttons after rejection", () => {
        renderCard({
            status: "rejected"
        });

        expect(
            screen.queryByRole("button", {
                name: "Approve"
            })
        ).not.toBeInTheDocument();

        expect(
            screen.queryByRole("button", {
                name: "Reject"
            })
        ).not.toBeInTheDocument();
    });

    it("renders an error message when one exists", () => {
        renderCard({
            error: "Could not update roadmap."
        });

        expect(
            screen.getByText("Could not update roadmap.")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Could not update roadmap.")
        ).toHaveClass("chat-proposal-error");
    });

    it("does not render an error message when error is null", () => {
        renderCard({
            error: null
        });

        expect(
            screen.queryByText(/Could not update/)
        ).not.toBeInTheDocument();
    });
});