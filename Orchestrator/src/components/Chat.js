// Chat.js
import React, { useRef, useState, useEffect } from "react";
import "../styles/chat.css";
import botImage from "../img/bot.png";
import userImage from "../img/user.png";
import GPTAPIConnector from "./GPTAPIConnector"; // Dein angepasster Hook

const Chat = () => {
  const { loading, error, fetchAssistantResponse } = GPTAPIConnector();
  const [messages, setMessages] = useState([
    // Initiale Begrüßung vom Assistenten
    { type: "gpt", content: "Hallo! Ich bin dein Chat-Assistent. Wie kann ich dir helfen?" },
  ]);
  const messageRef = useRef(null);
  const chatRef = useRef(null);

  // Scroll automatisch ans Ende, wenn neue Nachrichten hinzukommen
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const messageSend = async () => {
    const rawText = messageRef.current.value;
    const trimmed = rawText.trim();
    if (trimmed === "") return;

    // 1) Erstelle das User-Message-Objekt und hänge es temporär ans Ende
    const userMessage = { type: "user", content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    messageRef.current.value = "";

    // 2) Erstelle die Chat-History für API-Call (nur text-basiert)
    const chatHistory = [
      
      ...messages.map((msg) => ({
        sender: msg.type === "user" ? "user" : "assistant",
        text: msg.content,
      })),
      
      { sender: "user", text: trimmed },
    ];

    try {
      
      const assistantReply = await fetchAssistantResponse(chatHistory);

      
      if (assistantReply) {
        setMessages((prev) => [
          ...prev,
          { type: "gpt", content: assistantReply },
        ]);
      } else {
        
        setMessages((prev) => [
          ...prev,
          { type: "gpt", content: "Entschuldigung, da ist etwas schiefgelaufen." },
        ]);
      }
    } catch (err) {
      // Bei Exception ebenfalls Fehler-Nachricht anhängen
      setMessages((prev) => [
        ...prev,
        { type: "gpt", content: "Fehler beim Abrufen der Antwort." },
      ]);
    }
  };

  return (
    <div className="card mt-3 card-content chat">
      <div className="card text-center">
        <div className="card-header">AbbeSynapse</div>
        <div className="card-body">
          <div className="container d-flex justify-content-center chat-container">
            <div ref={chatRef} className="card chat-contant mt-5">
              {messages.map((msg, index) => (
                <div key={index} className={`d-flex flex-row p-3 message-${msg.type}`}>
                  {/* GPT-Antworten */}
                  {msg.type === "gpt" && (
                    <>
                      <img src={botImage} alt="GPT" className="imgs-chat" />
                      <div className="bg-white mr-2 p-3 chat-bubble">
                        <span className="text-muted">{msg.content}</span>
                      </div>
                    </>
                  )}
                  {/* User-Nachrichten */}
                  {msg.type === "user" && (
                    <>
                      <div className="bg-white mr-2 p-3 chat-bubble-user">
                        <span className="text-muted">{msg.content}</span>
                      </div>
                      <img src={userImage} alt="User" className="imgs-chat" />
                    </>
                  )}
                </div>
              ))}

              {/* Lade-Indikator */}
              {loading && (
                <div className="d-flex flex-row p-3 message-gpt">
                  <img src={botImage} alt="GPT" className="imgs-chat" />
                  <div className="bg-white mr-2 p-3 chat-bubble">
                    <span className="text-muted">Loading...</span>
                  </div>
                </div>
              )}
              {/* Fehlermeldung */}
              {error && (
                <div className="d-flex flex-row p-3 message-gpt">
                  <img src={botImage} alt="GPT" className="imgs-chat" />
                  <div className="bg-white mr-2 p-3 chat-bubble">
                    <span className="text-muted">Error: {error}</span>
                  </div>
                </div>
              )}

              <div ref={chatRef} />
            </div>
            <div className="form-group px-3 d-flex flex-column justify-content-end">
              <textarea
                ref={messageRef}
                className="form-control"
                rows="3"
                placeholder="Schreibe deine Nachricht"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    messageSend();
                  }
                }}
              />
              <button className="btn btn-success mt-2" onClick={messageSend} disabled={loading}>
                Senden
              </button>
            </div>
          </div>
        </div>
        <div className="card-footer text-muted">
          Bei was kann ich dir heute helfen. :)
        </div>
      </div>
    </div>
  );
};

export default Chat;
