import { useState } from "react";
import { useNavigate } from "react-router-dom"; 

import './Portfolio.css';
import Projects from '../data/projectsPlaceholder';
import Project from '../components/Projects/Project';

function Portfolio ({ darkMode }){
    const navigate = useNavigate();

    return (
        <main>
            <div className ="banner"> 
                <h1 className="banner-title">User's Portfolio</h1>
            </div>

            <div className="portfolio-body">

                {/* List all a Users projects in a portfolio */}
                <div className="project-box">
                    {Projects.map(proj => (
                    <Project
                    key={proj.id}
                    date={proj.date}
                    name={proj.name}
                    type={proj.type}
                    description={proj.description}
                    images={proj.images}
                    links={proj.links}
                    darkMode={darkMode}
                    />
                ))}
                </div>

                {/* Give the user an option to create a new project, routes to the new project page */}
                <button className="box project-card create-project-card project-box" onClick={() => navigate("/projects/new")}>
                    <h2>Create New Project !!</h2>
                </button>

            </div>
        </main>
    );
}

export default Portfolio;