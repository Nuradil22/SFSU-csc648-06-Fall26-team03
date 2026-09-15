const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, body) {
    const res = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => null);

    if (!res.ok) {
        throw new Error(data?.detail || 'Something went wrong. Please try again.');
    }

    return data;
}

export function signup({ name, email, password }) {
    return request('/auth/signup', { name, email, password });
}

export function login({ email, password }) {
    return request('/auth/login', { email, password });
}
