import "./ProjectLinks.css";

// Controlled: the parent page owns `links` so it can save and pre-fill them.
function ProjectLinks({ links, setLinks }) {

    function addLink() {
        const newLink = {
            id: crypto.randomUUID(),
            label: "",
            url: "",
            type: ""
        };

        setLinks((currentLinks) => [...currentLinks, newLink]);
    }

    function deleteLink(id) {
        setLinks((currentLinks) =>
            currentLinks.filter((link) => link.id !== id)
        );
    }

    function updateLink(id, field, value) {
        setLinks((currentLinks) =>
            currentLinks.map((link) =>
                link.id === id
                    ? { ...link, [field]: value }
                    : link
            )
        );
    }

    return (
        <section className="project-links-editor">
            <h2>External Links</h2>

            <p className="project-links-instructions">
                Add repositories, project demonstrations, websites, or other
                resources related to your project.
            </p>

            <div className="project-links-list">
                {links.map((link, index) => (
                    <div className="project-link-card" key={link.id}>

                    <button type="button" className="delete-item-button" aria-label={`Delete link ${index + 1}`}
                        onClick={() => deleteLink(link.id)}
                    >
                        Remove Link
                    </button>

                        <h3>Link {index + 1}</h3>

                        <div className="project-link-field">
                            <label htmlFor={`link-label-${link.id}`}>
                                Link Name
                            </label>
                            <input
                                id={`link-label-${link.id}`}
                                type="text"
                                placeholder="e.g. Main GitHub Repository"
                                value={link.label}
                                onChange={(event) =>
                                    updateLink(
                                        link.id,
                                        "label",
                                        event.target.value
                                    )
                                }
                            />
                        </div>

                        <div className="project-link-field">
                            <label htmlFor={`link-url-${link.id}`}>
                                URL
                            </label>
                            <input
                                id={`link-url-${link.id}`}
                                type="url"
                                placeholder="https://..."
                                value={link.url}
                                onChange={(event) =>
                                    updateLink(
                                        link.id,
                                        "url",
                                        event.target.value
                                    )
                                }
                            />
                        </div>

                        <div className="project-link-field">
                            <label htmlFor={`link-type-${link.id}`}>
                                Link Type
                            </label>
                            <input
                                id={`link-type-${link.id}`}
                                type="text"
                                placeholder="e.g. GitHub, YouTube, Website"
                                value={link.type}
                                onChange={(event) =>
                                    updateLink(
                                        link.id,
                                        "type",
                                        event.target.value
                                    )
                                }
                            />
                        </div>
                    </div>
                ))}
            </div>

            <button
                className="project-links-add-button"
                type="button"
                onClick={addLink}
            >
                + Add Link
            </button>
        </section>
    );
}

export default ProjectLinks;
