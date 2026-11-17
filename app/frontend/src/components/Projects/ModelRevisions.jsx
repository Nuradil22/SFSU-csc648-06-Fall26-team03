import { useEffect, useRef, useState } from "react";
import { getModelRevisions, uploadModelRevision } from "../../lib/api";
import "./ProjectEngagement.css";

// Revision history for a project's 3D model (M4 design iterations). Viewers
// can pick a version to display; the owner can also upload a new version with
// a change note. Older files are kept on the server.
export default function ModelRevisions({ projectId, canEdit, onSelectRevision }) {
    const [revisions, setRevisions] = useState([]);
    const [selectedPath, setSelectedPath] = useState(null);
    const [note, setNote] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const fileInput = useRef(null);

    useEffect(() => {
        let live = true;
        getModelRevisions(projectId)
            .then((list) => live && setRevisions(list))
            .catch((err) => live && setError(err.message || "Could not load revision history."));
        return () => { live = false; };
    }, [projectId]);

    function select(revision) {
        setSelectedPath(revision.url);
        onSelectRevision?.(revision.url);
    }

    async function submitRevision(event) {
        event.preventDefault();
        const file = fileInput.current?.files?.[0];
        if (!file || busy) return;
        setBusy(true);
        setError("");
        try {
            await uploadModelRevision(projectId, file, note.trim());
            setNote("");
            fileInput.current.value = "";
            const list = await getModelRevisions(projectId);
            setRevisions(list);
            const newest = list.find((r) => r.is_current) || list[0];
            if (newest) select(newest);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    if (error && revisions.length === 0) {
        return <p className="form-error" role="alert">{error}</p>;
    }
    if (revisions.length === 0 && !canEdit) return null;

    return (
        <div className="model-revisions">
            <h4>Model revisions</h4>
            <ul className="revision-list">
                {revisions.map((revision) => (
                    <li key={revision.id || revision.url}>
                        <button
                            type="button"
                            className={`revision-item ${revision.url === selectedPath ? "selected" : ""}`}
                            onClick={() => select(revision)}
                        >
                            <span className="revision-label">
                                {revision.version_label}
                                {revision.is_current && <em> (current)</em>}
                            </span>
                            <span className="revision-meta">
                                {revision.original_filename}
                                {" · "}
                                {new Date(revision.created_at).toLocaleDateString()}
                            </span>
                            {revision.change_note && (
                                <span className="revision-note">{revision.change_note}</span>
                            )}
                        </button>
                    </li>
                ))}
            </ul>

            {canEdit && (
                <form className="revision-upload" onSubmit={submitRevision}>
                    <label>
                        New version (.glb / .gltf)
                        <input
                            type="file"
                            accept=".glb,.gltf"
                            ref={fileInput}
                            disabled={busy}
                            required
                        />
                    </label>
                    <label>
                        What changed?
                        <input
                            type="text"
                            value={note}
                            onChange={(e) => setNote(e.target.value)}
                            placeholder="e.g. Fixed the enclosure gap"
                            maxLength={2000}
                            disabled={busy}
                        />
                    </label>
                    <button type="submit" disabled={busy}>
                        {busy ? "Uploading…" : "Upload revision"}
                    </button>
                </form>
            )}

            {error && <p className="form-error" role="alert">{error}</p>}
        </div>
    );
}
