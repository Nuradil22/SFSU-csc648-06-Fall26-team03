
import { useState } from "react";
import "./Certificates.css";

const certificates = [
    {
        id: 1,
        name: "Artificial Intelligence (AI) for Business Technologies",
        type: "Undergraduate",
        department: "Information Systems",
        description: "",
        sourceUrl: "https://bulletin.sfsu.edu/about-sfsu/degrees-offered/certificates/",
    },
    {
        id: 2,
        name: "Accounting",
        type: "Graduate",
        department: "Lam Family College of Business",
        description: "",
        sourceUrl: "https://bulletin.sfsu.edu/about-sfsu/degrees-offered/certificates/",
    },
    {
        id: 3,
        name: "Pre-Health Professions",
        type: "Post-Baccalaureate",
        department: "College of Science and Engineering",
        description: "",
        sourceUrl: "https://bulletin.sfsu.edu/about-sfsu/degrees-offered/certificates/",
    },
];

function Certificates({ darkMode }) {
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedType, setSelectedType] = useState("All");

    const filteredCertificates = certificates.filter((certificate) => {
        const searchText = [
            certificate.name,
            certificate.type,
            certificate.department,
            certificate.description,
        ]
            .join(" ")
            .toLowerCase();

        const matchesSearch = searchText.includes(searchTerm.toLowerCase());
        const matchesType =
            selectedType === "All" || certificate.type === selectedType;

        return matchesSearch && matchesType;
    });

    return (
        <main className={`certificates-page ${darkMode ? "dark" : ""}`}>
            <div className="banner certificates-header">
                <h1>Certificate Programs</h1>
                <p>
                    Explore certificate programs offered by San Francisco
                    State University.
                </p>
            </div>

            <section className="certificates-controls">
                <input
                    type="search"
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search certificates or departments..."
                    aria-label="Search certificate programs"
                />

                <select
                    value={selectedType}
                    onChange={(event) => setSelectedType(event.target.value)}
                    aria-label="Filter by certificate type"
                >
                    <option value="All">All certificate types</option>
                    <option value="Undergraduate">Undergraduate</option>
                    <option value="Post-Baccalaureate">
                        Post-Baccalaureate
                    </option>
                    <option value="Graduate">Graduate</option>
                </select>
            </section>

            <p className="certificates-count">
                {filteredCertificates.length} certificate
                {filteredCertificates.length !== 1 ? "s" : ""} found
            </p>

            <section className="certificates-list">
                {filteredCertificates.length > 0 ? (
                    filteredCertificates.map((certificate) => (
                        <article
                            className="certificate-card"
                            key={certificate.id}
                        >
                            <span className="certificate-type">
                                {certificate.type}
                            </span>

                            <h2>{certificate.name}</h2>

                            <p className="certificate-department">
                                {certificate.department}
                            </p>

                            {certificate.description && (
                                <p>{certificate.description}</p>
                            )}

                            <a
                                href={certificate.sourceUrl}
                                target="_blank"
                                rel="noreferrer"
                            >
                                View official information
                            </a>
                        </article>
                    ))
                ) : (
                    <p className="certificates-empty">
                        No certificates match your search.
                    </p>
                )}
            </section>
        </main>
    );
}

export default Certificates;