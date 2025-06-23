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
            description:
              "Freitext zur Kalendersuche, z.B. 'Termine heute ab 14 Uhr' oder 'Treffen nächste Woche'.",
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
            description:
              "Freitext zur Mail-Suche, z.B. 'Unbeantwortete Mails', 'Mails von Anna', 'Wichtige Mails'.",
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
            description:
              "Suchbegriff als Freitext, z.B. 'Wetter Berlin heute', 'Neueste Nachrichten KI'.",
          },
        },
        required: ["text"],
      },
    },
  ];

  /**
   * @param {Array<{sender: "user"|"assistant", text: string}>} chatHistory
   * @returns {string|null} – Normaler Assistant-Text oder null, wenn GPT eine Funktion anfordert.
   */
  const fetchAssistantResponse = async (chatHistory) => {
    setLoading(true);
    setError(null);

    try {
      // 1) System-Message + komplette History ins OpenAI-Format bringen
      const messagesForApi = [
        {
          role: "system",
          content:
            "Du bist ein hilfreicher Assistent. Wenn der Nutzer nach Kalender- oder Mail-Daten oder einer Websuche fragt, verwende eine Function-Call mit Freitext-Argument.",
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
        function_call: "auto", // GPT entscheidet selbst, ob Function-Call nötig ist
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

        // Je nach Funktion nur console.log
        switch (name) {
          case "getCalendar":
            console.log("🗓️ Funktion 'getCalendar' aufgerufen mit Text:", {"message": freeText,
            "time": new Date().toISOString()});
            break;
          case "getMail":
            console.log("📧 Funktion 'getMail' aufgerufen mit Text:", freeText);
            break;
          case "webSearch":
            console.log("🔍 Funktion 'webSearch' aufgerufen mit Text:", freeText);
            break;
          default:
            console.log(`❓ Unbekannte Function-Call: ${name}`, parsedArgs);
        }

        // Wir geben null zurück, damit im Chat-Component keine normale Antwort angezeigt wird
        return null;
      }

      // 4) Kein Function-Call – normale GPT-Nachricht extrahieren
      const assistantReply = message?.content ?? "";
      setResponse(assistantReply);
      return assistantReply;
    } catch (err) {
      console.error("Fehler beim API-Call:", err);
      setError(err.message || "Unbekannter Fehler");
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { response, loading, error, fetchAssistantResponse };
};

export default useGPTAPIConnector;
