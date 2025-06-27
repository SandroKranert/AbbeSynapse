from dotenv import load_dotenv
import os
import openai
import json

from pydantic import BaseModel
from typing import List, Optional

# Modelle für die E-Mail-Datenstruktur
class RelevanteEmail(BaseModel):
    id: str
    betreff: str
    absender: str

class MailAgentResponse(BaseModel):
    relevante_emails: Optional[List[RelevanteEmail]]
    archive_id: Optional[str]
    reply_text: Optional[str]
    original_id: Optional[str]
    to: Optional[str]
    subject: Optional[str]

# API-Key laden
load_dotenv()
client = openai.OpenAI()

def rank_emails_with_ai(message, email_list, top_n=10):
    prompt = f"""
Du bist ein E-Mail-Ranking-Assistent. Sortiere die folgenden E-Mails nach ihrer Relevanz zur Nutzeranfrage und gib die IDs der Top {top_n} im JSON-Format zurück.

Nutzeranfrage: {message}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}
"""
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "Du bist ein E-Mail-Ranking-Assistent. Antworte immer im JSON-Format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        output = json.loads(completion.choices[0].message.content)
        return output.get("top_ids", [])
    except Exception as e:
        print(f"OpenAI-Fehler (Ranking): {e}")
        return []

def process_emails(message, email_list, time):
    prompt = build_prompt(message, email_list, time)
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "Du bist ein hilfreicher E-Mail-Filter-Assistent. "
                    "Extrahiere alle relevanten Informationen zur Nutzeranfrage im vorgegebenen Format."
                )},
                {"role": "user", "content": prompt}
            ],
            response_format=MailAgentResponse,
        )
        return completion.choices[0].message.parsed.model_dump()
    except Exception as e:
        print(f"OpenAI-Fehler: {e}")
        return {"error": str(e)}

def build_prompt(message, email_list, time):
    return f"""
Du erhältst eine Nutzeranfrage (message), eine Liste von E-Mails und einen Zeitstempel.
Extrahiere alle relevanten Informationen für die Anfrage.

Message: {message}
Zeitstempel: {time}
E-Mails: {json.dumps(email_list, ensure_ascii=False, indent=2)}
"""