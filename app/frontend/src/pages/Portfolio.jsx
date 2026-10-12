import { useState } from "react";

import './portfolio.css';
import projects from '../data/projectsPlaceholder';
import Project from '../components/Projects/project';

function portfolio ({ darkMode }){
    return (
        <main>
            <div className ="banner"> 
                <h1 className="banner-title">Your Portfolio</h1>
            </div>

            <div className="portfolio-body">

                <div className="project-box">
                    {projects.map(proj => (
                    <Project
                    name={proj.name}
                    date={proj.date}
                    type={proj.type}
                    />
                ))}

                </div>
            </div>
        </main>
    );
}

export default portfolio;