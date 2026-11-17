import "./ModelComparison.css";

function ValidationBadge({ validation }) {
    if (!validation) return null;

    const labels = {
        verified: "Verified in catalog",
        unverified: "Not in catalog",
        title_mismatch: "Title mismatch",
        not_applicable: "Not a catalog course",
    };

    return (
        <span className={`validation-badge validation-${validation.status}`}>
            {labels[validation.status] || validation.status}
        </span>
    );
}

function RecommendationCard({ rec }) {
    const issue = rec.validation?.issue;

    return (
        <li className="compare-rec">
            <div className="compare-rec-head">
                <strong>
                    {rec.course_code ? `${rec.course_code} — ` : ""}
                    {rec.title}
                </strong>
                <ValidationBadge validation={rec.validation} />
            </div>
            <p className="compare-rec-rationale">{rec.rationale}</p>
            {rec.validation?.catalog_prerequisites && (
                <p className="compare-rec-prereq">
                    Recorded prerequisites: {rec.validation.catalog_prerequisites}
                </p>
            )}
            {issue && <p className="compare-rec-issue">{issue}</p>}
        </li>
    );
}

// Renders the backend's two-model comparison result. Each column shows which
// model produced the recommendations; agreement is never presented as proof
// of accuracy.
export default function ModelComparison({ data }) {
    const okModels = data.models?.filter((m) => m.status === "ok") || [];
    const failed = data.models?.filter((m) => m.status === "error") || [];
    const comparison = data.comparison;

    return (
        <div className="message-row assistant-message">
            <div className="message-avatar" aria-hidden="true">
                AI
            </div>
            <div className="message-bubble compare-panel">
                <h4 className="compare-heading">Two-model comparison</h4>
                <p className="compare-question">{data.question}</p>

                {failed.map((m) => (
                    <p key={m.label} className="compare-error">
                        {m.label} could not respond: {m.error}
                    </p>
                ))}

                <div className="compare-columns">
                    {okModels.map((m) => (
                        <section key={m.label} className="compare-column">
                            <h5>{m.label}</h5>
                            <ul>
                                {m.recommendations.map((rec, i) => (
                                    <RecommendationCard key={i} rec={rec} />
                                ))}
                                {m.recommendations.length === 0 && (
                                    <li>No recommendations returned.</li>
                                )}
                            </ul>
                        </section>
                    ))}
                </div>

                {comparison && (
                    <div className="compare-summary">
                        {comparison.shared.length > 0 ? (
                            <p>
                                <strong>Both models suggested:</strong>{" "}
                                {comparison.shared.join(", ")}
                            </p>
                        ) : (
                            <p>The two models suggested different courses.</p>
                        )}
                        {Object.entries(comparison.only).map(([label, codes]) =>
                            codes.length > 0 && (
                                <p key={label}>
                                    <strong>Only {label}:</strong> {codes.join(", ")}
                                </p>
                            )
                        )}
                    </div>
                )}

                <p className="compare-disclaimer">{data.disclaimer}</p>
            </div>
        </div>
    );
}
