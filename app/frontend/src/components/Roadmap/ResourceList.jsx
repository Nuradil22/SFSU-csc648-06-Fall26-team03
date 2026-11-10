import "./ResourceList.css";

// Verified learning resources ({title, url, provider?, description?, type?})
// exactly as the backend returns them. The backend only keeps https links
// that came back from that request's web search; this re-checks the scheme
// before rendering a link. type "sfsu" marks official SFSU pages.
export default function ResourceList({ resources, compact = false }) {
  const items = (resources || []).filter(
    (item) => item?.title && typeof item.url === "string" && item.url.startsWith("https://")
  );

  if (!items.length) return null;

  return (
    <ul className={`resource-list${compact ? " is-compact" : ""}`}>
      {items.map((item) => (
        <li key={item.url} className="resource-item">
          <span
            className={`resource-dot ${item.type === "sfsu" ? "is-official" : "is-verified"}`}
            title={item.type === "sfsu" ? "Official SFSU source" : "Verified source"}
            aria-hidden="true"
          />
          <div>
            <a href={item.url} target="_blank" rel="noopener noreferrer">
              {item.title}
            </a>
            {item.provider && <span className="resource-provider"> · {item.provider}</span>}
            {item.description && !compact && (
              <p className="resource-description">{item.description}</p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
