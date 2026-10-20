// Converts a project from the API into the props the <Project> card expects.
export function toProjectProps(project) {
    const blocks = project.content_blocks?.length
        ? project.content_blocks
        : project.description
            ? [{ id: 'summary', type: 'paragraph', content: project.description }]
            : [];

    return {
        name: project.title,
        date: project.project_date,
        type: project.subject,
        description: blocks,
        images: project.images.map((image) => ({ src: image.url, alt: image.label })),
        links: project.links.map((link) => ({ label: link.label || link.url, url: link.url, type: link.link_type })),
        model: project.model_3d?.url ?? null,
    };
}
