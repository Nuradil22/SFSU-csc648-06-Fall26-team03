import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import "./portfolio.css";
import "./Explore.css";
import Project from "../components/Projects/project";
import { searchProjects } from "../lib/api";
import { toProjectProps } from "../lib/projects";

const PAGE_SIZE = 20;

// Public search over all shared projects (GET /projects?search=&category=).
function Explore({ darkMode }) {
    const [searchParams, setSearchParams] = useSearchParams();
    const search = searchParams.get("search") || "";
    const category = searchParams.get("category") || "";

    const [searchInput, setSearchInput] = useState(search);
    const [categoryInput, setCategoryInput] = useState(category);
    const [projects, setProjects] = useState([]);
    const [hasMore, setHasMore] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let cancelled = false;
        searchProjects({ search, category, limit: PAGE_SIZE })
            .then((results) => {
                if (cancelled) return;
                setProjects(results);
                setHasMore(results.length === PAGE_SIZE);
                setError("");
            })
            .catch((err) => !cancelled && setError(err.message))
            .finally(() => !cancelled && setLoading(false));
        return () => { cancelled = true; };
    }, [search, category]);

    function handleSubmit(event) {
        event.preventDefault();
        const params = {};
        if (searchInput.trim()) params.search = searchInput.trim();
        if (categoryInput.trim()) params.category = categoryInput.trim();
        // The effect only re-runs when the search actually changes.
        if ((params.search || "") === search && (params.category || "") === category) return;
        setLoading(true);
        setSearchParams(params);
    }

    async function loadMore() {
        try {
            const more = await searchProjects({ search, category, limit: PAGE_SIZE, offset: projects.length });
            setProjects((current) => [...current, ...more]);
            setHasMore(more.length === PAGE_SIZE);
        } catch (err) {
            setError(err.message);
        }
    }

    const categories = [...new Set(projects.map((p) => p.subject).filter(Boolean))].sort();

    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">Explore Projects</h1>
            </div>

            <form className="box explore-search" onSubmit={handleSubmit} role="search">
                <label htmlFor="explore-search-input">Search</label>
                <input id="explore-search-input" type="search" placeholder="e.g. robot, python, React"
                    value={searchInput} onChange={(event) => setSearchInput(event.target.value)} maxLength={100}/>

                <label htmlFor="explore-category-input">Category</label>
                <input id="explore-category-input" type="text" placeholder="Any category" list="explore-categories"
                    value={categoryInput} onChange={(event) => setCategoryInput(event.target.value)} maxLength={200}/>
                <datalist id="explore-categories">
                    {categories.map((name) => <option key={name} value={name}/>)}
                </datalist>

                <button type="submit">Search</button>
            </form>

            <div className="portfolio-body">
                {loading && <p>Loading projects... (the server may take up to a minute to wake up)</p>}
                {error && <p className="form-error" role="alert">{error}</p>}
                {!loading && !error && projects.length === 0 && (
                    <p>No projects found{search || category ? " for that search" : ""}.</p>
                )}

                <div className="project-box">
                    {projects.map((project) => (
                        <Project key={project.id} {...toProjectProps(project)} owner={project.owner_name} darkMode={darkMode}>
                            {project.share_token && (
                                <Link to={`/p/${project.share_token}`}>View {project.owner_name}'s portfolio</Link>
                            )}
                        </Project>
                    ))}
                </div>

                {hasMore && <button type="button" onClick={loadMore}>Load more</button>}
            </div>
        </main>
    );
}

export default Explore;
