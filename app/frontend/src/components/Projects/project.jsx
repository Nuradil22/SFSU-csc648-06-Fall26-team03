import { useState } from "react";
import './project.css';
import ProjectDescription from "./projectDescription";
import ModelViewer from "../ModelViewer/ModelViewer";

function Project({name, date, type, description, images = [], links = [], model, owner, darkMode, children}) {

    // this will be used to track if each project box is collapsed or expanded
    const [expanded, setExpanded] = useState(false);

    return (

        <article className={`box project-box project-card ${expanded ? "expanded" : ""}`}>
            <button className="project-header" onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
                <div className="project-metadata">  
                    <h3>{date}</h3>
                    <h2>{name}</h2>
                    <h3>{type}</h3>
                    {owner && <p className="project-owner">by {owner}</p>}
                </div>
                <span>{expanded ? "-" : "+"}</span>
            </button>

            {expanded && (
                <div className="project-details">

                    <section className="project-overview">
                        <h3>Project Overview</h3>
                        <ProjectDescription blocks={description} darkmode={darkMode}/>
                    </section>

                    {images.length > 0 && (
                    <section className="project-gallery">
                        <h3>Project Gallery</h3>

                        {/* This will allow all horizontally displayed images to be scrolled through (they will overflow width) */}
                        <div className="project-gallery-track">
                            {images.map((image, index) => (
                                // gracefully handle not being able to find an image
                                <a  key ={image.src || index} href={image.src} target="_blank" rel="noopener noreferrer" className="project-gallery-image-link">
                                    <img src={image.src} alt={image.alt || "project image"} className="project-gallery-image"/>
                                </a>
                            ))}
                        </div>
                    </section>
                    )}

                    {/* Optional interactive 3D model, shown only when the project has one */}
                    {model && (
                    <section className="project-model">
                        <h3>3D Model</h3>
                        <ModelViewer modelUrl={model} />
                    </section>
                    )}

                    {/* List all external links associated with a project */}
                    {links.length > 0 && (
                    <section>
                        <h3>Project Links</h3>
                        {links.map((link, index) => (
                            <p key={link.url || index}><a href={link.url} target="_blank" rel="noopener noreferrer" className="project-link">{link.label}</a></p>
                        ))}
                    </section>
                    )}

                    {children && <div className="project-actions">{children}</div>}

                </div>
            )}
        </article>

    );
}

export default Project;