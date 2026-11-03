import { useState } from "react";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";
import { sendMessage } from "../../services/chatService";

export default function ChatWindow() {
    const [messages, setMessages] = useState([
        {
            id: "welcome",
            role: "assistant",
            content:
                "Hi! I'm your career guide. Ask me about career paths, university courses, certifications, or ways to improve your portfolio."
        }
    ]);

    const [isLoading, setIsLoading] = useState(false);

    async function handleSend(content) {
        if (!content.trim() || isLoading) return;

        const userMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content
        };

        setMessages((previous) => [...previous, userMessage]);
        setIsLoading(true);

        try {
            const response = await sendMessage(content);

            const assistantMessage = typeof response === "string"
                ? { content: response }
                : response;

            setMessages((previous) => [
                ...previous,
                {
                    id: assistantMessage.id || crypto.randomUUID(),
                    role: "assistant",
                    content: assistantMessage.content || "I couldn't generate a response."
                }
            ]);
        } catch (error) {
            console.error("Career assistant error:", error);

            setMessages((previous) => [
                ...previous,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content:
                        "The career assistant isn't connected yet. Your message was added, but I can't generate a response right now."
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="chat-window">
            <MessageList
                messages={messages}
                isLoading={isLoading}
            />

            <ChatInput
                onSend={handleSend}
                disabled={isLoading}
            />
        </div>
    );
}
