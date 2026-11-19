import { useEffect, useState } from "react";
import {
    addComment,
    deleteComment,
    getComments,
    getEngagement,
    getToken,
    likeProject,
    unlikeProject,
} from "../../lib/api";
import "./ProjectEngagement.css";

// Likes + comments for a project (M4 social engagement). Reads work for any
// viewer who can see the project; liking, commenting, and deleting require
// login, which the backend enforces as well.
export default function ProjectEngagement({ projectId }) {
    const [likeCount, setLikeCount] = useState(0);
    const [liked, setLiked] = useState(false);
    const [comments, setComments] = useState([]);
    const [draft, setDraft] = useState("");
    const [loading, setLoading] = useState(true);
    const [loadFailed, setLoadFailed] = useState(false);
    const [busy, setBusy] = useState(""); // "", "like", "comment", or "delete"
    const [error, setError] = useState("");

    const loggedIn = Boolean(getToken());

    useEffect(() => {
        let live = true;
        Promise.all([getEngagement(projectId), getComments(projectId)])
            .then(([engagement, list]) => {
                if (!live) return;
                setLikeCount(engagement.like_count);
                setLiked(engagement.liked_by_me);
                setComments(list);
            })
            .catch((err) => {
                if (!live) return;
                setLoadFailed(true);
                setError(err.message || "Could not load comments.");
            })
            .finally(() => live && setLoading(false));
        return () => { live = false; };
    }, [projectId]);

    async function toggleLike() {
        if (!loggedIn || busy) return;
        setBusy("like");
        setError("");
        try {
            const result = liked
                ? await unlikeProject(projectId)
                : await likeProject(projectId);
            setLikeCount(result.like_count);
            setLiked(result.liked_by_me);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy("");
        }
    }

    async function submitComment(event) {
        event.preventDefault();
        const body = draft.trim();
        if (!body || busy) return;
        setBusy("comment");
        setError("");
        try {
            const comment = await addComment(projectId, body);
            setComments((previous) => [...previous, comment]);
            setDraft("");
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy("");
        }
    }

    async function removeComment(commentId) {
        if (busy) return;
        setBusy("delete");
        setError("");
        try {
            await deleteComment(projectId, commentId);
            setComments((previous) => previous.filter((c) => c.id !== commentId));
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <section className="project-engagement">
            <div className="engagement-likes">
                <button
                    type="button"
                    className={`like-button ${liked ? "liked" : ""}`}
                    onClick={toggleLike}
                    disabled={!loggedIn || busy}
                    aria-pressed={liked}
                    title={loggedIn ? (liked ? "Unlike this project" : "Like this project") : "Log in to like this project"}
                >
                    {liked ? "♥" : "♡"} {likeCount} {likeCount === 1 ? "like" : "likes"}
                </button>
                {!loggedIn && <span className="engagement-hint">Log in to like or comment</span>}
            </div>

            <h4>Comments ({comments.length})</h4>

            {loading ? (
                <p className="engagement-hint">Loading comments…</p>
            ) : loadFailed ? null : comments.length === 0 ? (
                <p className="engagement-hint">No comments yet.</p>
            ) : (
                <ul className="comment-list">
                    {comments.map((comment) => (
                        <li key={comment.id} className="comment-item">
                            <div className="comment-head">
                                <strong>{comment.author_name}</strong>
                                <time dateTime={comment.created_at}>
                                    {new Date(comment.created_at).toLocaleString()}
                                </time>
                                {comment.can_delete && (
                                    <button
                                        type="button"
                                        className="comment-delete"
                                        onClick={() => removeComment(comment.id)}
                                        disabled={busy}
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                            <p className="comment-body">{comment.body}</p>
                        </li>
                    ))}
                </ul>
            )}

            {loggedIn && (
                <form className="comment-form" onSubmit={submitComment}>
                    <textarea
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        placeholder="Share feedback on this project…"
                        maxLength={2000}
                        rows={2}
                        disabled={busy}
                        aria-label="Write a comment"
                    />
                    <button type="submit" disabled={busy || !draft.trim()}>
                        {busy === "comment" ? "Posting…" : "Post comment"}
                    </button>
                </form>
            )}

            {error && <p className="form-error" role="alert">{error}</p>}
        </section>
    );
}
