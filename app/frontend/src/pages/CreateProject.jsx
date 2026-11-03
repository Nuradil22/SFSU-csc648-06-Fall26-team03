import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import "./CreateProject.css";
import ProjectGallery from "../components/Projects/ProjectGallery";
import DescriptionEditor from "../components/Projects/DescriptionEditor";
import ProjectLinks from "../components/Projects/ProjectLinks";

import {
    addProjectLink,
    createProject,
    getProject,
    getToken,
    removeProjectMedia,
    removeProjectModel,
    updateProject,
    uploadProjectImage,
    uploadProjectModel,
} from "../lib/api";

// Plain-text version of the editor blocks, saved as the project's `description`
// so search and AI analysis can read it.
function blocksToText(blocks) {
    return blocks
        .flatMap((block) => (Array.isArray(block.content) ? [block.title, ...block.content] : [block.content]))
        .map((text) => (text || "").trim())
        .filter(Boolean)
        .join("\n");
}

function sameLink(a, b) {
    return a.label === b.label && a.url === b.url && (a.type || "") === (b.type || "");
}

// Handles both /projects/new and /projects/:id/edit.
function CreateProject({ darkMode }) {
    const { id } = useParams();
    const isEditing = Boolean(id);
    const navigate = useNavigate();

    const [title, setTitle] = useState("");
    const [date, setDate] = useState("");
    const [subject, setSubject] = useState("");
    const [blocks, setBlocks] = useState([]);
    const [images, setImages] = useState([]);
    const [links, setLinks] = useState([]);
    // What's already saved on the server, to work out what changed on save.
    const [saved, setSaved] = useState({ images: [], links: [] });

    // 3D model state
    const [modelFile, setModelFile] = useState(null);
    const [savedModel, setSavedModel] = useState(null);
    const [removeModel, setRemoveModel] = useState(false);

    const [loading, setLoading] = useState(isEditing);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isEditing || !getToken()) return;
        getProject(id)
            .then((project) => {
                setTitle(project.title);
                setDate(project.project_date || "");
                setSubject(project.subject || "");
                setBlocks(
                    project.content_blocks.length
                        ? project.content_blocks
                        : project.description
                            ? [{ id: crypto.randomUUID(), type: "paragraph", content: project.description }]
                            : []
                );
                const savedImages = project.images.map((image) => ({ id: image.id, src: image.url, alt: image.label, saved: true }));
                const savedLinks = project.links.map((link) => ({ id: link.id, label: link.label || "", url: link.url, type: link.link_type || "", saved: true }));
                setImages(savedImages);
                setLinks(savedLinks);
                setSaved({ images: savedImages, links: savedLinks });

                setSavedModel(project.model_3d || null);
            })
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [id, isEditing]);

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");
        setSaving(true);

        const fields = {
            title: title.trim(),
            project_date: date.trim() || null,
            subject: subject.trim() || null,
            content_blocks: blocks,
            description: blocksToText(blocks),
        };

        let project = null;
        try {
            project = isEditing ? await updateProject(id, fields) : await createProject(fields);

            // Upload or remove the project's 3D model.
            if (modelFile) {
                await uploadProjectModel(project.id, modelFile);
            } else if (removeModel && savedModel) {
                await removeProjectModel(project.id);
            }

            // Images: delete removed ones, upload new ones.
            const keptImageIds = new Set(images.filter((image) => image.saved).map((image) => image.id));
            for (const image of saved.images.filter((image) => !keptImageIds.has(image.id))) {
                await removeProjectMedia(project.id, image.id);
            }
            for (const image of images.filter((image) => image.file)) {
                await uploadProjectImage(project.id, image.file, image.alt);
            }

            // Links can't be edited in place: changed or removed ones are deleted,
            // then new and changed ones are added.
            const filledLinks = links.filter((link) => link.url.trim());
            for (const old of saved.links) {
                const current = filledLinks.find((link) => link.id === old.id);
                if (!current || !sameLink(current, old)) {
                    await removeProjectMedia(project.id, old.id);
                }
            }
            for (const link of filledLinks) {
                const old = saved.links.find((savedLink) => savedLink.id === link.id);
                if (!old || !sameLink(link, old)) {
                    await addProjectLink(project.id, {
                        label: link.label.trim() || link.url.trim(),
                        url: link.url.trim(),
                        link_type: link.type.trim(),
                    });
                }
            }

            navigate("/portfolio");
        } catch (err) {
            if (project && !isEditing) {
                // The project itself was created, so retrying here would make a duplicate.
                // Continue on its edit page, which loads what was actually saved.
                setError(`Project saved, but: ${err.message}`);
                navigate(`/projects/${project.id}/edit`, { replace: true });
                return;
            }
            setError(err.message);
        } finally {
            setSaving(false);
        }
    }

    if (!getToken()) {
        return (
            <main>
                <div className="box project-form">
                    <p>Please <Link to="/login">log in</Link> to {isEditing ? "edit" : "create"} a project.</p>
                </div>
            </main>
        );
    }

    if (loading) {
        return <main><p className="box project-form">Loading project...</p></main>;
    }

    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">{isEditing ? "Edit Your Project" : "Your New Project !!"}</h1>
            </div>

            <form className="box project-form" onSubmit={handleSubmit}>

                <div className="header-fields">

                    <div className="form-field header-field">
                        <label htmlFor="project-name">Project Name</label>
                        <input id="project-name" name="name" type="text" placeholder="Enter your project name" required
                            value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200}/>
                    </div>

                    <div className="form-field header-field">
                        <label htmlFor="project-date">Project Date</label>
                        <input id="project-date" name="date" type="text" placeholder="e.g. Fall 2025" required
                            value={date} onChange={(event) => setDate(event.target.value)} maxLength={100}/>
                    </div>

                    <div className="form-field header-field">
                        <label htmlFor="project-subject">Subject / Field</label>
                        <input id="project-subject" name="subject" type="text" placeholder="e.g. Interior Design, Architecture" required
                            value={subject} onChange={(event) => setSubject(event.target.value)} maxLength={200}/>
                    </div>

                </div>

                <DescriptionEditor blocks={blocks} setBlocks={setBlocks} />

                <ProjectGallery images={images} setImages={setImages} />

                <div className="project-model-editor">
                    <h2>3D Project Model</h2>
                    <p className="model-instructions">
                        Upload a 3D model of your project. GLB files exported from Scaniverse are supported.
                    </p>

                    <div className="model-dropzone">
                        <p>
                            {modelFile
                                ? "New model selected"
                                : savedModel && !removeModel
                                    ? "A 3D model is attached to this project"
                                    : "Add a 3D model to your project"}
                        </p>

                        <span>
                            {modelFile
                                ? modelFile.name
                                : savedModel && !removeModel
                                    ? savedModel.original_filename || "Existing 3D model"
                                    : "GLB files only"}
                        </span>

                        <label htmlFor="project-model" className="model-upload-button">
                            {modelFile || (savedModel && !removeModel) ? "Choose Another Model" : "Choose GLB File"}
                        </label>

                        <input
                            id="project-model"
                            type="file"
                            accept=".glb,model/gltf-binary"
                            hidden
                            onChange={(event) => {
                                const file = event.target.files?.[0];

                                if (!file) {
                                    setModelFile(null);
                                    return;
                                }

                                if (!file.name.toLowerCase().endsWith(".glb")) {
                                    setError("Please select a .glb file.");
                                    event.target.value = "";
                                    setModelFile(null);
                                    return;
                                }

                                setError("");
                                setModelFile(file);
                                setRemoveModel(false);
                            }}
                        />

                        {savedModel && !removeModel && (
                            <button
                                type="button"
                                className="model-remove-button"
                                onClick={() => {
                                    setRemoveModel(true);
                                    setModelFile(null);
                                }}
                            >
                                Remove Model
                            </button>
                        )}

                        {removeModel && (
                            <button
                                type="button"
                                className="model-undo-button"
                                onClick={() => setRemoveModel(false)}
                            >
                                Undo Remove
                            </button>
                        )}
                    </div>
                </div>

                <ProjectLinks links={links} setLinks={setLinks} />

                {error && <p className="form-error" role="alert">{error}</p>}

                <div className="project-form-actions">
                    <button type="submit" className="project-submit-button" disabled={saving}>
                        {saving ? "Saving..." : isEditing ? "Save Changes" : "Save Project"}
                    </button>
                </div>

            </form>
        </main>
    );
}

export default CreateProject;
