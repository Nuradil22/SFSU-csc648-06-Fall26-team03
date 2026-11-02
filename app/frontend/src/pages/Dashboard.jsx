
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import "./Dashboard.css";
import {
    getCurrentUser,
    getMyPortfolio,
    getMyProjects,
    getToken
} from "../lib/api";

function Dashboard({ darkMode }) {
    const isLoggedIn = Boolean(getToken());
    const user = getCurrentUser();

    const [portfolio, setPortfolio] = useState(null);
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(isLoggedIn);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isLoggedIn) return;

        let cancelled = false;

        async function loadDashboard() {
            const results = await Promise.allSettled([
                getMyPortfolio(),
                getMyProjects()
            ]);

            if (cancelled) return;

            if (results[0].status === "fulfilled") {
                setPortfolio(results[0].value);
            }

            if (results[1].status === "fulfilled") {
                setProjects(
                    Array.isArray(results[1].value)
                        ? results[1].value
                        : []
                );
            }

            const failures = results.filter(
                result => result.status === "rejected"
            );

            if (failures.length === 2) {
                setError(failures[0].reason.message);
            } else if (failures.length === 1) {
                setError(
                    `Some dashboard information couldn't load: ${failures[0].reason.message}`
                );
            }

            setLoading(false);
        }

        loadDashboard();

        return () => {
            cancelled = true;
        };
    }, [isLoggedIn]);

    if (!isLoggedIn) {
        return (
            <main>
                <div className="banner">
                    <h1 className="banner-title">Dashboard</h1>
                </div>

                <div className="dashboard-body">
                    <div className="box dashboard-section">
                        <h2 className="box-header">Welcome!</h2>
                        <p>
                            <Link to="/login">Log in</Link> to view your dashboard.
                        </p>
                    </div>
                </div>
            </main>
        );
    }

    const name = portfolio?.name || user?.name || "Student";

    const skills = portfolio?.skills || [];
    const education = portfolio?.education || [];
    const certificates = portfolio?.certificates || [];
    const jobPreferences = portfolio?.job_preferences || [];

    // These are the actual sections users can complete in Account Setup.
    const profileSections = [
        Boolean(portfolio?.name),
        Boolean(portfolio?.email),
        Boolean(portfolio?.location),
        education.length > 0,
        certificates.length > 0,
        skills.length > 0,
        jobPreferences.length > 0
    ];

    const completedSections = profileSections.filter(Boolean).length;
    const profileProgress = Math.round(
        (completedSections / profileSections.length) * 100
    );

    const recentProjects = [...projects]
        .sort((a, b) =>
            new Date(b.updated_at || b.created_at || 0) -
            new Date(a.updated_at || a.created_at || 0)
        )
        .slice(0, 3);

    function formatDate(date) {
        if (!date) return "Date unavailable";

        const parsed = new Date(date);

        if (Number.isNaN(parsed.getTime())) return "Date unavailable";

        return parsed.toLocaleDateString();
    }

    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">Welcome Back, {name}!</h1>
                <p>Your Projectory Dashboard</p>
            </div>

            <div className="dashboard-body">

                {loading && <p>Loading your dashboard...</p>}

                {error && (
                    <p className="form-error" role="alert">
                        {error}
                    </p>
                )}

                {!loading && (
                    <>
                        {/* Overview cards */}
                        <section className="dashboard-stats">
                            <div className="box dashboard-stat">
                                <h2 className="box-header">Projects</h2>
                                <p>{projects.length}</p>
                                <Link to="/portfolio">View Portfolio</Link>
                            </div>

                            <div className="box dashboard-stat">
                                <h2 className="box-header">Skills</h2>
                                <p>{skills.length}</p>
                                <Link to="/account/setup">Manage Skills</Link>
                            </div>

                            <div className="box dashboard-stat">
                                <h2 className="box-header">Certificates</h2>
                                <p>{certificates.length}</p>
                                <Link to="/account/setup">Manage Certificates</Link>
                            </div>

                            <div className="box dashboard-stat">
                                <h2 className="box-header">Education</h2>
                                <p>{education.length}</p>
                                <Link to="/account/setup">Manage Education</Link>
                            </div>
                        </section>

                        {/* Profile overview */}
                        <section className="box dashboard-section">
                            <div className="dashboard-section-heading">
                                <h2 className="box-header">Account Overview</h2>
                                <Link to="/account/setup">Edit Account</Link>
                            </div>

                            <div className="dashboard-profile-info">
                                <div>
                                    <h3>{name}</h3>
                                    <p>{portfolio?.email || user?.email || "No email provided"}</p>
                                    <p>{portfolio?.location || "No location added yet"}</p>
                                </div>

                                <div className="dashboard-completion">
                                    <h3>Profile Completion</h3>
                                    <p>{profileProgress}%</p>

                                    <div className="dashboard-progress">
                                        <div
                                            style={{
                                                width: `${profileProgress}%`
                                            }}
                                        />
                                    </div>

                                    <small>
                                        {completedSections} of {profileSections.length} sections completed
                                    </small>
                                </div>
                            </div>
                        </section>

                        {/* Education */}
                        <section className="box dashboard-section">
                            <div className="dashboard-section-heading">
                                <h2 className="box-header">Education & Degrees</h2>
                                <Link to="/account/setup">Edit</Link>
                            </div>

                            {education.length === 0 ? (
                                <p>No education information added yet.</p>
                            ) : (
                                education.map(item => (
                                    <div className="dashboard-list-item" key={item.id}>
                                        <h3>{item.degree || "Degree not specified"}</h3>
                                        <p>{item.school_name}</p>
                                        {item.graduation_date && (
                                            <p>
                                                Graduation: {item.graduation_date.slice(0, 4)}
                                            </p>
                                        )}
                                    </div>
                                ))
                            )}
                        </section>

                        {/* Skills and certificates */}
                        <div className="dashboard-two-column">
                            <section className="box dashboard-section">
                                <div className="dashboard-section-heading">
                                    <h2 className="box-header">My Skills</h2>
                                    <Link to="/account/setup">Edit</Link>
                                </div>

                                {skills.length === 0 ? (
                                    <p>No skills added yet.</p>
                                ) : (
                                    <div className="dashboard-tags">
                                        {skills.map(skill => (
                                            <span key={skill.id}>
                                                {skill.name}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </section>

                            <section className="box dashboard-section">
                                <div className="dashboard-section-heading">
                                    <h2 className="box-header">Certificates</h2>
                                    <Link to="/account/setup">Edit</Link>
                                </div>

                                {certificates.length === 0 ? (
                                    <p>No certificates added yet.</p>
                                ) : (
                                    certificates.map(cert => (
                                        <div className="dashboard-list-item" key={cert.id}>
                                            <h3>{cert.name}</h3>
                                            <p>{cert.issuer || "Issuer not specified"}</p>
                                            {cert.issue_year && <p>{cert.issue_year}</p>}
                                        </div>
                                    ))
                                )}

                                <Link to="/resources/certificates">
                                    Explore Certificate Programs
                                </Link>
                            </section>
                        </div>

                        {/* Career preferences */}
                        <section className="box dashboard-section">
                            <div className="dashboard-section-heading">
                                <h2 className="box-header">Job Preferences</h2>
                                <Link to="/account/setup">Edit Preferences</Link>
                            </div>

                            {jobPreferences.length === 0 ? (
                                <p>
                                    You haven't added any career preferences yet.
                                </p>
                            ) : (
                                jobPreferences.map(job => (
                                    <div className="dashboard-list-item" key={job.id}>
                                        <h3>{job.role}</h3>
                                        <p>
                                            {[
                                                job.location,
                                                job.employment_type
                                            ].filter(Boolean).join(" • ") || "No additional preferences"}
                                        </p>
                                        {job.min_salary != null && (
                                            <p>
                                                Minimum salary: ${Number(job.min_salary).toLocaleString()}
                                            </p>
                                        )}
                                    </div>
                                ))
                            )}
                        </section>

                        {/* Portfolio and project tracking */}
                        <section className="box dashboard-section">
                            <div className="dashboard-section-heading">
                                <h2 className="box-header">My Portfolio & Projects</h2>
                                <Link to="/portfolio">View Full Portfolio</Link>
                            </div>

                            <p>
                                You currently have {projects.length} project
                                {projects.length === 1 ? "" : "s"} in your portfolio.
                            </p>

                            {recentProjects.length === 0 ? (
                                <p>You haven't added any projects yet.</p>
                            ) : (
                                <div className="dashboard-projects">
                                    {recentProjects.map(project => (
                                        <div className="dashboard-project" key={project.id}>
                                            {project.images?.[0]?.url && (
                                                <img
                                                    src={project.images[0].url}
                                                    alt={project.title}
                                                />
                                            )}

                                            <div className="dashboard-project-details">
                                                <h3>{project.title}</h3>
                                                <p>{project.subject}</p>
                                                <p>
                                                    {project.description || "No description provided."}
                                                </p>
                                                <small>
                                                    Last updated: {formatDate(project.updated_at || project.created_at)}
                                                </small>

                                                <div>
                                                    <Link to={`/projects/${project.id}/edit`}>
                                                        Edit Project
                                                    </Link>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div className="dashboard-project-actions">
                                <Link to="/projects/new">+ Add a Project</Link>
                                <Link to="/portfolio">Manage Portfolio</Link>
                            </div>
                        </section>
                    </>
                )}
            </div>
        </main>
    );
}

export default Dashboard;
