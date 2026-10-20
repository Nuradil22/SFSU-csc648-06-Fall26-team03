import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import './portfolio.css';
import Project from '../components/Projects/project';
import { deleteProject, getCurrentUser, getMyProjects, getToken } from '../lib/api';
import { toProjectProps } from '../lib/projects';

function Portfolio ({ darkMode }){
    const navigate = useNavigate();
    const isLoggedIn = Boolean(getToken());
    const user = getCurrentUser();

    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(isLoggedIn);
    const [error, setError] = useState("");

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

                {loading && <p>Loading your projects...</p>}
                {error && <p className="form-error" role="alert">{error}</p>}
                {!loading && !error && projects.length === 0 && <p>You haven't added any projects yet.</p>}

                {/* List all a Users projects in a portfolio */}
                <div className="project-box">
                    {projects.map(project => (
                    <Project key={project.id} {...toProjectProps(project)} darkMode={darkMode}>
                        <button type="button" onClick={() => navigate(`/projects/${project.id}/edit`)}>Edit</button>
                        <button type="button" onClick={() => handleDelete(project)}>Delete</button>
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
