const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");

const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

// === ROOT ROUTE ===
app.get("/", (req, res) => {
  res.json({
    message: "AbbeSynapse Backend läuft!",
    endpoints: {
      "POST /get_mail": "Mail Agent",
      "POST /get_calendar": "Kalender Agent", 
      "POST /web_search": "WebSearch Agent"
    }
  });
});

// === MAIL AGENT ===
app.post("/get_mail", (req, res) => {
  const { message, time } = req.body;
  const path = require("path");
  const os = require("os");
  
  console.log("📧 Backend: Mail-Request erhalten:", { message, time });
  
  const pythonCmd = os.platform() === 'win32' ? 'py' : 'python3';
  const cmd = `${pythonCmd} "${path.join(__dirname, "mail_agent", "main.py")}" "${message}" "${time}"`;
  
  console.log("🐍 Ausgeführter Befehl:", cmd);

  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error("❌ Fehler beim Mail-Agent:", stderr || stdout);
      return res.status(500).json({ error: stderr || stdout });
    }

    try {
      const parsed = JSON.parse(stdout);
      console.log("✅ Erfolgreich geparst:", parsed);
      
      // Normalisiere die Antwort für das Frontend
      let response;
      
      if (parsed.success && parsed.response) {
        // Neue Format-Version mit response-Field
        response = {
          response: parsed.response,
          success: true,
          message: parsed.message || "Mail-Agent erfolgreich ausgeführt"
        };
      } else if (parsed.relevante_emails && parsed.relevante_emails.length > 0) {
        // Fallback: Alte Format-Version ohne response-Field
        const emailList = parsed.relevante_emails
          .map((email, index) => 
            `${index + 1}. **${email.betreff}**\n   Von: ${email.absender}\n   ID: ${email.id}`
          )
          .join('\n\n');
        
        response = {
          response: `**${parsed.relevante_emails.length} relevante E-Mails gefunden:**\n\n${emailList}`,
          success: true,
          message: `${parsed.relevante_emails.length} relevante E-Mails gefunden`
        };
      } else {
        // Keine E-Mails gefunden
        response = {
          response: "Keine relevanten E-Mails zu deiner Anfrage gefunden.",
          success: true,
          message: "Keine relevanten E-Mails gefunden"
        };
      }
      
      res.json(response);
    } catch (parseError) {
      console.error("❌ JSON-Parse-Fehler:", parseError);
      console.error("❌ Raw stdout:", stdout);
      res.status(500).json({ error: "Ungültiges JSON vom Python-Skript", raw: stdout });
    }
  });
});

// === KALENDER AGENT ===
app.post("/get_calendar", (req, res) => {
  const { message, time } = req.body;
  const path = require("path");
  const os = require("os");
  
  const pythonCmd = os.platform() === 'win32' ? 'py' : 'python3';
  // Pfad in Anführungszeichen setzen
  const cmd = `${pythonCmd} "${path.join(__dirname, "calendar_agent", "main.py")}" "${message}" "${time}"`;

  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error("❌ Fehler beim Kalender-Agent:", stderr || stdout);
      return res.status(500).json({ error: stderr || stdout });
    }

    try {
      const parsed = JSON.parse(stdout);
      res.json(parsed);
    } catch (parseError) {
      console.error("❌ Ungültige JSON-Antwort vom Kalender-Agent:", stdout);
      res.status(500).json({ error: "Ungültiges JSON vom Python-Skript", raw: stdout });
    }
  });
});

// === WEB SEARCH AGENT ===
app.post("/web_search", (req, res) => {
  const { message } = req.body;
  const path = require("path");
  const os = require("os");
  
  console.log("🔍 Backend: WebSearch-Request erhalten:", { message });
  
  const pythonCmd = os.platform() === 'win32' ? 'py' : 'python3';
  
  // Escaping für sicheren Python-Code
  const escapedMessage = message.replace(/'/g, "\\'").replace(/"/g, '\\"').replace(/\n/g, '\\n');
  const escapedPath = path.join(__dirname, "web_search").replace(/\\/g, "\\\\");
  
  const cmd = `${pythonCmd} -c "import sys; sys.path.append('${escapedPath}'); from web_search_agent import create_web_search_agent; import json; result = create_web_search_agent('${escapedMessage}'); print(json.dumps(result, ensure_ascii=False))"`;
  
  console.log("🐍 Ausgeführter Befehl:", cmd);

  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error("❌ Fehler beim WebSearch-Agent:", stderr || stdout);
      return res.status(500).json({ error: stderr || stdout });
    }

    console.log("📤 Python stdout:", stdout);
    if (stderr) console.log("📤 Python stderr:", stderr);

    try {
      const parsed = JSON.parse(stdout);
      console.log("✅ Erfolgreich geparst:", parsed);
      
      // Formatiere für Frontend
      if (parsed && parsed.ai_summary && !parsed.error) {
        const summary = parsed.ai_summary;
        const searchResults = parsed.search_results || [];
        
        // Erstelle Links-Liste
        const links = searchResults.slice(0, 5).map((result, index) => 
          `${index + 1}. **${result.title || 'Ohne Titel'}**\n   ${result.link || ''}\n   ${(result.snippet || '').substring(0, 100)}...`
        ).join('\n\n');
        
        const responseText = `**Zusammenfassung:**\n\n${summary}\n\n**Relevante Links:**\n\n${links}`;
        
        res.json({
          response: responseText,
          success: true,
          message: "WebSearch erfolgreich",
          ai_summary: summary,
          search_results: searchResults
        });
      } else {
        res.json({
          response: `Websuche fehlgeschlagen: ${parsed?.error || 'Unbekannter Fehler'}`,
          success: false,
          message: "WebSearch-Fehler",
          error: parsed?.error
        });
      }
    } catch (parseError) {
      console.error("❌ JSON-Parse-Fehler:", parseError);
      console.error("❌ Raw stdout:", stdout);
      res.status(500).json({ error: "Ungültiges JSON vom Python-Skript", raw: stdout });
    }
  });
});

// === SERVER START ===
app.listen(PORT, () => {
  console.log(`✅ Backend läuft auf http://localhost:${PORT}`);
});