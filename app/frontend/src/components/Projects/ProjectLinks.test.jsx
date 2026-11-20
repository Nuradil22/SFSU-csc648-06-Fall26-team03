import { useState } from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectLinks from "./ProjectLinks";

function LinksHarness({ initialLinks = [] }) {
    const [links, setLinks] = useState(initialLinks);

    return (
        <ProjectLinks
            links={links}
            setLinks={setLinks}
        />
    );
}

function renderLinks(initialLinks = []) {
    return render(
        <LinksHarness initialLinks={initialLinks} />
    );
}

beforeEach(() => {
    vi.stubGlobal("crypto", {
        randomUUID: vi.fn(() => "test-link-id")
    });
});

describe("ProjectLinks", () => {
    it("renders the heading and instructions", () => {
        renderLinks();

        expect(
            screen.getByRole("heading", {
                level: 2,
                name: "External Links"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByText(
                /Add repositories, project demonstrations/
            )
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "+ Add Link"
            })
        ).toBeInTheDocument();
    });

    it("does not render link cards when there are no links", () => {
        renderLinks();

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: /Link/
            })
        ).not.toBeInTheDocument();
    });

    it("adds a new link with empty fields", async () => {
        const user = userEvent.setup();

        renderLinks();

        await user.click(
            screen.getByRole("button", {
                name: "+ Add Link"
            })
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Link 1"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByLabelText("Link Name")
        ).toHaveValue("");

        expect(
            screen.getByLabelText("URL")
        ).toHaveValue("");

        expect(
            screen.getByLabelText("Link Type")
        ).toHaveValue("");

        expect(crypto.randomUUID).toHaveBeenCalled();
    });

    it("renders an existing link", () => {
        renderLinks([
            {
                id: "link-1",
                label: "Project Repository",
                url: "https://github.com/example/project",
                type: "GitHub"
            }
        ]);

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Link 1"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByLabelText("Link Name")
        ).toHaveValue("Project Repository");

        expect(
            screen.getByLabelText("URL")
        ).toHaveValue("https://github.com/example/project");

        expect(
            screen.getByLabelText("Link Type")
        ).toHaveValue("GitHub");
    });

    it("allows users to edit the link name", async () => {
        const user = userEvent.setup();

        renderLinks([
            {
                id: "link-1",
                label: "",
                url: "",
                type: ""
            }
        ]);

        const labelInput = screen.getByLabelText("Link Name");

        await user.type(labelInput, "Project Website");

        expect(labelInput).toHaveValue("Project Website");
    });

    it("allows users to edit the URL", async () => {
        const user = userEvent.setup();

        renderLinks([
            {
                id: "link-1",
                label: "",
                url: "",
                type: ""
            }
        ]);

        const urlInput = screen.getByLabelText("URL");

        await user.type(urlInput, "https://example.com");

        expect(urlInput).toHaveValue("https://example.com");
    });

    it("allows users to edit the link type", async () => {
        const user = userEvent.setup();

        renderLinks([
            {
                id: "link-1",
                label: "",
                url: "",
                type: ""
            }
        ]);

        const typeInput = screen.getByLabelText("Link Type");

        await user.type(typeInput, "Website");

        expect(typeInput).toHaveValue("Website");
    });

    it("removes a link", async () => {
        const user = userEvent.setup();

        renderLinks([
            {
                id: "link-1",
                label: "Project Repository",
                url: "https://github.com/example/project",
                type: "GitHub"
            }
        ]);

        expect(
            screen.getByDisplayValue("Project Repository")
        ).toBeInTheDocument();

        await user.click(
            screen.getByRole("button", {
                name: "Delete link 1"
            })
        );

        expect(
            screen.queryByDisplayValue("Project Repository")
        ).not.toBeInTheDocument();

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: "Link 1"
            })
        ).not.toBeInTheDocument();
    });

    it("renders multiple links with numbered headings", () => {
        renderLinks([
            {
                id: "link-1",
                label: "First Link",
                url: "https://first.example.com",
                type: "Website"
            },
            {
                id: "link-2",
                label: "Second Link",
                url: "https://second.example.com",
                type: "GitHub"
            }
        ]);

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Link 1"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Link 2"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Delete link 1"
            })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Delete link 2"
            })
        ).toBeInTheDocument();
    });

    it("renumbers links after one is removed", async () => {
        const user = userEvent.setup();

        renderLinks([
            {
                id: "link-1",
                label: "First Link",
                url: "",
                type: ""
            },
            {
                id: "link-2",
                label: "Second Link",
                url: "",
                type: ""
            }
        ]);

        await user.click(
            screen.getByRole("button", {
                name: "Delete link 1"
            })
        );

        expect(
            screen.getByRole("heading", {
                level: 3,
                name: "Link 1"
            })
        ).toBeInTheDocument();

        expect(
            screen.queryByRole("heading", {
                level: 3,
                name: "Link 2"
            })
        ).not.toBeInTheDocument();

        expect(
            screen.getByDisplayValue("Second Link")
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", {
                name: "Delete link 1"
            })
        ).toBeInTheDocument();
    });
});