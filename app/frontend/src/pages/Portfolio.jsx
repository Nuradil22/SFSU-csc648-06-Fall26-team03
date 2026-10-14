import { useState } from "react";

import './portfolio.css';
import projects from '../data/projectsPlaceholder';
import Project from '../components/Projects/project';

function Portfolio ({ darkMode }){

    return (
        <main>
            <div className ="banner"> 
                <h1 className="banner-title">User's Portfolio</h1>
            </div>

            <div className="portfolio-body">

                <div className="project-box">
                    {projects.map(proj => (
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
            </div>
        </main>
    );
}

export default Portfolio;