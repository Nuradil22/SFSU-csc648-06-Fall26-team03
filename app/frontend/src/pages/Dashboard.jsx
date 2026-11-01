import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    getToken,
    getCurrentUser,
    getMyPortfolio,
    getMyProjects
} from "../lib/api";

import "./Dashboard.css";

function formatDate(date) {
    if (!date) return "Date unavailable";

    const parsed = new Date(date);

    if (Number.isNaN(parsed.getTime())) return "Date unavailable";

    return parsed.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric"
    });
}

function Dashboard({ darkMode }) {
    const [user, setUser] = useState(() => getCurrentUser());
    const [portfolio, setPortfolio] = useState(null);
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let isMounted = true;

        async function loadDashboard() {
            if (!getToken()) {
                setError("Please log in to view your dashboard.");
                setLoading(false);
                return;
            }

            try {
                const [portfolioResult, projectsResult] =
                    await Promise.allSettled([
                        getMyPortfolio(),
                        getMyProjects()
                    ]);

                if (!isMounted) return;

                if (portfolioResult.status === "fulfilled") {
                    setPortfolio(portfolioResult.value);
                }

                if (projectsResult.status === "fulfilled") {
                    const result = projectsResult.value;
                    setProjects(Array.isArray(result) ? result : []);
                }

                if (
                    portfolioResult.status === "rejected" &&
                    projectsResult.status === "rejected"
                ) {
                    setError("Unable to load your dashboard. Please try again.");
                } else if (portfolioResult.status === "rejected") {
                    console.error("Portfolio request failed:", portfolioResult.reason);
                } else if (projectsResult.status === "rejected") {
                    console.error("Projects request failed:", projectsResult.reason);
                }

            } catch (err) {
                if (isMounted) {
                    setError(err.message || "Something went wrong.");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        }

        loadDashboard();

        return () => {
            isMounted = false;
        };
    }, []);

    const displayName =
        portfolio?.name ||
        user?.name ||
        "there";

    // Portfolio data
    const education = portfolio?.education || [];
    const skills = portfolio?.skills || [];
    const experiences = portfolio?.experiences || [];
    const certificates = portfolio?.certificates || [];

    // Profile completion
    const profileItems = [
        {
            label: "Basic information",
            complete: Boolean(portfolio?.name && portfolio?.email)
        },
        {
            label: "Professional headline",
            complete: Boolean(portfolio?.headline?.trim())
        },
        {
            label: "Biography",
            complete: Boolean(portfolio?.bio?.trim())
        },
        {
            label: "Profile picture",
            complete: Boolean(portfolio?.profile_image_url)
        },
        {
            label: "Add your skills",
            complete: skills.length > 0
        },
        {
            label: "Add your education",
            complete: education.length > 0
        },
        {
            label: "Add your experience",
            complete: experiences.length > 0
        },
        {
            label: "Add a certificate",
            complete: certificates.length > 0
        }
    ];

    const completedItems = profileItems.filter(
        item => item.complete
    ).length;

    const profileProgress = Math.round(
        (completedItems / profileItems.length) * 100
    );

    // Sort projects by last updated
    const recentProjects = [...projects]
        .sort((a, b) => {
            const dateA = new Date(a.updated_at || a.created_at || 0);
            const dateB = new Date(b.updated_at || b.created_at || 0);
            return dateB - dateA;
        })
        .slice(0, 3);

    if (loading) {
        return (
            <main className={`dashboard ${darkMode ? "dark" : ""}`}>
                <div className="dashboard-message">
                    <h2>Loading your dashboard...</h2>
                    <p>Getting your projects and profile information.</p>
                </div>
            </main>
        );
    }

    if (error && !portfolio && projects.length === 0) {
        return (
            <main className={`dashboard ${darkMode ? "dark" : ""}`}>
                <div className="dashboard-message">
                    <h2>Unable to load dashboard</h2>
                    <p>{error}</p>
                    <Link to="/login" className="dashboard-primary-btn">
                        Go to Login
                    </Link>
                </div>
            </main>
        );
    }

    return (
        <main className={`dashboard ${darkMode ? "dark" : ""}`}>

            {/* Welcome Header */}
            <section className="dashboard-welcome">
                <div className="welcome-user">
                    {portfolio?.profile_image_url && (
                        <img
                            src={portfolio.profile_image_url}
                            alt="Profile"
                            className="dashboard-profile-image"
                        />
                    )}

                    <div>
                        <p className="dashboard-eyebrow">
                            YOUR PROJECTORY DASHBOARD
                        </p>

                        <h1>Welcome back, {displayName}!</h1>

                        <p className="welcome-subtitle">
                            {portfolio?.headline ||
                                "Keep building your portfolio and showcasing your work."}
                        </p>
                    </div>
                </div>

                <div className="welcome-actions">
                    <Link to="/create-project" className="dashboard-primary-btn">
                        + Create Project
                    </Link>

                    <Link to="/portfolio" className="dashboard-secondary-btn">
                        View Portfolio
                    </Link>
                </div>
            </section>

            {/* Statistics */}
            <section className="dashboard-stats">

                <div className="stat-card">
                    <div className="stat-icon">📁</div>
                    <div>
                        <p className="stat-number">{projects.length}</p>
                        <p className="stat-label">Total Projects</p>
                        <p className="stat-description">Your projects</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">🏆</div>
                    <div>
                        <p className="stat-number">{certificates.length}</p>
                        <p className="stat-label">Certificates</p>
                        <p className="stat-description">Credentials earned</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">⚡</div>
                    <div>
                        <p className="stat-number">{skills.length}</p>
                        <p className="stat-label">Skills</p>
                        <p className="stat-description">Your listed skills</p>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon">👤</div>
                    <div>
                        <p className="stat-number">{profileProgress}%</p>
                        <p className="stat-label">Profile Complete</p>
                        <p className="stat-description">Keep it up!</p>
                    </div>
                </div>

            </section>

            {/* Main Content */}
            <section className="dashboard-content">

                {/* Recent Projects */}
                <div className="dashboard-panel projects-panel">
                    <div className="panel-heading">
                        <div>
                            <h2>Recent Projects</h2>
                            <p>Your latest work in Projectory</p>
                        </div>

                        <Link to="/portfolio" className="panel-link">
                            View All →
                        </Link>
                    </div>

                    <div className="recent-projects">
                        {recentProjects.length > 0 ? (
                            recentProjects.map(project => (
                                <article
                                    className="recent-project-card"
                                    key={project.id}
                                >
                                    <div className="project-thumbnail">
                                        {project.images?.[0]?.url ? (
                                            <img
                                                src={project.images[0].url}
                                                alt={project.images[0].label || project.title}
                                            />
                                        ) : (
                                            <span>📁</span>
                                        )}
                                    </div>

                                    <div className="project-details">
                                        <h3>{project.title}</h3>

                                        <p>
                                            {project.subject || "Personal Project"}
                                        </p>

                                        <p className="project-date">
                                            Updated {formatDate(
                                                project.updated_at ||
                                                project.created_at
                                            )}
                                        </p>
                                    </div>
                                </article>
                            ))
                        ) : (
                            <p className="dashboard-empty">
                                You haven't created any projects yet.
                                Start building your portfolio!
                            </p>
                        )}
                    </div>

                    <Link to="/create-project" className="add-project-link">
                        + Add another project
                    </Link>
                </div>

                {/* Profile Completion */}
                <div className="dashboard-panel profile-panel">
                    <div className="panel-heading">
                        <div>
                            <h2>Complete Your Profile</h2>
                            <p>Help others get to know you.</p>
                        </div>
                    </div>

                    <div className="progress-summary">
                        <span>Profile progress</span>
                        <strong>{profileProgress}%</strong>
                    </div>

                    <div className="progress-track">
                        <div
                            className="progress-fill"
                            style={{ width: `${profileProgress}%` }}
                        />
                    </div>

                    <div className="profile-checklist">
                        {profileItems.map(item => (
                            <div
                                className={`checklist-item ${
                                    item.complete ? "completed" : ""
                                }`}
                                key={item.label}
                            >
                                <span>{item.complete ? "✓" : "○"}</span>
                                <p>{item.label}</p>
                            </div>
                        ))}
                    </div>

                    <Link
                        to="/account/setup"
                        className="complete-profile-btn"
                    >
                        Edit Profile →
                    </Link>
                </div>

            </section>

            {/* Bottom Content */}
            <section className="dashboard-bottom">

                {/* Resources */}
                <div className="dashboard-panel resources-panel">
                    <div className="panel-heading">
                        <div>
                            <h2>Explore Resources</h2>
                            <p>Find ways to grow your skills.</p>
                        </div>
                    </div>

                    <Link
                        to="/resources/certificates"
                        className="resource-item"
                    >
                        <div className="resource-icon">🎓</div>

                        <div>
                            <h3>Certificates</h3>
                            <p>
                                Discover credentials to strengthen your profile.
                            </p>
                        </div>

                        <span>→</span>
                    </Link>

                    <Link
                        to="/resources/certificates"
                        className="resource-item"
                    >
                        <div className="resource-icon">💡</div>

                        <div>
                            <h3>Learning Opportunities</h3>
                            <p>
                                Explore new skills and areas of interest.
                            </p>
                        </div>

                        <span>→</span>
                    </Link>
                </div>

                {/* Portfolio Summary */}
                <div className="dashboard-panel activity-panel">
                    <div className="panel-heading">
                        <div>
                            <h2>Your Portfolio</h2>
                            <p>A quick look at your professional profile.</p>
                        </div>
                    </div>

                    <div className="portfolio-summary-item">
                        <span>🎓</span>
                        <div>
                            <h3>Education</h3>
                            <p>{education.length} entries</p>
                        </div>
                    </div>

                    <div className="portfolio-summary-item">
                        <span>💼</span>
                        <div>
                            <h3>Experience</h3>
                            <p>{experiences.length} entries</p>
                        </div>
                    </div>

                    <div className="portfolio-summary-item">
                        <span>🔗</span>
                        <div>
                            <h3>Profile Links</h3>
                            <p>{portfolio?.links?.length || 0} links</p>
                        </div>
                    </div>

                    <Link to="/account/setup" className="add-project-link">
                        Manage Your Profile →
                    </Link>
                </div>

            </section>

        </main>
    );
}

export default Dashboard;
