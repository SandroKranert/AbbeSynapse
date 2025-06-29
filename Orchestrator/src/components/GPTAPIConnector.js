// GPTAPIConnector.js
import { useState } from "react";
import OpenAI from "openai";

const apiKey = process.env.REACT_APP_OPENAI_API_KEY;

const useGPTAPIConnector = () => {
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // OpenAI-Client initialisieren
  const openai = new OpenAI({
    apiKey: apiKey,
    dangerouslyAllowBrowser: true,
  });

  const functions = [
    {
      name: "getCalendar",
      description: "Sucht Termine im Kalender basierend auf Freitext, z.B. 'Termine heute ab 14 Uhr'.",
      parameters: {
        type: "object",
        properties: {
          text: {
            type: "string",
            description: "Freitext zur Kalendersuche, z.B. 'Termine heute ab 14 Uhr' oder 'Treffen nächste Woche'.",
          },
        },
        required: ["text"],
      },
    },
    {
      name: "getMail",
      description: "Sucht E-Mails basierend auf Freitext, z.B. 'Zeige wichtige Mails von Markus'.",
      parameters: {
        type: "object",
        properties: {
          text: {
            type: "string",
            description: "Freitext zur Mail-Suche, z.B. 'Unbeantwortete Mails', 'Mails von Anna', 'Wichtige Mails'.",
          },
        },
        required: ["text"],
      },
    },
    {
      name: "webSearch",
      description: "Führt eine Websuche basierend auf Freitext aus, z.B. 'Wetter Berlin heute' oder 'React Hooks Tutorial'.",
      parameters: {
        type: "object",
        properties: {
          text: {
            type: "string",
            description: "Suchbegriff als Freitext, z.B. 'Wetter Berlin heute', 'Neueste Nachrichten KI'.",
          },
        },
        required: ["text"],
      },
    },
  ];

  const fetchAssistantResponse = async (chatHistory) => {
    setLoading(true);
    setError(null);

    try {
      // 1) System-Message + komplette History ins OpenAI-Format bringen
      const messagesForApi = [
        {
          role: "system",
          content: "Du bist ein hilfreicher Assistent. Wenn der Nutzer nach Kalender- oder Mail-Daten oder einer Websuche fragt, verwende eine Function-Call mit Freitext-Argument.",
        },
        ...chatHistory.map((msg) => ({
          role: msg.sender,
          content: msg.text,
        })),
      ];

      // 2) Starte Chat-Completion mit function_call="auto"
      const chatResponse = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        messages: messagesForApi,
        temperature: 0.7,
        functions: functions,
        function_call: "auto",
      });

      const message = chatResponse.choices?.[0]?.message;

      // 3) Prüfe, ob GPT eine Function-Call angefordert hat
      if (message?.function_call) {
        const { name, arguments: argsJson } = message.function_call;
        let parsedArgs = {};
        try {
          parsedArgs = JSON.parse(argsJson || "{}");
        } catch {
          parsedArgs = {};
        }

        // Freitext-Argument extrahieren
        const freeText = parsedArgs.text || "";

        // Je nach Funktion Backend aufrufen
        switch (name) {
          case "getCalendar":
            console.log("📅 Funktion 'getCalendar' aufgerufen mit Text:", freeText);
            try {
              const res = await fetch("http://localhost:8000/get_calendar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  message: freeText,
                  time: new Date().toISOString(),
                }),
              });
              const json = await res.json();
              return json.response || json.message || "Keine Kalenderantwort erhalten.";
            } catch (e) {
              console.error("❌ Fehler beim Kalender-Agent:", e);
              return "Fehler beim Abrufen der Kalenderdaten.";
            }

          case "getMail":
            console.log("📧 Funktion 'getMail' aufgerufen mit Text:", freeText);
            try {
              const res = await fetch("http://localhost:8000/get_mail", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  message: freeText,
                  time: new Date().toISOString(),
                }),
              });
              const json = await res.json();
              
              console.log("📧 Mail-Agent Response:", json);
              
              // Verwende das neue response-Format vom Backend
              if (json.response) {
                return json.response;
              } else if (json.relevante_emails && json.relevante_emails.length > 0) {
                // Fallback falls kein response-Field vorhanden
                const emailList = json.relevante_emails
                  .map((email, index) => 
                    `${index + 1}. **${email.betreff}**\n   Von: ${email.absender}\n   ID: ${email.id}`
                  )
                  .join('\n\n');
                
                return `**${json.relevante_emails.length} relevante E-Mails gefunden:**\n\n${emailList}`;
              } else {
                return "Keine relevanten E-Mails zu deiner Anfrage gefunden.";
              }
            } catch (e) {
              console.error("❌ Fehler beim Mail-Agent:", e);
              return "Fehler beim Abrufen der E-Mail-Daten.";
            }

          case "webSearch":
            console.log("🔍 Funktion 'webSearch' aufgerufen mit Text:", freeText);
            try {
              const res = await fetch("http://localhost:8000/web_search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: freeText }),
              });
              const json = await res.json();
              const summary = json.ai_summary || "Keine Zusammenfassung verfügbar.";
              const links = (json.search_results || [])
                .slice(0, 5)
                .map((r, i) => `${i + 1}. ${r.title} — ${r.link}`)
                .join("\n\n");

              return `🧠 ${summary}\n\n\n🔗 Relevante Links:\n\n${links}`;
            } catch (e) {
              console.error("❌ Fehler beim WebSearch-Agent:", e);
              return "Fehler bei der Websuche.";
            }

          default:
            return "Unbekannte Funktion angefordert.";
        }
      } else {
        // 4) Normale Chat-Antwort ohne Function-Call
        const assistantText = message?.content || "Keine Antwort erhalten.";
        setResponse(assistantText);
        return assistantText;
      }
    } catch (err) {
      console.error("❌ Fehler in fetchAssistantResponse:", err);
      setError(err.message);
      return "Entschuldigung, ein Fehler ist aufgetreten.";
    } finally {
      setLoading(false);
    }
  };

  return {
    response,
    loading,
    error,
    fetchAssistantResponse,
  };
};

export default useGPTAPIConnector;