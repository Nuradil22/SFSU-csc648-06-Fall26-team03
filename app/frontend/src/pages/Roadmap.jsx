import { useState } from "react";

import "./Roadmap.css";
import quotes from "../data/inspoQuotes.js";
import ChatWindow from "../components/Chat/ChatWindow.jsx";

// Placeholder until backend catches up, but figured it would look something like this

const sampleMilestones = [
    {
        id: 1,
        title: "Strengthen your programming foundation",
        category: "Coursework",
        description:
            "Build a strong understanding of programming fundamentals, data structures, and algorithms.",
        recommendations: [
            "Review your university's data structures course options.",
            "Practice programming problems regularly.",
            "Review object-oriented programming concepts."
        ],
        source: "University course recommendation",
        status: "Foundation"
    },
    {
        id: 2,
        title: "Build a full-stack application",
        category: "Portfolio",
        description:
            "Create a project that demonstrates your ability to build and connect a frontend and backend.",
        recommendations: [
            "Build an application using React.",
            "Connect it to a backend API.",
            "Document the project and add it to your portfolio."
        ],
        source: "AI portfolio recommendation",
        status: "Practical experience"
    },
    {
        id: 3,
        title: "Develop software testing skills",
        category: "Technical skills",
        description:
            "Learn how to test applications and identify problems before they reach users.",
        recommendations: [
            "Learn unit testing fundamentals.",
            "Explore testing tools for your preferred programming language.",
            "Add tests to an existing portfolio project."
        ],
        source: "AI skill recommendation",
        status: "Technical development"
    },
    {
        id: 4,
        title: "Explore industry certifications",
        category: "Certification",
        description:
            "Research credentials that may complement your education and demonstrate relevant skills.",
        recommendations: [
            "Compare certification options related to software development.",
            "Review official provider requirements and costs.",
            "Decide whether a certification supports your career goals."
        ],
        source: "Certification research needed",
        status: "Professional development"
    },
    {
        id: 5,
        title: "Prepare for internship applications",
        category: "Career preparation",
        description:
            "Prepare your resume, portfolio, and interview skills for entry-level opportunities.",
        recommendations: [
            "Review your resume.",
            "Make sure your portfolio projects are documented.",
            "Practice technical and behavioral interview questions."
        ],
        source: "AI career recommendation",
        status: "Career readiness"
    }
];

function getInspo() {
    return quotes[Math.floor(Math.random() * quotes.length)];
}

function Roadmap() {
    const [quote] = useState(getInspo);
    const [milestones, setMilestones] = useState(sampleMilestones);

    const completedCount = milestones.filter(
        (milestone) => milestone.completed
    ).length;

    const progress = milestones.length
        ? Math.round((completedCount / milestones.length) * 100)
        : 0;

    function toggleMilestone(id) {
        setMilestones((current) =>
            current.map((milestone) =>
                milestone.id === id
                    ? { ...milestone, completed: !milestone.completed }
                    : milestone
            )
        );
    }

    return (
        <main className="roadmap-page">
            <div className="banner">
                <h1 className="banner-title">Your Career Roadmap</h1>
                {quote && (
                    <>
                        <p>"{quote.line}"</p>
                        <p>- {quote.cred}</p>
                    </>
                )}
            </div>

            <div className="roadmap-content">

                {/* Career goal and progress */}
                <section className="roadmap-overview box">
                    <div>
                        <p className="roadmap-eyebrow">YOUR CURRENT CAREER GOAL</p>
                        <h2>Software Engineer</h2>
                        <p className="roadmap-muted">
                            A sample personalized roadmap based on your education,
                            career interests, and portfolio.
                        </p>
                    </div>

                    <div className="roadmap-progress">
                        <div className="roadmap-progress-heading">
                            <span>Roadmap progress</span>
                            <strong>{progress}%</strong>
                        </div>

                        <div
                            className="roadmap-progress-track"
                            role="progressbar"
                            aria-valuenow={progress}
                            aria-valuemin="0"
                            aria-valuemax="100"
                        >
                            <div
                                className="roadmap-progress-fill"
                                style={{ width: `${progress}%` }}
                            />
                        </div>

                        <p className="roadmap-muted">
                            {completedCount} of {milestones.length} milestones completed
                        </p>
                    </div>
                </section>

                <div className="roadmap-layout">

                    {/* Main roadmap */}
                    <section className="roadmap-main box">
                        <div className="roadmap-section-heading">
                            <div>
                                <p className="roadmap-eyebrow">YOUR ACTION PLAN</p>
                                <h2>Roadmap Milestones</h2>
                            </div>
                            <span className="roadmap-count">
                                {milestones.length} steps
                            </span>
                        </div>

                        <div className="milestone-list">
                            {milestones.map((milestone, index) => (
                                <article
                                    className={`milestone-card ${
                                        milestone.completed ? "completed" : ""
                                    }`}
                                    key={milestone.id}
                                >
                                    <div className="milestone-number">
                                        {milestone.completed ? "✓" : index + 1}
                                    </div>

                                    <div className="milestone-content">
                                        <div className="milestone-title-row">
                                            <div>
                                                <span className="milestone-category">
                                                    {milestone.category}
                                                </span>
                                                <h3>{milestone.title}</h3>
                                            </div>

                                            <label className="milestone-complete">
                                                <input
                                                    type="checkbox"
                                                    checked={Boolean(milestone.completed)}
                                                    onChange={() =>
                                                        toggleMilestone(milestone.id)
                                                    }
                                                />
                                                <span>
                                                    {milestone.completed
                                                        ? "Completed"
                                                        : "Mark complete"}
                                                </span>
                                            </label>
                                        </div>

                                        <p>{milestone.description}</p>

                                        <details className="milestone-details">
                                            <summary>View recommended actions</summary>

                                            <ul>
                                                {milestone.recommendations.map(
                                                    (recommendation, i) => (
                                                        <li key={i}>{recommendation}</li>
                                                    )
                                                )}
                                            </ul>
                                        </details>

                                        <span className="milestone-source">
                                            <span>Source:</span> {milestone.source}
                                        </span>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </section>

                    {/* Sidebar */}
                    <aside className="roadmap-sidebar">

                        <section className="box next-step-card">
                            <p className="roadmap-eyebrow">UP NEXT</p>
                            <h2>Your next step</h2>
                            <p>
                                {milestones.find((milestone) => !milestone.completed)
                                    ?.title || "You've completed every milestone!"}
                            </p>
                            <p className="roadmap-muted">
                                Work through your milestones at your own pace.
                            </p>
                        </section>

                        <section className="box roadmap-resources">
                            <h2>Roadmap Resources</h2>
                            <p>
                                Recommendations will eventually include links to
                                official university catalogs, certification providers,
                                and other trusted resources.
                            </p>

                            <div className="source-legend">
                                <span className="source-dot official" />
                                Official university or certification source
                            </div>
                            <div className="source-legend">
                                <span className="source-dot verified" />
                                Verified supporting resource
                            </div>
                            <div className="source-legend">
                                <span className="source-dot suggestion" />
                                AI-generated suggestion
                            </div>
                        </section>

                        <section className="box saved-roadmaps">
                            <h2>Saved Roadmaps</h2>
                            <div className="saved-roadmaps-empty">
                                <span className="saved-roadmaps-icon">📄</span>
                                <p>No saved roadmaps yet.</p>
                                <span>
                                    Exported PDF roadmaps will appear here.
                                </span>
                            </div>

                            <button
                                type="button"
                                className="roadmap-export-button"
                                disabled
                                title="PDF export will be connected later"
                            >
                                <span>↓</span> Export roadmap as PDF
                            </button>
                        </section>
                    </aside>
                </div>

                {/* Career assistant */}
                <section className="box roadmap-assistant">
                    <div className="roadmap-section-heading">
                        <div>
                            <p className="roadmap-eyebrow">NEED SOME GUIDANCE?</p>
                            <h2>Career Assistant</h2>
                            <p className="roadmap-muted">
                                Ask questions about your career goals, education,
                                certifications, or next steps.
                            </p>
                        </div>
                    </div>

                    <ChatWindow />
                </section>
            </div>
        </main>
    );
}

export default Roadmap;