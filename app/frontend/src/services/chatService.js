const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function sendMessage(message) {
    const token = localStorage.getItem("token");

    const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Unable to send message.");
    }

    return data;
}