import { useState } from "react";
import "./RoadmapTimeline.css";

// Renders a roadmap ({title, goals: [{id, title, milestones: [{id, title, completed}]}]})
// exactly as the backend returns it. No roadmap content is defined here.
//
// Goals are connected nodes on a vertical timeline; each goal's milestones
// branch off it. Click a goal to collapse/expand its milestones. When
// onToggleMilestone is given (approved roadmap), milestones can be ticked off.
export default function RoadmapTimeline({ roadmap, onToggleMilestone, disabled = false }) {
  const [collapsed, setCollapsed] = useState({});

  if (!roadmap?.goals?.length) return null;

  function toggleGoal(goalId) {
    setCollapsed(prev => ({ ...prev, [goalId]: !prev[goalId] }));
  }

  return (
    <div className="roadmap-timeline">
      <h3 className="roadmap-title">{roadmap.title}</h3>

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
                          <span>{milestone.title}</span>
                        </label>
                      ) : (
                        <span>{milestone.title}</span>
                      )}
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
