import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import './portfolio.css';
import Project from '../components/Projects/project';
import { deleteProject, getCurrentUser, getMyProjects, getToken, getPortfolioVisibility, setPortfolioVisibility } from '../lib/api';
import { toProjectProps } from '../lib/projects';

function Portfolio ({ darkMode }){
    const navigate = useNavigate();
    const isLoggedIn = Boolean(getToken());
    const user = getCurrentUser();

    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(isLoggedIn);
    const [error, setError] = useState("");
    const [visibility, setVisibility] = useState(null);
    const [savingVisibility, setSavingVisibility] = useState(false);
    const [visibilityError, setVisibilityError] = useState("");

    async function loadVisibility() {
        try {
            setVisibility(await getPortfolioVisibility());
            setVisibilityError("");
        } catch (err) {
            setVisibilityError(err.message);
        }
    }

    useEffect(() => {
        if (!isLoggedIn) return;
        let cancelled = false;
        getPortfolioVisibility()
            .then((saved) => !cancelled && setVisibility(saved))
            .catch((err) => !cancelled && setVisibilityError(err.message));
        return () => { cancelled = true; };
    }, [isLoggedIn]);

    useEffect(() => {
        if (!isLoggedIn) return;
        getMyProjects()
            .then(setProjects)
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, [isLoggedIn]);

    async function handleDelete(project) {
        if (!window.confirm(`Delete "${project.title}"? This can't be undone.`)) return;
        try {
            await deleteProject(project.id);
            setProjects((current) => current.filter((p) => p.id !== project.id));
        } catch (err) {
            setError(err.message);
        }
    }

    // placeholder:
    // Ali, please replace this with the backend update call when project visibility is supported.
    async function handleVisibilityToggle() {
        if (!visibility || savingVisibility) return;
        setSavingVisibility(true);
        setVisibilityError("");
        try {
            setVisibility(await setPortfolioVisibility(!visibility.is_public));
        } catch (err) {
            setVisibilityError(`${err.message} Visibility was not confirmed; retry or reload to check.`);
        } finally {
            setSavingVisibility(false);
        }
    }

    if (!isLoggedIn) {
        return (
            <main>
                <div className ="banner">
                    <h1 className="banner-title">Your Portfolio</h1>
                </div>
                <div className="portfolio-body">
                    <p className="box project-box">
                        <Link to="/login">Log in</Link> to see and manage your projects,
                        or <Link to="/explore">explore other students' projects</Link>.
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main>
            <div className ="banner">
                <h1 className="banner-title">{user?.name ? `${user.name}'s Portfolio` : "Your Portfolio"}</h1>
            </div>

            <div className="portfolio-body">

                <section className="box" aria-label="Portfolio visibility">
                    <h2>Portfolio visibility</h2>
                    <p>Public portfolios and all their projects appear in Explore Projects. Private portfolios are hidden from public discovery.</p>
                    <button type="button" className={`toggle ${visibility?.is_public ? "on" : ""}`}
                        role="switch" aria-checked={Boolean(visibility?.is_public)}
                        aria-label="Public portfolio" disabled={!visibility || savingVisibility}
                        onClick={handleVisibilityToggle}>
                        <span className="toggle-knob" />
                    </button>
                    <p role="status">{savingVisibility ? "Saving visibility..." : visibility ? `${visibility.is_public ? "Public" : "Private"} — ${visibilityError ? "last confirmed state" : "saved"}` : visibilityError ? "Visibility unavailable" : "Loading visibility..."}</p>
                    {visibilityError && <p className="form-error" role="alert">{visibilityError} <button type="button" onClick={loadVisibility}>Reload visibility</button></p>}
                </section>
                {loading && <p>Loading your projects...</p>}
                {error && <p className="form-error" role="alert">{error}</p>}
                {!loading && !error && projects.length === 0 && <p>You haven't added any projects yet.</p>}

                {/* List all a Users projects in a portfolio */}
                <div className="project-box">
                    {projects.map(project => (
                    <Project key={project.id} {...toProjectProps(project)} darkMode={darkMode}>
                        <button className="portfolio-button" type="button" onClick={() => navigate(`/projects/${project.id}/edit`)}>Edit</button>
                        <button className="portfolio-button" type="button" onClick={() => handleDelete(project)}>Delete</button>
                        <p>Visibility follows your portfolio setting.</p>
                        
                    </Project>
                ))}
                </div>

                {/* Give the user an option to create a new project, routes to the new project page */}
                <button className="box project-card create-project-card project-box" onClick={() => navigate("/projects/new")}>
                    <h2>Create New Project !!</h2>
                </button>



            </div>
        </main>
    );
}

export default Portfolio;
