const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// --- Auth state (token + user are saved by the login/signup forms) ---

export function getToken() {
    return localStorage.getItem('token');
}

export function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('user'));
    } catch {
        return null;
    }
}

export function saveAuth(data) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
}

export function clearAuth() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

// --- Request helper ---

// FastAPI errors come back as {detail: "..."} or, for validation errors,
// {detail: [{loc, msg}, ...]}.
function errorMessage(data) {
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) {
        return data.detail
            .map((err) => `${err.loc?.slice(1).join('.') || 'field'}: ${err.msg.replace(/^Value error, /, '')}`)
            .join('; ');
    }
    return 'Something went wrong. Please try again.';
}

async function request(path, { method = 'GET', body, formData, auth = false } = {}) {
    const headers = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (auth) {
        const token = getToken();
        if (token) headers.Authorization = `Bearer ${token}`;
    }

    const res = await fetch(`${API_URL}${path}`, {
        method,
        headers,
        body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
    });

    if (res.status === 401 && auth) {
        clearAuth();
    }

    const data = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
        const error = new Error(errorMessage(data));
        error.status = res.status;
        throw error;
    }
    return data;
}

// --- Auth ---

export function signup({ name, email, password }) {
    return request('/auth/signup', { method: 'POST', body: { name, email, password } });
}

export function login({ email, password }) {
    return request('/auth/login', { method: 'POST', body: { email, password } });
}

export async function logout() {
    try {
        await request('/auth/logout', { method: 'POST', auth: true });
    } finally {
        clearAuth();
    }
}

// --- Portfolio ---

export function getMyPortfolio() {
    return request('/portfolio/me', { auth: true });
}

export function updateMyPortfolio(fields) {
    return request('/portfolio/me', { method: 'PATCH', body: fields, auth: true });
}

export function enableSharing() {
    return request('/portfolio/me/share', { method: 'POST', auth: true });
}

export function getSharedPortfolio(shareToken) {
    return request(`/public/portfolios/${encodeURIComponent(shareToken)}`);
}

// Education, skills, and experience share the same add/update/delete shape.
function sectionApi(section) {
    return {
        add: (fields) => request(`/portfolio/me/${section}`, { method: 'POST', body: fields, auth: true }),
        update: (id, fields) => request(`/portfolio/me/${section}/${id}`, { method: 'PATCH', body: fields, auth: true }),
        remove: (id) => request(`/portfolio/me/${section}/${id}`, { method: 'DELETE', auth: true }),
    };
}

export const education = sectionApi('education');
export const skills = sectionApi('skills');
export const experience = sectionApi('experience');

// --- Projects ---

export function searchProjects({ search = '', category = '', limit = 20, offset = 0 } = {}) {
    const params = new URLSearchParams({ limit, offset });
    if (search.trim()) params.set('search', search.trim());
    if (category.trim()) params.set('category', category.trim());
    return request(`/projects?${params}`);
}

export function getMyProjects() {
    return request('/projects/mine', { auth: true });
}

export function getProject(id) {
    return request(`/projects/${id}`, { auth: true });
}

export function createProject(fields) {
    return request('/projects', { method: 'POST', body: fields, auth: true });
}

export function updateProject(id, fields) {
    return request(`/projects/${id}`, { method: 'PATCH', body: fields, auth: true });
}

export function deleteProject(id) {
    return request(`/projects/${id}`, { method: 'DELETE', auth: true });
}

export function uploadProjectImage(projectId, file, label) {
    const formData = new FormData();
    formData.append('file', file);
    if (label) formData.append('label', label);
    return request(`/projects/${projectId}/images`, { method: 'POST', formData, auth: true });
}

export function addProjectLink(projectId, { label, url, link_type }) {
    return request(`/projects/${projectId}/links`, {
        method: 'POST',
        body: { label, url, link_type: link_type || null },
        auth: true,
    });
}

export function removeProjectMedia(projectId, mediaId) {
    return request(`/projects/${projectId}/media/${mediaId}`, { method: 'DELETE', auth: true });
}
