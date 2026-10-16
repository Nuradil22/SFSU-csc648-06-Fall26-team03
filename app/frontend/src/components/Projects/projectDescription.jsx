import "./projectDescription.css";

function ProjectDescription({ blocks = [], darkMode }) {
    return (
        <div className="project-description">
            {blocks.map(block => {
                switch (block.type) {
                    case "heading":
                        return <h4 key={block.id}>{block.content}</h4>;

                    case "paragraph":
                        return <p key={block.id}>{block.content}</p>;
                    case "list":
                        return (
                            <ul key={block.id}>
                                {block.items.map((item, index) => (
                                    <li key={index}>{item}</li>
                                ))}
                            </ul>
                        );

                    default:
                        return null;
                }
            })}
        </div>
    );
}

export default ProjectDescription;