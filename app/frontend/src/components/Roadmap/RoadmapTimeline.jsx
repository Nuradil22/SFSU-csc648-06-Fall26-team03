import { useState } from "react";
import "./RoadmapTimeline.css";
import ResourceList from "./ResourceList";
import { approvedRoadmapNotice } from "../../lib/educational";

// Renders a roadmap ({title, goals: [{id, title, kind?, milestones: [{id, title, completed, step?, resources?}]}]})
// exactly as the backend returns it. No roadmap content is defined here.
// step "learn" / "apply" (competency goals) is shown as a small label; older
// roadmaps without it render as before.
//
// Goals are connected nodes on a vertical timeline; each goal's milestones
// branch off it. Click a goal to collapse/expand its milestones. When
// onToggleMilestone is given (approved roadmap), milestones can be ticked off;
// an approved roadmap without verified educational offerings (educational:
// false) gets an informational note, and keeps its progress and ticking. Drafts
// (no onToggleMilestone) get their note from RoadmapProposalCard instead.
const STEP_LABELS = { learn: "Learn", apply: "Apply" };

function StepLabel({ step }) {
  const label = STEP_LABELS[step];
  return label ? <small className={`roadmap-step is-${step}`}>{label}</small> : null;
}

export default function RoadmapTimeline({ roadmap, onToggleMilestone, disabled = false }) {
  const [collapsed, setCollapsed] = useState({});

  if (!roadmap?.goals?.length) return null;

  const notice = onToggleMilestone ? approvedRoadmapNotice(roadmap) : null;

  function toggleGoal(goalId) {
    setCollapsed(prev => ({ ...prev, [goalId]: !prev[goalId] }));
  }

  return (
    <div className="roadmap-timeline">
      <h3 className="roadmap-title">{roadmap.title}</h3>

      {notice && <p className="roadmap-unverified" role="note">{notice}</p>}

      <ol className="roadmap-goals">
        {roadmap.goals.map((goal, index) => {
          const milestones = goal.milestones || [];
          const done = milestones.filter(m => m.completed).length;
          const isOpen = !collapsed[goal.id];
          const isComplete = milestones.length > 0 && done === milestones.length;

          return (
            <li
              key={goal.id}
              className={`roadmap-goal${isComplete ? " is-complete" : ""}`}
            >
              <span className="roadmap-node" aria-hidden="true">{index + 1}</span>

              <button
                type="button"
                className="roadmap-goal-head"
                onClick={() => toggleGoal(goal.id)}
                aria-expanded={isOpen}
              >
                <span className="roadmap-goal-title">{goal.title}</span>
                <span className="roadmap-goal-progress">
                  {done}/{milestones.length} {isOpen ? "▾" : "▸"}
                </span>
              </button>

              {/* Which of the student's own goals this learning stage serves
                  (newer roadmaps only). */}
              {goal.serves && (
                <p className="roadmap-goal-serves">Supports your goal: {goal.serves}</p>
              )}

              {isOpen && milestones.length > 0 && (
                <ul className="roadmap-milestones">
                  {milestones.map(milestone => (
                    <li
                      key={milestone.id}
                      className={`roadmap-milestone${milestone.completed ? " is-done" : ""}`}
                    >
                      {onToggleMilestone ? (
                        <label>
                          <input
                            type="checkbox"
                            checked={Boolean(milestone.completed)}
                            disabled={disabled}
                            onChange={() => onToggleMilestone(goal.id, milestone.id)}
                          />
                          <StepLabel step={milestone.step} />
                          <span>{milestone.title}</span>
                        </label>
                      ) : (
                        <>
                          <StepLabel step={milestone.step} />
                          <span>{milestone.title}</span>
                        </>
                      )}
                      <ResourceList resources={milestone.resources} compact />
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
