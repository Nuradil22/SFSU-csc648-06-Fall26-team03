import { useState } from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectGallery from "./ProjectGallery";

// Mimics the parent page that owns the images state.
function GalleryHarness({ initialImages = [] }) {
    const [images, setImages] = useState(initialImages);

    return (
        <ProjectGallery
            images={images}
            setImages={setImages}
        />
    );
}

// Helper so we don't repeat render() everywhere.
function renderGallery(initialImages = []) {
    return render(
        <GalleryHarness initialImages={initialImages} />
    );
}

// The browser normally creates blob URLs for local image previews.
// jsdom doesn't implement createObjectURL, so we provide a mock.
beforeEach(() => {
    vi.stubGlobal("URL", {
        createObjectURL: vi.fn(() => "blob:test-image"),
        revokeObjectURL: vi.fn()
    });
});

describe("ProjectGallery", () => {

    it("renders the gallery heading and instructions", () => {
        renderGallery();

        expect(
            screen.getByRole("heading", { name: "Project Gallery" })
        ).toBeInTheDocument();

        expect(
            screen.getByText(/Drag and drop images here/)
        ).toBeInTheDocument();
    });

    it("does not display an image list when the gallery is empty", () => {
        renderGallery();

        expect(
            screen.queryByRole("img")
        ).not.toBeInTheDocument();
    });

    it("opens the file picker when Browse Images is clicked", async () => {
        const user = userEvent.setup();
        const { container } = renderGallery();

        const fileInput = container.querySelector('input[type="file"]');
        const clickSpy = vi.spyOn(fileInput, "click");

        await user.click(
            screen.getByRole("button", { name: "Browse Images" })
        );

        expect(clickSpy).toHaveBeenCalled();
    });

    it("adds an image when a user selects a file", async () => {
        const user = userEvent.setup();
        const { container } = renderGallery();

        const file = new File(
            ["image contents"],
            "team-photo.png",
            { type: "image/png" }
        );

        const fileInput = container.querySelector('input[type="file"]');

        await user.upload(fileInput, file);

        expect(screen.getByRole("img")).toBeInTheDocument();
        expect(URL.createObjectURL).toHaveBeenCalledWith(file);
    });

    it("ignores files that are not images", async () => {
        const user = userEvent.setup();
        const { container } = renderGallery();

        const image = new File(
            ["image contents"],
            "photo.png",
            { type: "image/png" }
        );

        const document = new File(
            ["document contents"],
            "notes.txt",
            { type: "text/plain" }
        );

        const fileInput = container.querySelector('input[type="file"]');

        // applyAccept: false lets us simulate a non-image file
        // even though the input has accept="image/*".
        await user.upload(fileInput, [image, document], {
            applyAccept: false
        });

        expect(screen.getAllByRole("img")).toHaveLength(1);
    });

    it("removes an image when Remove Image is clicked", async () => {
        const user = userEvent.setup();

        renderGallery([
            {
                id: "image-1",
                src: "test-image.png",
                alt: "Test image",
                saved: true
            }
        ]);

        expect(screen.getByRole("img")).toBeInTheDocument();

        await user.click(
            screen.getByRole("button", { name: "Remove image" })
        );

        expect(screen.queryByRole("img")).not.toBeInTheDocument();
    });

    it("allows users to edit image alt text", async () => {
        const user = userEvent.setup();

        renderGallery([
            {
                id: "image-1",
                src: "test-image.png",
                alt: "Old description",
                saved: false
            }
        ]);

        const altInput = screen.getByLabelText(
            "Image description (alt text)"
        );

        await user.clear(altInput);
        await user.type(altInput, "A new description");

        expect(
            screen.getByRole("img", { name: "A new description" })
        ).toBeInTheDocument();
    });

    it("disables alt text editing for saved images", () => {
        renderGallery([
            {
                id: "image-1",
                src: "saved-image.png",
                alt: "Saved image",
                saved: true
            }
        ]);

        expect(
            screen.getByLabelText("Image description (alt text)")
        ).toBeDisabled();
    });

});
