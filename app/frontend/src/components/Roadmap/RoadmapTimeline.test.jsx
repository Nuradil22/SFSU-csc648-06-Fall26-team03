import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RoadmapTimeline from "./RoadmapTimeline";

const roadmap = {
    title: "Software Engineering Roadmap",
    goals: [
        {
            id: "goal-1",
            title: "Learn JavaScript",
            milestones: [
                {
                    id: "milestone-1",
                    title: "Complete a JavaScript course",
                    completed: true
                },
                {
                    id: "milestone-2",
                    title: "Build a JavaScript project",
                    completed: false
                }
            ]
        },
        {
            id: "goal-2",
            title: "Build a Portfolio",
            milestones: [
                {
                    id: "milestone-3",
                    title: "Create a portfolio website",
                    completed: true
                }
            ]
        }
    ]
};

describe("RoadmapTimeline", () => {
    it("renders nothing when no roadmap is provided", () => {
        const { container } = render(
            <RoadmapTimeline />
        );

        expect(container).toBeEmptyDOMElement();
    });

    it("renders nothing when the roadmap has no goals", () => {
        const { container } = render(
            <RoadmapTimeline
                roadmap={{
                    title: "Empty Roadmap",
                    goals: []
                }}
            />
        );

        expect(container).toBeEmptyDOMElement();
    });

    it("renders the roadmap title", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Software Engineering Roadmap"
            })
        ).toBeInTheDocument();
    });

    it("renders every goal", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        expect(
            screen.getByRole("button", {
                name: /Learn JavaScript/
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: /Build a Portfolio/
            })
        ).toBeInTheDocument();
    });

    it("renders goal progress counts", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        expect(
            screen.getByText("1/2 ▾")
        ).toBeInTheDocument();

        expect(
            screen.getByText("1/1 ▾")
        ).toBeInTheDocument();
    });

    it("renders milestones expanded by default", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        expect(
            screen.getByText("Complete a JavaScript course")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Build a JavaScript project")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Create a portfolio website")
        ).toBeInTheDocument();
    });

    it("marks a fully completed goal with the complete class", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        const completedGoal = screen
            .getByRole("button", {
                name: /Build a Portfolio/
            })
            .closest(".roadmap-goal");

        expect(completedGoal).toHaveClass(
            "roadmap-goal",
            "is-complete"
        );

        const incompleteGoal = screen
            .getByRole("button", {
                name: /Learn JavaScript/
            })
            .closest(".roadmap-goal");

        expect(incompleteGoal).not.toHaveClass(
            "is-complete"
        );
    });

    it("collapses a goal when its heading is clicked", async () => {
        const user = userEvent.setup();

        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        const goalButton = screen.getByRole("button", {
            name: /Learn JavaScript/
        });

        expect(goalButton).toHaveAttribute(
            "aria-expanded",
            "true"
        );

        await user.click(goalButton);

        expect(goalButton).toHaveAttribute(
            "aria-expanded",
            "false"
        );

        expect(
            screen.queryByText("Complete a JavaScript course")
        ).not.toBeInTheDocument();

        expect(
            screen.queryByText("Build a JavaScript project")
        ).not.toBeInTheDocument();

        expect(
            screen.getByText("1/2 ▸")
        ).toBeInTheDocument();
    });

    it("expands a collapsed goal when clicked again", async () => {
        const user = userEvent.setup();

        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        const goalButton = screen.getByRole("button", {
            name: /Learn JavaScript/
        });

        await user.click(goalButton);
        await user.click(goalButton);

        expect(goalButton).toHaveAttribute(
            "aria-expanded",
            "true"
        );

        expect(
            screen.getByText("Complete a JavaScript course")
        ).toBeInTheDocument();
    });

    it("renders checkboxes when onToggleMilestone is provided", () => {
        render(
            <RoadmapTimeline
                roadmap={roadmap}
                onToggleMilestone={vi.fn()}
            />
        );

        const completedCheckbox = screen.getByRole(
            "checkbox",
            {
                name: "Complete a JavaScript course"
            }
        );

        const incompleteCheckbox = screen.getByRole(
            "checkbox",
            {
                name: "Build a JavaScript project"
            }
        );

        expect(completedCheckbox).toBeChecked();
        expect(incompleteCheckbox).not.toBeChecked();
    });

    it("renders milestone text without checkboxes when no handler is provided", () => {
        render(
            <RoadmapTimeline roadmap={roadmap} />
        );

        expect(
            screen.getByText("Complete a JavaScript course")
        ).toBeInTheDocument();

        expect(
            screen.queryByRole("checkbox")
        ).not.toBeInTheDocument();
    });

    it("calls onToggleMilestone when a milestone is clicked", async () => {
        const user = userEvent.setup();
        const onToggleMilestone = vi.fn();

        render(
            <RoadmapTimeline
                roadmap={roadmap}
                onToggleMilestone={onToggleMilestone}
            />
        );

        await user.click(
            screen.getByRole("checkbox", {
                name: "Build a JavaScript project"
            })
        );

        expect(onToggleMilestone).toHaveBeenCalledWith(
            "goal-1",
            "milestone-2"
        );
    });

    it("disables milestone checkboxes when disabled is true", () => {
        render(
            <RoadmapTimeline
                roadmap={roadmap}
                onToggleMilestone={vi.fn()}
                disabled={true}
            />
        );

        const checkboxes = screen.getAllByRole(
            "checkbox"
        );

        expect(checkboxes).toHaveLength(3);

        checkboxes.forEach((checkbox) => {
            expect(checkbox).toBeDisabled();
        });
    });

    it("renders a goal with no milestones", () => {
        render(
            <RoadmapTimeline
                roadmap={{
                    title: "Roadmap",
                    goals: [
                        {
                            id: "goal-1",
                            title: "No milestones yet",
                            milestones: []
                        }
                    ]
                }}
            />
        );

        expect(
            screen.getByRole("button", {
                name: /No milestones yet/
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText("0/0 ▾")
        ).toBeInTheDocument();

        expect(
            document.querySelector(".roadmap-milestones")
        ).not.toBeInTheDocument();
    });

    it("supports goals without a milestones property", () => {
        render(
            <RoadmapTimeline
                roadmap={{
                    title: "Roadmap",
                    goals: [
                        {
                            id: "goal-1",
                            title: "Future goal"
                        }
                    ]
                }}
            />
        );

        expect(
            screen.getByRole("button", {
                name: /Future goal/
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText("0/0 ▾")
        ).toBeInTheDocument();
    });
});