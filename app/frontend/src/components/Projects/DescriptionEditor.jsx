import "./DescriptionEditor.css";

// Controlled: the parent page owns `blocks` so it can save and pre-fill them.
function DescriptionEditor({ blocks, setBlocks }) {

    function addBlock(type) {
        const newBlock = {
            id: crypto.randomUUID(),
            type,
            title: type === "list" ? "Bullet List" : "",
            content: type === "list" ? [""] : ""
        };

        setBlocks((currentBlocks) => [...currentBlocks, newBlock]);
    }

    function updateBlock(id, value) {
        setBlocks((currentBlocks) =>
            currentBlocks.map((block) =>
                block.id === id
                    ? { ...block, content: value }
                    : block
            )
        );
    }


    function deleteBlock(id) {
        setBlocks((currentBlocks) =>
            currentBlocks.filter((block) => block.id !== id)
        );
    }

    function deleteBulletPoint(blockId, bulletIndex) {
        setBlocks((currentBlocks) =>
            currentBlocks.map((block) =>
                block.id === blockId ? {
                    ...block, content: block.content.filter(
                        (_, index) => index !== bulletIndex
                    )
                } : block
            )
        );
    }


    return (
        <section className="description-editor">
            <h2>Project Overview</h2>

            <div className="description-editor-blocks">

                {blocks.map((block) => (
                    <div key={block.id} className="description-editor-block">

                        <button type="button" className="delete-item-button" aria-label="Delete this section"
                            onClick={() => deleteBlock(block.id)}
                        >
                            Delete This Section
                        </button>

                        {block.type === "heading" && (

                            <input type="text" placeholder="Enter heading..." value={block.content}
                                onChange={(event) =>
                                    updateBlock(block.id, event.target.value)
                                }
                            />
                        )}

                        {block.type === "paragraph" && (
                            <textarea placeholder="Write your paragraph..." value={block.content}
                                onChange={(event) =>
                                    updateBlock(block.id, event.target.value)
                                }
                                rows={4}
                            />
                        )}

                        {block.type === "list" && (
                            <div>
                                <input
                                    type="text"
                                    placeholder="Enter list title..."
                                    value={block.title}
                                    onChange={(event) =>
                                        setBlocks((currentBlocks) =>
                                            currentBlocks.map((currentBlock) =>
                                                currentBlock.id === block.id
                                                    ? {
                                                        ...currentBlock,
                                                        title: event.target.value
                                                    }
                                                    : currentBlock
                                            )
                                        )
                                    }
                                />

                                {block.content.map((item, index) => (
                                    <div className="bullet-point-row" key={index}>

                                        <button type="button" className="delete-item-button"
                                            aria-label={`Delete bullet point ${index + 1}`}
                                            onClick={() =>
                                                deleteBulletPoint(block.id, index)
                                            }
                                        >
                                            Delete Bullet
                                        </button>

                                        <input
                                            type="text"
                                            placeholder={`Bullet point ${index + 1}`}
                                            value={item}
                                            onChange={(event) => {
                                                const updatedItems = [...block.content];
                                                updatedItems[index] = event.target.value;
                                                updateBlock(block.id, updatedItems);
                                            }}
                                        />


                                    </div>
                                ))}

                                <button
                                    type="button"
                                    onClick={() =>
                                        updateBlock(block.id, [
                                            ...block.content,
                                            ""
                                        ])
                                    }
                                >
                                    Add Bullet Point
                                </button>
                            </div>
                        )}

                    </div>
                ))}
            </div>

            <div className="description-editor-controls">
                <button type="button" onClick={() => addBlock("heading")}>
                    Add Heading
                </button>

                <button type="button" onClick={() => addBlock("paragraph")}>
                    Add Paragraph
                </button>

                <button type="button" onClick={() => addBlock("list")}>
                    Add Bullet List
                </button>
            </div>
        </section>
    );
}

export default DescriptionEditor;