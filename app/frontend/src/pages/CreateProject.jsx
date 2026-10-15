import "./CreateProject.css";
import "../components/Projects/DescriptionEditor";
import DescriptionEditor from "../components/Projects/DescriptionEditor";

function CreateProject({ darkMode }) {
    return (
        <main>
            <div className="banner">
                <h1 className="banner-title">Your New Project !!</h1>
            </div>

            <div className="box project-form">

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

            </div>
        </main>
    );
}

export default CreateProject;