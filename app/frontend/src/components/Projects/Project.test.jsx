import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Project from "./Project";

vi.mock("./projectDescription", () => ({
    default: ({ blocks, darkMode }) => (
        <div data-testid="project-description">
            <span>{JSON.stringify(blocks)}</span>
            <span>{String(darkMode)}</span>
        </div>
    )
}));

vi.mock("../ModelViewer/ModelViewer", () => ({
    default: ({ modelUrl }) => (
        <div data-testid="model-viewer">
            {modelUrl}
        </div>
    )
}));

vi.mock("./ModelRevisions", () => ({
    default: ({
        projectId,
        canEdit,
        onSelectRevision
    }) => (
        <div data-testid="model-revisions">
            <span data-testid="revision-project-id">
                {projectId}
            </span>

            <span data-testid="revision-can-edit">
                {String(canEdit)}
            </span>

            <button
                type="button"
                onClick={() =>
                    onSelectRevision("models/revision.glb")
                }
            >
                Select Revision
            </button>
        </div>
    )
}));

vi.mock("./ProjectEngagement", () => ({
    default: ({ projectId }) => (
        <div data-testid="project-engagement">
            Engagement for {projectId}
        </div>
    )
}));

const defaultProps = {
    name: "Portfolio Website",
    date: "2026",
    type: "Web Development",
    description: [
        {
            id: "block-1",
            type: "paragraph",
            content: "A portfolio project."
        }
    ]
};

function renderProject(props = {}) {
    return render(
        <Project
            {...defaultProps}
            {...props}
        />
    );
}

describe("Project", () => {
    it("renders the project metadata", () => {
        renderProject();

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "2026"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("heading", {
                level: 2,
                name: "Portfolio Website"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Web Development"
            })
        ).toBeInTheDocument();
    });

    it("starts collapsed", () => {
        renderProject();

        expect(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        ).toHaveAttribute("aria-expanded", "false");

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: "Project Overview"
            })
        ).not.toBeInTheDocument();

        expect(
            screen.getByText("+")
        ).toBeInTheDocument();
    });

    it("expands when the project header is clicked", async () => {
        const user = userEvent.setup();

        renderProject();

        const headerButton = screen.getByRole("button", {
            name: /Portfolio Website/
        });

        await user.click(headerButton);

        expect(headerButton).toHaveAttribute(
            "aria-expanded",
            "true"
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Project Overview"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText("-")
        ).toBeInTheDocument();
    });

    it("collapses when the project header is clicked again", async () => {
        const user = userEvent.setup();

        renderProject();

        const headerButton = screen.getByRole("button", {
            name: /Portfolio Website/
        });

        await user.click(headerButton);
        await user.click(headerButton);

        expect(headerButton).toHaveAttribute(
            "aria-expanded",
            "false"
        );

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: "Project Overview"
            })
        ).not.toBeInTheDocument();
    });

    it("renders the project owner when one is provided", () => {
        renderProject({
            owner: "Alex Rivera"
        });

        expect(
            screen.getByText("by Alex Rivera")
        ).toBeInTheDocument();
    });

    it("does not render an owner when one is not provided", () => {
        renderProject();

        expect(
            screen.queryByText(/^by /)
        ).not.toBeInTheDocument();
    });

    it("renders the project description when expanded", async () => {
        const user = userEvent.setup();

        renderProject({
            darkMode: true
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.getByTestId("project-description")
        ).toHaveTextContent(
            JSON.stringify(defaultProps.description)
        );

        expect(
            screen.getByTestId("project-description")
        ).toHaveTextContent("true");
    });

    it("renders project images when provided", async () => {
        const user = userEvent.setup();

        renderProject({
            images: [
                {
                    src: "image-one.png",
                    alt: "Project screenshot"
                },
                {
                    src: "image-two.png",
                    alt: ""
                }
            ]
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Project Gallery"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("img", {
                name: "Project screenshot"
            })
        ).toHaveAttribute("src", "image-one.png");

        expect(
            screen.getByRole("img", {
                name: "project image"
            })
        ).toHaveAttribute("src", "image-two.png");
    });

    it("does not render the gallery when there are no images", async () => {
        const user = userEvent.setup();

        renderProject({
            images: []
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: "Project Gallery"
            })
        ).not.toBeInTheDocument();
    });

    it("renders the 3D model when one is provided", async () => {
        const user = userEvent.setup();

        renderProject({
            model: "models/project.glb"
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "3D Model"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByTestId("model-viewer")
        ).toHaveTextContent("models/project.glb");
    });

    it("does not render the 3D model when one is not provided", async () => {
        const user = userEvent.setup();

        renderProject();

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.queryByTestId("model-viewer")
        ).not.toBeInTheDocument();
    });

    it("renders external project links", async () => {
        const user = userEvent.setup();

        renderProject({
            links: [
                {
                    label: "GitHub Repository",
                    url: "https://github.com/example/project"
                },
                {
                    label: "Live Demo",
                    url: "https://example.com"
                }
            ]
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Project Links"
            })
        ).toBeInTheDocument();

        const githubLink = screen.getByRole("link", {
            name: "GitHub Repository"
        });

        expect(githubLink).toHaveAttribute(
            "href",
            "https://github.com/example/project"
        );

        expect(githubLink).toHaveAttribute("target", "_blank");

        expect(
            screen.getByRole("link", {
                name: "Live Demo"
            })
        ).toHaveAttribute(
            "href",
            "https://example.com"
        );
    });

    it("renders child project actions when provided", async () => {
        const user = userEvent.setup();

        renderProject({
            children: (
                <button type="button">
                    Edit Project
                </button>
            )
        });

        await user.click(
            screen.getByRole("button", {
                name: /Portfolio Website/
            })
        );

        expect(
            screen.getByRole("button", {
                name: "Edit Project"
            })
        ).toBeInTheDocument();
    });
    
    it("passes dark mode to the project description", async () => {
    const user = userEvent.setup();

    renderProject({
        darkMode: true
    });

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.getByTestId("project-description")
    ).toHaveTextContent("true");
});

it("renders model revisions when a project ID is provided", async () => {
    const user = userEvent.setup();

    renderProject({
        model: "models/current.glb",
        projectId: "project-123",
        canEdit: true
    });

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.getByTestId("model-revisions")
    ).toBeInTheDocument();

    expect(
        screen.getByTestId("revision-project-id")
    ).toHaveTextContent("project-123");

    expect(
        screen.getByTestId("revision-can-edit")
    ).toHaveTextContent("true");
});

it("does not render model revisions without a project ID", async () => {
    const user = userEvent.setup();

    renderProject({
        model: "models/current.glb"
    });

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.queryByTestId("model-revisions")
    ).not.toBeInTheDocument();
});

it("changes the displayed model when a revision is selected", async () => {
    const user = userEvent.setup();

    renderProject({
        model: "models/current.glb",
        projectId: "project-123"
    });

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.getByTestId("model-viewer")
    ).toHaveTextContent("models/current.glb");

    await user.click(
        screen.getByRole("button", {
            name: "Select Revision"
        })
    );

    expect(
        screen.getByTestId("model-viewer")
    ).toHaveTextContent("models/revision.glb");
});

it("renders project engagement when a project ID is provided", async () => {
    const user = userEvent.setup();

    renderProject({
        projectId: "project-123"
    });

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.getByTestId("project-engagement")
    ).toHaveTextContent(
        "Engagement for project-123"
    );
});

it("does not render project engagement without a project ID", async () => {
    const user = userEvent.setup();

    renderProject();

    await user.click(
        screen.getByRole("button", {
            name: /Portfolio Website/
        })
    );

    expect(
        screen.queryByTestId("project-engagement")
    ).not.toBeInTheDocument();
});
});