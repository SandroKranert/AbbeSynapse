const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");

const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

// === MAIL AGENT ===
app.post("/get_mail", (req, res) => {
  const { message, time } = req.body;
  const path = require("path");
const cmd = `python3 ${path.join(__dirname, "mail_agent", "main.py")} "${message}" "${time}"`;



  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error("❌ Fehler beim Mail-Agent:", stderr || stdout);
      return res.status(500).json({ error: stderr || stdout });
    }

    try {
      const parsed = JSON.parse(stdout);
      res.json(parsed);
    } catch (parseError) {
      console.error("❌ Ungültige JSON-Antwort vom Mail-Agent:", stdout);
      res.status(500).json({ error: "Ungültiges JSON vom Python-Skript", raw: stdout });
    }
  });
});

// === KALENDER AGENT (optional) ===
app.post("/get_calendar", (req, res) => {
  const { message, time } = req.body;
  const cmd = `python3 calendar_agent/main.py "${message}" "${time}"`;

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
// === WEBSEARCH AGENT ===
app.post("/web_search", (req, res) => {
  const { message } = req.body;
  const path = require("path");
  const cmd = `python3 ${path.join(__dirname, "web_search", "web_search_agent.py")} "${message}"`;

  exec(cmd, (err, stdout, stderr) => {
    if (err) {
      console.error("❌ Fehler beim WebSearch-Agent:", stderr || stdout);
      return res.status(500).json({ error: stderr || stdout });
    }

    try {
      const parsed = JSON.parse(stdout);
      res.json(parsed);
    } catch (parseError) {
      console.error("❌ Ungültige JSON-Antwort vom WebSearch-Agent:", stdout);
      res.status(500).json({
        error: "Ungültiges JSON vom Python-Skript",
        raw: stdout,
      });
    }
  });
});


// === SERVER START ===
app.listen(PORT, () => {
  console.log(`✅ Backend läuft auf http://localhost:${PORT}`);
});
