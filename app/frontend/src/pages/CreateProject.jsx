import "./CreateProject.css";
import ProjectGallery from "../components/Projects/ProjectGallery";
import DescriptionEditor from "../components/Projects/DescriptionEditor";
import ProjectLinks from "../components/Projects/ProjectLinks";

function CreateProject({ darkMode }) {
    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">Your New Project !!</h1>
            </div>

            <form className="box project-form"
                onSubmit={(event) => {
                    event.preventDefault();
                    console.log("Project form is valid!");
                }}
            >

                <div className="header-fields">

                    <div className="form-field header-field">
                        <label htmlFor="project-name">Project Name</label>
                        <input id="project-name" name="name" type="text" placeholder="Enter your project name" required/>
                    </div>

                    <div className="form-field header-field">
                        <label htmlFor="project-date">Project Date</label>
                        <input id="project-date" name="date" type="text" placeholder="e.g. Fall 2025" required/>
                    </div>

                    <div className="form-field header-field">
                        <label htmlFor="project-subject">Subject / Field</label>
                        <input id="project-subject" name="subject" type="text" placeholder="e.g. Interior Design, Architecture" required/>
                    </div>

                </div>

                <DescriptionEditor />

                <ProjectGallery />

                <ProjectLinks />

                <div className="project-form-actions">
                    <button type="submit" className="project-submit-button">
                        Preview Project
                    </button>
                </div>

            </form>
        </main>
    );
}

export default CreateProject;