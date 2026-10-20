import { useEffect, useRef, useState } from "react";
import "./ProjectGallery.css";

// Controlled: the parent page owns `images`. New images carry their `file` so the
// page can upload them; images already saved on the server have `saved: true`.
function ProjectGallery({ images, setImages }) {
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef(null);

    // Free the local preview URLs when the page is closed.
    const imagesRef = useRef(images);
    useEffect(() => {
        imagesRef.current = images;
    }, [images]);
    useEffect(() => {
        return () => {
            imagesRef.current.forEach((image) => image.file && URL.revokeObjectURL(image.src));
        };
    }, []);

    function addImages(files) {
        const imageFiles = Array.from(files).filter((file) =>
            file.type.startsWith("image/")
        );

        const newImages = imageFiles.map((file) => ({
            id: crypto.randomUUID(),
            file,
            src: URL.createObjectURL(file),
            alt: file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ")
        }));

        setImages((currentImages) => [...currentImages, ...newImages]);
    }

    function deleteImage(id) {
        setImages((currentImages) => {
            const imageToDelete = currentImages.find(
                (image) => image.id === id
            );

            if (imageToDelete?.file) {
                URL.revokeObjectURL(imageToDelete.src);
            }

            return currentImages.filter((image) => image.id !== id);
        });
    }

    function handleDrop(event) {
        event.preventDefault();
        setIsDragging(false);
        addImages(event.dataTransfer.files);
    }

    function updateAltText(id, value) {
        setImages((currentImages) =>
            currentImages.map((image) =>
                image.id === id ? { ...image, alt: value } : image
            )
        );
    }

    return (
        <section className="project-gallery-editor">
            <h2>Project Gallery</h2>
            <p className="gallery-instructions">
                Add images that showcase your project. You can select multiple
                images at once.
            </p>

            <div
                className={`gallery-dropzone ${isDragging ? "dragging" : ""}`}
                onDragOver={(event) => {
                    event.preventDefault();
                    setIsDragging(true);
                }}
                onDragLeave={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget)) {
                        setIsDragging(false);
                    }
                }}
                onDrop={handleDrop}
            >
                <p>Drag and drop images here</p>
                <span>or</span>

                <button type="button" onClick={() => fileInputRef.current?.click()}>
                    Browse Images
                </button>

                <input ref={fileInputRef} type="file" accept="image/*" multiple hidden
                    onChange={(event) => {
                        addImages(event.target.files);
                        event.target.value = "";
                    }}
                />
            </div>

            {images.length > 0 && (
                <div className="gallery-image-list">
                    {images.map((image) => (
                        <div className="gallery-image-card" key={image.id}>

                        <button type="button" className="delete-item-button" aria-label="Remove image"
                            onClick={() => deleteImage(image.id)}
                        >
                            Remove Image
                        </button>

                            <img src={image.src} alt={image.alt} />

                            <div className="gallery-image-field">

                                <label htmlFor={`image-alt-${image.id}`}>
                                    Image description (alt text)
                                </label>

                                <input id={`image-alt-${image.id}`} type="text" value={image.alt || ""} placeholder="Describe this image"
                                    disabled={image.saved}
                                    onChange={(event) =>
                                        updateAltText(
                                            image.id,
                                            event.target.value
                                        )
                                    }
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}

export default ProjectGallery;
