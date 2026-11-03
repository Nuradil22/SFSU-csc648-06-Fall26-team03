import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function MessageList({ messages, isLoading, onDecide }) {
  const endRef = useRef(null);

  // Keep the newest message in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, isLoading]);

  return (
    <div className="chat-messages" aria-live="polite">
      {messages.map(message => (
        <MessageBubble key={message.id} message={message} onDecide={onDecide} />
      ))}

      {isLoading && (
        <div className="chat-bubble chat-bubble-assistant chat-thinking">
          Thinking…
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}
