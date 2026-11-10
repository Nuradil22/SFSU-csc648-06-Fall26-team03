import { Link } from "react-router-dom";

// Where each required item is already added in Projectory. These are the
// existing dashboard destinations ("Manage Education", "Manage Skills",
// "Edit Preferences" -> Account Setup; "+ Add a Project" -> project editor).
const WHERE = {
    education: { to: "/account/setup", text: "Account Setup → Education & Degrees" },
    skills: { to: "/account/setup", text: "Account Setup → Skills" },
    career_goal: { to: "/account/setup", text: "Account Setup → Job Preferences" },
    projects: { to: "/projects/new", text: "Add a Project" }
};

// Shown in place of the chat input while the student's saved portfolio is
// missing what the assistant needs (GET /career/readiness). The assistant
// reads the portfolio from the account, so nothing is typed in here.
export default function PortfolioReadinessNotice({ missing }) {
    return (
        <div className="chat-readiness" role="status">
            <p className="chat-readiness-title">
                Let's finish your portfolio first
            </p>
            <p>
                I build advice and roadmaps from the information saved in your
                Projectory portfolio. Please add the following using your
                existing dashboard options. I'll pick it up automatically as
                soon as it's saved.
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
