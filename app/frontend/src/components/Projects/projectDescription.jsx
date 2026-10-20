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
                    case "list": {
                        // The DescriptionEditor saves bullets in `content` (with a `title`);
                        // older placeholder data used `items`.
                        const items = (block.items || block.content || []).filter((item) => item.trim());
                        return (
                            <div key={block.id}>
                                {block.title && <h4>{block.title}</h4>}
                                <ul>
                                    {items.map((item, index) => (
                                        <li key={index}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        );
                    }

                    default:
                        return null;
                }
            })}
        </div>
    );
}

export default ProjectDescription;