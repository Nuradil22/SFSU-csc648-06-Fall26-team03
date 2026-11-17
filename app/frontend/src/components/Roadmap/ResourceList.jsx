import "./ResourceList.css";

// Verified learning resources exactly as the backend returns them:
// {title, url, provider?, type?, description?, code?, kind?, topics?,
//  credential?, credential_detail?, outcome?}. `title` is the offering's
// official name, confirmed by the backend on the provider's own page; a
// credential the page doesn't state arrives as "unverified". The backend only
// keeps https links that came back from that request's web search; this
// re-checks the scheme before rendering a link. type "sfsu" marks official
// SFSU pages. Topics and credential come from the provider's page; "why it
// fits" and the expected outcome are Projectory's own estimates and are
// labelled as such. Older resources (before these details existed) show title,
// provider, and description only.

const KIND_LABELS = {
  course: "Course",
  certificate: "Certificate program",
  specialization: "Specialization",
  professional_certification: "Professional certification",
  degree_program: "Degree program",
  other_program: "Program",
};

const CREDENTIAL_LABELS = {
  academic_credit: "Course credit",
  certificate: "Certificate",
  professional_certification: "Professional certification",
  degree: "Degree",
  badge: "Digital badge",
  none_stated: "None stated by the provider",
  unverified: "Not confirmed on the provider's page",
};

function credentialText(item) {
  const label = CREDENTIAL_LABELS[item.credential];
  if (!label) return "";
  return item.credential_detail ? `${label} (${item.credential_detail})` : label;
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function Details({ item }) {
  const credential = credentialText(item);
  const topics = Array.isArray(item.topics) ? item.topics : [];

  return (
    <dl className="resource-details">
      {topics.length > 0 && (
        <>
          <dt>Covers (provider page)</dt>
          <dd>{topics.join(", ")}</dd>
        </>
      )}
      {credential && (
        <>
          <dt>Credential</dt>
          <dd>{credential}</dd>
        </>
      )}
      {item.description && (
        <>
          <dt>Why it fits</dt>
          <dd>{item.description}</dd>
        </>
      )}
      {item.outcome && (
        <>
          <dt>Expected outcome (estimate)</dt>
          <dd>{item.outcome}</dd>
        </>
      )}
      <dt>Official page</dt>
      <dd>
        <a href={item.url} target="_blank" rel="noopener noreferrer">
          {hostOf(item.url)}
        </a>
      </dd>
    </dl>
  );
}

export default function ResourceList({ resources, compact = false }) {
  const items = (resources || []).filter(
    (item) => item?.title && typeof item.url === "string" && item.url.startsWith("https://")
  );

  if (!items.length) return null;

  return (
    <ul className={`resource-list${compact ? " is-compact" : ""}`}>
      {items.map((item) => {
        // Resources from before official-name details only have a description.
        const detailed = Boolean(item.kind || item.code || item.credential || item.outcome || item.topics);
        const kind = KIND_LABELS[item.kind];

        return (
          // Several courses can share one page (an SFSU Bulletin subject listing).
          <li key={`${item.url}|${item.code || ""}|${item.title}`} className="resource-item">
            <span
              className={`resource-dot ${item.type === "sfsu" ? "is-official" : "is-verified"}`}
              title={item.type === "sfsu" ? "Official SFSU source" : "Verified source"}
              aria-hidden="true"
            />
            <div>
              <a href={item.url} target="_blank" rel="noopener noreferrer">
                {item.code && <span className="resource-code">{item.code} </span>}
                {item.title}
              </a>
              {item.provider && <span className="resource-provider"> · {item.provider}</span>}
              {kind && <span className="resource-kind">{kind}</span>}

              {!detailed && item.description && !compact && (
                <p className="resource-description">{item.description}</p>
              )}
              {detailed && !compact && <Details item={item} />}
              {detailed && compact && (
                <details className="resource-more">
                  <summary>Details</summary>
                  <Details item={item} />
                </details>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
