import { Link } from "react-router-dom";

// Where each required item is already added in Projectory: the existing
// dashboard destinations ("Manage Education", "Manage Skills", "Edit
// Preferences" -> Account Setup). The major goes in the Degree box there
// (e.g. "B.A. Undecided").
const WHERE = {
    education: { to: "/account/setup", text: "Account Setup → Education & Degrees" },
    major: { to: "/account/setup", text: "Account Setup → Education & Degrees" },
    career_goal: { to: "/account/setup", text: "Account Setup → Job Preferences" },
    skills: { to: "/account/setup", text: "Account Setup → Skills" }
};

// Shown above the chat while the saved portfolio is missing what a
// personalized roadmap needs (GET /career/readiness). The chat itself stays
// available; the assistant reads the portfolio from the account, so nothing
// is typed in here.
export default function PortfolioReadinessNotice({ missing }) {
    return (
        <div className="chat-readiness" role="status">
            <p className="chat-readiness-title">
                A few details before your personalized roadmap
            </p>
            <p>
                You can ask me anything now. To build a roadmap for you, I need
                the following saved in your Projectory portfolio. Projects, work
                experience, and certificates are optional. I'll pick up your
                changes automatically as soon as they're saved.
            </p>

            <ul className="chat-readiness-list">
                {missing.map((item) => {
                    const where = WHERE[item.key];

                    return (
                        <li key={item.key}>
                            <span>{item.label}</span>
                            {where && <Link to={where.to}>{where.text}</Link>}
                        </li>
                    );
                })}
            </ul>

            <Link className="chat-readiness-dashboard" to="/account/dashboard">
                Go to your Dashboard
            </Link>
        </div>
    );
}
