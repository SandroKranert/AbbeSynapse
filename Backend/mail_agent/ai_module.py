from dotenv import load_dotenv
import os
import openai
import json

# API-Key laden
load_dotenv()
client = openai.OpenAI()

def rank_emails_with_ai(message, email_list, top_n=10):
    prompt = f"""
Du bist ein E-Mail-Ranking-Assistent. Sortiere die folgenden E-Mails nach ihrer Relevanz zur Nutzeranfrage und gib die IDs der Top {top_n} zurück.

Nutzeranfrage: {message}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}

Gib das Ergebnis als JSON zurück, z.B.:
{{ "top_ids": ["id1", "id2", "id3"] }}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein E-Mail-Ranking-Assistent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        output = json.loads(response.choices[0].message.content)
        return output.get("top_ids", [])
    except Exception as e:
        print(f"OpenAI-Fehler (Ranking): {e}")
        return []

def process_emails(message, email_list, time):
    prompt = build_prompt(message, email_list, time)
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": (
                    "Du bist ein hilfreicher E-Mail-Filter-Assistent. "
                    "Wenn die Nutzeranfrage eine Antwort auf eine E-Mail verlangt, "
                    "gib ein JSON mit den Feldern 'reply_text', 'original_id', 'to' und 'subject' zurück. "
                    "Du kannst auch E-Mails archivieren, indem du im JSON-Ausgabeformat das Feld 'archive_id' mit der ID der zu archivierenden E-Mail setzt."
                )},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        output_text = response.choices[0].message.content
        return json.loads(output_text)
    except Exception as e:
        print(f"OpenAI-Fehler: {e}")
        return {"error": str(e)}

def build_prompt(message, email_list, time):
    return f"""
Du erhältst eine Nutzeranfrage (message), eine Liste von E-Mails und einen Zeitstempel. 
Deine Aufgabe ist es, die zur Anfrage passenden E-Mails aus der Liste auszuwählen und sie im JSON-Format zurückzugeben.

Wenn die Nutzeranfrage das Archivieren einer E-Mail verlangt, gib zusätzlich das Feld "archive_id" mit der ID der zu archivierenden E-Mail zurück.

Wenn die Nutzeranfrage eine Antwort auf eine E-Mail verlangt, gib ein JSON mit den Feldern "reply_text", "original_id", "to" und "subject" zurück. Beispiel:
{{
  "reply_text": "Hallo Julius, ...",
  "original_id": "xyz123",
  "to": "julius@example.com",
  "subject": "Re: Test, bitte antworten"
}}

Message:
{message}

Zeitstempel:
{time}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}

Gib das Ergebnis im JSON-Format zurück, z. B.:
{{
  "relevante_emails": [
    {{ "id": "xyz123", "betreff": "...", "absender": "..." }}
  ],
  "archive_id": "xyz123",
  "reply_text": "Hallo Julius, ...",
  "original_id": "xyz123",
  "to": "julius@example.com",
  "subject": "Re: Test, bitte antworten"
}}
"""