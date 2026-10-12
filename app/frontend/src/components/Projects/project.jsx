import './project.css'

function Project({name, date, type}) {
    return (
        <div className="box project-contents">
            <h2>{name}</h2>
            <h3>{date}</h3>
            <h3>{type}</h3>
        </div>
    );
}

export default Project;