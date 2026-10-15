
import { useState } from "react";
import "./AccountSetup.css";
import defaultPfp from "../assets/Team/generic-icon.png";

function AccountSetup({ darkMode }) {
    const [isEditing, setIsEditing] = useState(true);

    const [profilePic, setProfilePic] = useState(defaultPfp);

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [location, setLocation] = useState("");

    const [skills, setSkills] = useState([
        { id: 1, name: "JavaScript" },
        { id: 2, name: "React" },
    ]);

    const [degrees, setDegrees] = useState([]);
    const [certificates, setCertificates] = useState([]);
    const [jobPreferences, setJobPreferences] = useState([]);

    const [newSkill, setNewSkill] = useState("");

    function addEntry(setter, newEntry) {
        setter((currentEntries) => [
            ...currentEntries,
            {
                id: crypto.randomUUID(),
                ...newEntry,
            },
        ]);
    }

    function updateEntry(setter, id, field, value) {
        setter((currentEntries) =>
            currentEntries.map((entry) =>
                entry.id === id
                    ? { ...entry, [field]: value }
                    : entry
            )
        );
    }

    function removeEntry(setter, id) {
        setter((currentEntries) =>
            currentEntries.filter((entry) => entry.id !== id)
        );
    }

    function handleProfilePicChange(event) {
        const file = event.target.files[0];

        if (file && file.type.startsWith("image/")) {
            setProfilePic(URL.createObjectURL(file));
        }
    }

    return (
        <main>
            <form
                className="box account-setup-form"
                onSubmit={(event) => {
                    event.preventDefault();
                    console.log("Account form submitted!");
                }}
            >
                <div className="account-form-header">
                    <div className="account-header-fields">
                        <div className="account-form-field account-header-field">
                            <label className="header-label" htmlFor="user-name">
                                Name
                            </label>
                            {isEditing ? (
                                <input id="user-name" className="header-input" name="name" type="text" placeholder="Enter name" value={name} onChange={(event) => setName(event.target.value)} required />
                            ) : (
                                <p className="header-value">{name || "No name provided"}</p>
                            )}
                        </div>

                        <div className="account-form-field account-header-field">
                            <label className="header-label" htmlFor="user-email">
                                Email
                            </label>
                            {isEditing ? (
                                <input id="user-email" className="header-input" name="email" type="email" placeholder="e.g. username@mail.com" value={email} onChange={(event) => setEmail(event.target.value)} required />
                            ) : (
                                <p className="header-value">{email || "No email provided"}</p>
                            )}
                        </div>

                        <div className="account-form-field account-header-field">
                            <label className="header-label" htmlFor="user-location">
                                Location
                            </label>
                            {isEditing ? (
                                <input id="user-location" className="header-input" name="location" type="text" placeholder="e.g. San Francisco, CA" value={location} onChange={(event) => setLocation(event.target.value)} />
                            ) : (
                                <p className="header-value">{location || "No location provided"}</p>
                            )}
                        </div>
                    </div>


                    <div className="pfp-holder">
                        {isEditing ? (
                            <label className="pfp-upload-btn" title="Change profile picture">
                                <img src={profilePic} alt="Profile" className="profile-pic"/>
                                <input type="file" accept="image/*" onChange={handleProfilePicChange}/>
                            </label>
                        ) : (
                            <img src={profilePic} alt="Profile" className="profile-pic"/>
                        )}
                    </div>

                    <div className="header-btns">
                        {isEditing ? (
                            <>
                                <button type="button" className="header-btn" onClick={() => setIsEditing(false)}>
                                    Save Profile
                                </button>

                                <button type="button" className="header-btn" onClick={() => setIsEditing(false)}>
                                    Discard Changes
                                </button>
                            </>
                        ) : (
                            <>
                                <button type="button" className="header-btn" onClick={() => setIsEditing(true)}>
                                    Edit Profile
                                </button>

                                <button type="button" className="header-btn" onClick={() => { console.log("Share profile clicked!"); }}>
                                    Share Profile
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <div className="form-body">

                    <div className="user-details">

                        <section className="account-section">
                            <h2>Education & Degrees</h2>

                            {degrees.map((degree) => (
                                <div className="entry-card" key={degree.id}>
                                    <label>
                                        Degree
                                        {isEditing ? (
                                            <input type="text" value={degree.degree} placeholder="e.g. B.S. Computer Science" onChange={(event) => updateEntry(setDegrees, degree.id, "degree", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{degree.degree || "Degree not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Institution
                                        {isEditing ? (
                                            <input type="text" value={degree.institution} placeholder="e.g. Example University" onChange={(event) => updateEntry(setDegrees, degree.id, "institution", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{degree.institution || "Institution not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Graduation year
                                        {isEditing ? (
                                            <input type="number" value={degree.year} placeholder="e.g. 2026" onChange={(event) => updateEntry(setDegrees, degree.id, "year", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{degree.year || "Graduation year not provided"}</p>
                                        )}
                                    </label>

                                    {isEditing && (
                                        <button type="button" onClick={() => removeEntry(setDegrees, degree.id)}>
                                            Remove degree
                                        </button>
                                    )}
                                </div>
                            ))}

                            {!isEditing && degrees.length === 0 && (
                                <p className="entry-value">No degrees added yet.</p>
                            )}

                            {isEditing && (
                                <button type="button" onClick={() => addEntry(setDegrees, { degree: "", institution: "", year: "" })}>
                                    + Add degree
                                </button>
                            )}
                        </section>

                        <section className="account-section">
                            <h2>Certificates</h2>

                            {certificates.map((certificate) => (
                                <div className="entry-card" key={certificate.id}>
                                    <label>
                                        Certificate name
                                        {isEditing ? (
                                            <input type="text" value={certificate.name} placeholder="e.g. AWS Cloud Practitioner" onChange={(event) => updateEntry(setCertificates, certificate.id, "name", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{certificate.name || "Certificate name not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Issuing organization
                                        {isEditing ? (
                                            <input type="text" value={certificate.issuer} placeholder="e.g. Amazon Web Services" onChange={(event) => updateEntry(setCertificates, certificate.id, "issuer", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{certificate.issuer || "Issuing organization not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Year earned
                                        {isEditing ? (
                                            <input type="number" value={certificate.year} placeholder="e.g. 2025" onChange={(event) => updateEntry(setCertificates, certificate.id, "year", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{certificate.year || "Year not provided"}</p>
                                        )}
                                    </label>

                                    {isEditing && (
                                        <button type="button" onClick={() => removeEntry(setCertificates, certificate.id)}>
                                            Remove certificate
                                        </button>
                                    )}
                                </div>
                            ))}

                            {!isEditing && certificates.length === 0 && (
                                <p className="entry-value">No certificates added yet.</p>
                            )}

                            {isEditing && (
                                <button type="button" onClick={() => addEntry(setCertificates, { name: "", issuer: "", year: "" })}>
                                    + Add certificate
                                </button>
                            )}
                        </section>

                        <section className="account-section">
                            <h2>Skills</h2>

                            <div className="entry-card">
                                {skills.map((skill) => (
                                    <div className="skill-item" key={skill.id}>
                                        {isEditing ? (
                                            <>
                                                <input type="text" value={skill.name} aria-label="Skill name" onChange={(event) => updateEntry(setSkills, skill.id, "name", event.target.value)} />

                                                <button type="button" onClick={() => removeEntry(setSkills, skill.id)} aria-label={`Remove ${skill.name}`}>
                                                    Remove
                                                </button>
                                            </>
                                        ) : (
                                            <span>{skill.name}</span>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {isEditing && (
                                <div className="add-skill-form">
                                    <input type="text" value={newSkill} onChange={(event) => setNewSkill(event.target.value)} placeholder="Enter a skill" aria-label="New skill" />

                                    <button type="button" onClick={() => {
                                        const name = newSkill.trim();

                                        if (!name) return;

                                        addEntry(setSkills, { name });
                                        setNewSkill("");
                                    }}>
                                        Add skill
                                    </button>
                                </div>
                            )}

                            {!isEditing && skills.length === 0 && (
                                <p className="entry-value">No skills added yet.</p>
                            )}
                        </section>

                        <section className="account-section">
                            <h2>Job Preferences</h2>

                            {jobPreferences.map((job) => (
                                <div className="entry-card" key={job.id}>
                                    <label>
                                        Desired role
                                        {isEditing ? (
                                            <input type="text" value={job.role} placeholder="e.g. Frontend Developer" onChange={(event) => updateEntry(setJobPreferences, job.id, "role", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{job.role || "Role not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Preferred location
                                        {isEditing ? (
                                            <input type="text" value={job.location} placeholder="e.g. San Francisco or Remote" onChange={(event) => updateEntry(setJobPreferences, job.id, "location", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{job.location || "Location not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Employment type
                                        {isEditing ? (
                                            <select value={job.employmentType} onChange={(event) => updateEntry(setJobPreferences, job.id, "employmentType", event.target.value)}>
                                                <option value="">Select type</option>
                                                <option value="Full-time">Full-time</option>
                                                <option value="Part-time">Part-time</option>
                                                <option value="Internship">Internship</option>
                                                <option value="Contract">Contract</option>
                                                <option value="Temporary">Temporary</option>
                                            </select>
                                        ) : (
                                            <p className="entry-value">{job.employmentType || "Employment type not provided"}</p>
                                        )}
                                    </label>

                                    <label>
                                        Minimum desired annual salary ($)
                                        {isEditing ? (
                                            <input type="number" min="0" value={job.salary} placeholder="e.g. 70000" onChange={(event) => updateEntry(setJobPreferences, job.id, "salary", event.target.value)} />
                                        ) : (
                                            <p className="entry-value">{job.salary ? `$${Number(job.salary).toLocaleString()}` : "Salary not provided"}</p>
                                        )}
                                    </label>

                                    {isEditing && (
                                        <button type="button" onClick={() => removeEntry(setJobPreferences, job.id)}>
                                            Remove preference
                                        </button>
                                    )}
                                </div>
                            ))}

                            {!isEditing && jobPreferences.length === 0 && (
                                <p className="entry-value">No job preferences added yet.</p>
                            )}

                            {isEditing && (
                                <button type="button" onClick={() => addEntry(setJobPreferences, { role: "", location: "", employmentType: "", salary: "" })}>
                                    + Add job preference
                                </button>
                            )}
                        </section>

                    </div>

                    <div className="user-work">
                        {/* Portfolio projects / Management */}
                    </div>
                </div>
            </form>
        </main>
    );
}

export default AccountSetup;
