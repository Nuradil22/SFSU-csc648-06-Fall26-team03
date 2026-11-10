import { useCallback, useEffect, useState } from "react";

import "./Roadmap.css";
import quotes from "../data/inspoQuotes.js";
import ChatWindow from "../components/Chat/ChatWindow.jsx";
import ResourceList from "../components/Roadmap/ResourceList.jsx";
import { getCareerRoadmap, getToken, updateCareerRoadmap } from "../lib/api";

// The milestones shown here are the user's approved AI roadmap
// (GET /career/roadmap): {title, goals: [{id, title, milestones: [{id, title, completed}]}]}.
// Each goal is shown as one milestone card; its milestones are the card's
// recommended actions. AI-generated roadmaps only appear here after the user
// approves them in the Career Assistant below.

function getInspo() {
    return quotes[Math.floor(Math.random() * quotes.length)];
}

function goalProgress(goal) {
    const steps = goal.milestones || [];
    const done = steps.filter((step) => step.completed).length;
    return { done, total: steps.length, complete: steps.length > 0 && done === steps.length };
}

function Roadmap() {
    const [quote] = useState(getInspo);
    const [roadmap, setRoadmap] = useState(null);
    const [isLoadingRoadmap, setIsLoadingRoadmap] = useState(() => Boolean(getToken()));
    const [isSaving, setIsSaving] = useState(false);
    const [roadmapError, setRoadmapError] = useState(null);

    const isLoggedIn = Boolean(getToken());

    // Reload after the user approves an AI proposal in the chat.
    const loadRoadmap = useCallback(async () => {
        try {
            setRoadmap(await getCareerRoadmap());
            setRoadmapError(null);
        } catch (error) {
            console.error("Roadmap load error:", error);
            setRoadmapError(error.message);
        }
    }, []);

    // Initial load of the user's approved roadmap.
    useEffect(() => {
        if (!getToken()) return;

        getCareerRoadmap()
            .then((data) => {
                setRoadmap(data);
                setRoadmapError(null);
            })
            .catch((error) => {
                console.error("Roadmap load error:", error);
                setRoadmapError(error.message);
            })
            .finally(() => setIsLoadingRoadmap(false));
    }, []);

    const goals = roadmap?.goals || [];
    const allSteps = goals.flatMap((goal) => goal.milestones || []);
    const completedCount = allSteps.filter((step) => step.completed).length;

    const progress = allSteps.length
        ? Math.round((completedCount / allSteps.length) * 100)
        : 0;

    const nextStep = allSteps.find((step) => !step.completed);

    // Owner edits to the approved roadmap are saved with PUT /career/roadmap.
    async function saveGoals(nextGoals) {
        if (!roadmap || isSaving) return;

        const previous = roadmap;
        const next = { ...roadmap, goals: nextGoals };

        setRoadmap(next);
        setIsSaving(true);
        setRoadmapError(null);

        try {
            setRoadmap(await updateCareerRoadmap(next));
        } catch (error) {
            console.error("Roadmap save error:", error);
            setRoadmap(previous);
            setRoadmapError(error.message);
        } finally {
            setIsSaving(false);
        }
    }

    // Card checkbox: marks every action in the goal complete (or not).
    function toggleGoal(goalId) {
        saveGoals(
            goals.map((goal) => {
                if (goal.id !== goalId) return goal;
                const markDone = !goalProgress(goal).complete;
                return {
                    ...goal,
                    milestones: (goal.milestones || []).map((step) => ({
                        ...step,
                        completed: markDone
                    }))
                };
            })
        );
    }

    function toggleStep(goalId, stepId) {
        saveGoals(
            goals.map((goal) =>
                goal.id !== goalId
                    ? goal
                    : {
                        ...goal,
                        milestones: (goal.milestones || []).map((step) =>
                            step.id === stepId
                                ? { ...step, completed: !step.completed }
                                : step
                        )
                    }
            )
        );
    }

    let emptyMessage = null;
    if (!isLoggedIn) {
        emptyMessage = "Log in to see your personalized career roadmap.";
    } else if (isLoadingRoadmap) {
        emptyMessage = "Loading your roadmap...";
    } else if (!goals.length) {
        emptyMessage =
            "You don't have an approved roadmap yet. The Career Assistant below drafts one from your portfolio (or ask it for one); approve it to see it here.";
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
                        <h2>{roadmap?.title || "No roadmap yet"}</h2>
                        <p className="roadmap-muted">
                            {roadmap
                                ? "Your personalized roadmap, generated by AI from your education, career interests, and portfolio, and approved by you."
                                : "Your personalized roadmap will be based on your education, career interests, and portfolio."}
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
                            {completedCount} of {allSteps.length} milestones completed
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
                                {goals.length} steps
                            </span>
                        </div>

                        {roadmapError && (
                            <p className="chat-proposal-error" role="alert">
                                {roadmapError}
                            </p>
                        )}

                        {emptyMessage ? (
                            <p className="roadmap-muted">{emptyMessage}</p>
                        ) : (
                            <div className="milestone-list">
                                {goals.map((goal, index) => {
                                    const { done, total, complete } = goalProgress(goal);
                                    const steps = goal.milestones || [];

                                    return (
                                        <article
                                            className={`milestone-card ${
                                                complete ? "completed" : ""
                                            }`}
                                            key={goal.id}
                                        >
                                            <div className="milestone-number">
                                                {complete ? "✓" : index + 1}
                                            </div>

                                            <div className="milestone-content">
                                                <div className="milestone-title-row">
                                                    <div>
                                                        <span className="milestone-category">
                                                            {done} of {total} actions done
                                                        </span>
                                                        <h3>{goal.title}</h3>
                                                    </div>

                                                    <label className="milestone-complete">
                                                        <input
                                                            type="checkbox"
                                                            checked={complete}
                                                            disabled={isSaving || !total}
                                                            onChange={() => toggleGoal(goal.id)}
                                                        />
                                                        <span>
                                                            {complete
                                                                ? "Completed"
                                                                : "Mark complete"}
                                                        </span>
                                                    </label>
                                                </div>

                                                {steps.length > 0 && (
                                                    <details className="milestone-details">
                                                        <summary>View recommended actions</summary>

                                                        <ul>
                                                            {steps.map((step) => (
                                                                <li key={step.id}>
                                                                    <label>
                                                                        <input
                                                                            type="checkbox"
                                                                            checked={Boolean(step.completed)}
                                                                            disabled={isSaving}
                                                                            onChange={() =>
                                                                                toggleStep(goal.id, step.id)
                                                                            }
                                                                        />{" "}
                                                                        {step.title}
                                                                    </label>
                                                                    <ResourceList
                                                                        resources={step.resources}
                                                                        compact
                                                                    />
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </details>
                                                )}

                                                <span className="milestone-source">
                                                    <span>Source:</span> AI career recommendation (approved by you)
                                                </span>
                                            </div>
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </section>

                    {/* Sidebar */}
                    <aside className="roadmap-sidebar">

                        <section className="box next-step-card">
                            <p className="roadmap-eyebrow">UP NEXT</p>
                            <h2>Your next step</h2>
                            <p>
                                {!allSteps.length
                                    ? "Approve an AI roadmap to get your next step."
                                    : nextStep?.title || "You've completed every milestone!"}
                            </p>
                            <p className="roadmap-muted">
                                Work through your milestones at your own pace.
                            </p>
                        </section>

                        <section className="box roadmap-resources">
                            <h2>Roadmap Resources</h2>
                            <p>
                                Recommended actions can include courses, programs,
                                and certificates found by live research. Only links
                                returned by that research are shown.
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

                    <ChatWindow onRoadmapApproved={loadRoadmap} />
                </section>
            </div>
        </main>
    );
}

export default Roadmap;
