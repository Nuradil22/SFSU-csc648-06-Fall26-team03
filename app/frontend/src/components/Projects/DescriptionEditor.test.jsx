import { useState } from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DescriptionEditor from "./DescriptionEditor";

function DescriptionHarness({ initialBlocks = [] }) {
    const [blocks, setBlocks] = useState(initialBlocks);

    return (
        <DescriptionEditor
            blocks={blocks}
            setBlocks={setBlocks}
        />
    );
}

function renderEditor(initialBlocks = []) {
    return render(
        <DescriptionHarness initialBlocks={initialBlocks} />
    );
}

beforeEach(() => {
    vi.stubGlobal("crypto", {
        randomUUID: vi.fn(() => "test-block-id")
    });
});

describe("DescriptionEditor", () => {
    it("renders the project overview heading and controls", () => {
        renderEditor();

        expect(
            screen.getByRole("heading", { name: "Project Overview" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", { name: "Add Heading" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", { name: "Add Paragraph" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("button", { name: "Add Bullet List" })
        ).toBeInTheDocument();
    });

    it("adds a heading block", async () => {
        const user = userEvent.setup();

        renderEditor();

        await user.click(
            screen.getByRole("button", { name: "Add Heading" })
        );

        expect(
            screen.getByPlaceholderText("Enter heading...")
        ).toBeInTheDocument();

        expect(crypto.randomUUID).toHaveBeenCalled();
    });

    it("adds a paragraph block", async () => {
        const user = userEvent.setup();

        renderEditor();

        await user.click(
            screen.getByRole("button", { name: "Add Paragraph" })
        );

        expect(
            screen.getByPlaceholderText("Write your paragraph...")
        ).toBeInTheDocument();
    });

    it("adds a bullet list with a title and initial bullet point", async () => {
        const user = userEvent.setup();

        renderEditor();

        await user.click(
            screen.getByRole("button", { name: "Add Bullet List" })
        );

        expect(
            screen.getByPlaceholderText("Enter list title...")
        ).toHaveValue("Bullet List");

        expect(
            screen.getByPlaceholderText("Bullet point 1")
        ).toBeInTheDocument();
    });

    it("allows users to edit a heading", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "heading-1",
                type: "heading",
                title: "",
                content: ""
            }
        ]);

        const headingInput = screen.getByPlaceholderText(
            "Enter heading..."
        );

        await user.type(headingInput, "About Our Project");

        expect(headingInput).toHaveValue("About Our Project");
    });

    it("allows users to edit a paragraph", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "paragraph-1",
                type: "paragraph",
                title: "",
                content: ""
            }
        ]);

        const paragraphInput = screen.getByPlaceholderText(
            "Write your paragraph..."
        );

        await user.type(
            paragraphInput,
            "This is the project description."
        );

        expect(paragraphInput).toHaveValue(
            "This is the project description."
        );
    });

    it("allows users to edit a bullet list title", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "list-1",
                type: "list",
                title: "Bullet List",
                content: [""]
            }
        ]);

        const titleInput = screen.getByPlaceholderText(
            "Enter list title..."
        );

        await user.clear(titleInput);
        await user.type(titleInput, "Project Features");

        expect(titleInput).toHaveValue("Project Features");
    });

    it("allows users to edit a bullet point", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "list-1",
                type: "list",
                title: "Features",
                content: [""]
            }
        ]);

        const bulletInput = screen.getByPlaceholderText(
            "Bullet point 1"
        );

        await user.type(bulletInput, "Fast and accessible");

        expect(bulletInput).toHaveValue("Fast and accessible");
    });

    it("adds another bullet point", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "list-1",
                type: "list",
                title: "Features",
                content: ["First feature"]
            }
        ]);

        await user.click(
            screen.getByRole("button", {
                name: "Add Bullet Point"
            })
        );

        expect(
            screen.getByPlaceholderText("Bullet point 2")
        ).toBeInTheDocument();

        expect(
            screen.getAllByRole("textbox")
        ).toHaveLength(3);
    });

    it("deletes a bullet point", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "list-1",
                type: "list",
                title: "Features",
                content: ["First feature", "Second feature"]
            }
        ]);

        await user.click(
            screen.getByRole("button", {
                name: "Delete bullet point 1"
            })
        );

        expect(
            screen.queryByDisplayValue("First feature")
        ).not.toBeInTheDocument();

        expect(
            screen.getByDisplayValue("Second feature")
        ).toBeInTheDocument();
    });

    it("deletes an entire section", async () => {
        const user = userEvent.setup();

        renderEditor([
            {
                id: "heading-1",
                type: "heading",
                title: "",
                content: "Project Heading"
            }
        ]);

        expect(
            screen.getByDisplayValue("Project Heading")
        ).toBeInTheDocument();

        await user.click(
            screen.getByRole("button", {
                name: "Delete this section"
            })
        );

        expect(
            screen.queryByDisplayValue("Project Heading")
        ).not.toBeInTheDocument();
    });
});