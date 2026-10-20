import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import "./portfolio.css";
import "./SharedPortfolio.css";
import Project from "../components/Projects/project";
import { getSharedPortfolio } from "../lib/api";
import { toProjectProps } from "../lib/projects";

function formatDate(isoDate) {
    if (!isoDate) return "";
    return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

// Read-only portfolio for visitors with a share link (R17). No login needed.
function SharedPortfolio({ darkMode }) {
    const { shareToken } = useParams();
    const [portfolio, setPortfolio] = useState(null);
    const [error, setError] = useState("");

    useEffect(() => {
        getSharedPortfolio(shareToken)
            .then(setPortfolio)
            .catch((err) => setError(err.message));
    }, [shareToken]);

    if (error) {
        return <main><p className="box shared-section">{error}</p></main>;
    }
    if (!portfolio) {
        return <main><p className="box shared-section">Loading portfolio...</p></main>;
    }

    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">{portfolio.name}</h1>
                {portfolio.headline && <p>{portfolio.headline}</p>}
                {portfolio.location && <p>{portfolio.location}</p>}
            </div>

            {(portfolio.bio || portfolio.career_interests.length > 0 || portfolio.links.length > 0) && (
                <section className="box shared-section">
                    <h2>About</h2>
                    {portfolio.bio && <p>{portfolio.bio}</p>}
                    {portfolio.career_interests.length > 0 && (
                        <p><strong>Career interests:</strong> {portfolio.career_interests.join(", ")}</p>
                    )}
                    {portfolio.links.map((link) => (
                        <p key={link.id}><a href={link.url} target="_blank" rel="noopener noreferrer">{link.label}</a></p>
                    ))}
                </section>
            )}

            {portfolio.education.length > 0 && (
                <section className="box shared-section">
                    <h2>Education</h2>
                    {portfolio.education.map((edu) => (
                        <div key={edu.id} className="shared-entry">
                            <h3>{[edu.degree, edu.major].filter(Boolean).join(" in ") || edu.school_name}</h3>
                            <p>
                                {edu.school_name}
                                {edu.graduation_date && ` · ${edu.is_expected ? "Expected" : "Graduated"} ${formatDate(edu.graduation_date)}`}
                            </p>
                            {edu.coursework.length > 0 && <p>Coursework: {edu.coursework.join(", ")}</p>}
                        </div>
                    ))}
                </section>
            )}

            {portfolio.certificates.length > 0 && (
                <section className="box shared-section">
                    <h2>Certificates</h2>
                    {portfolio.certificates.map((cert) => (
                        <div key={cert.id} className="shared-entry">
                            <h3>
                                {cert.credential_url
                                    ? <a href={cert.credential_url} target="_blank" rel="noopener noreferrer">{cert.name}</a>
                                    : cert.name}
                            </h3>
                            {(cert.issuer || cert.issue_year) && (
                                <p>{[cert.issuer, cert.issue_year].filter(Boolean).join(" · ")}</p>
                            )}
                        </div>
                    ))}
                </section>
            )}

            {portfolio.skills.length > 0 && (
                <section className="box shared-section">
                    <h2>Skills</h2>
                    <ul className="shared-skills">
                        {portfolio.skills.map((skill) => <li key={skill.id}>{skill.name}</li>)}
                    </ul>
                </section>
            )}

            {portfolio.experiences.length > 0 && (
                <section className="box shared-section">
                    <h2>Experience</h2>
                    {portfolio.experiences.map((exp) => (
                        <div key={exp.id} className="shared-entry">
                            <h3>{exp.position} · {exp.organization}</h3>
                            <p>
                                {formatDate(exp.start_date)}
                                {exp.start_date && " – "}
                                {exp.is_current ? "Present" : formatDate(exp.end_date)}
                            </p>
                            {exp.description && <p>{exp.description}</p>}
                        </div>
                    ))}
                </section>
            )}

            <div className="portfolio-body">
                <div className="project-box">
                    <h2>Projects</h2>
                    {portfolio.projects.length === 0 && <p>No projects yet.</p>}
                    {portfolio.projects.map((project) => (
                        <Project key={project.id} {...toProjectProps(project)} darkMode={darkMode}/>
                    ))}
                </div>
            </div>
        </main>
    );
}

export default SharedPortfolio;
