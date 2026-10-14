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
        "Hi! I'm your career guide. What would you like to explore?"
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

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const assistantMessage = await sendMessage(content);

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error(error);
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