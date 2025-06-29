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

class EmailRankingResponse(BaseModel):
    top_email_ids: List[str]

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
    if not email_list:
        return []
    
    prompt = f"""Analysiere die folgenden E-Mails und bestimme ihre Relevanz zur Nutzeranfrage.

Nutzeranfrage: {message}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}

Sortiere nach Relevanz und gib die Top {top_n} E-Mail-IDs zurück."""
    
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": "Du bist ein E-Mail-Ranking-Assistent. Bestimme die Relevanz von E-Mails zu Nutzeranfragen."},
                {"role": "user", "content": prompt}
            ],
            response_format=EmailRankingResponse,
        )
        
        result = response.choices[0].message.parsed
        return result.top_email_ids
            
    except Exception as e:
        return []

def process_emails(message, email_list, time):
    """Verarbeitet E-Mails und entscheidet über Aktionen"""
    if not email_list:
        return {
            "relevante_emails": [],
            "archive_id": None,
            "reply_text": None,
            "original_id": None,
            "to": None,
            "subject": None
        }
    
    try:
        prompt = build_prompt(message, email_list, time)
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": (
                    "Du bist ein hilfreicher E-Mail-Filter-Assistent. "
                    "Extrahiere alle relevanten Informationen zur Nutzeranfrage."
                )},
                {"role": "user", "content": prompt}
            ],
            response_format=MailAgentResponse,
        )
        
        result = completion.choices[0].message.parsed.model_dump()
        return result
        
    except Exception as e:
        # Fallback: Erstelle manuelle Antwort
        relevante_emails = []
        for email in email_list:
            relevante_emails.append({
                "id": email.get("id", ""),
                "betreff": email.get("betreff", ""),
                "absender": email.get("absender", "")
            })
        
        return {
            "relevante_emails": relevante_emails,
            "archive_id": None,
            "reply_text": None,
            "original_id": None,
            "to": None,
            "subject": None
        }

def build_prompt(message, email_list, time):
    """Erstellt den Prompt für die E-Mail-Verarbeitung"""
    return f"""Du bist ein E-Mail-Assistent. Analysiere die gegebenen E-Mails basierend auf der Nutzeranfrage.

Nutzeranfrage: {message}
Zeitstempel: {time}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}

Aufgaben:
1. Identifiziere alle E-Mails, die zur Anfrage relevant sind
2. Erkenne, ob der Nutzer eine E-Mail archivieren möchte
3. Erkenne, ob der Nutzer auf eine E-Mail antworten möchte
4. Falls eine Antwort gewünscht ist, formuliere eine passende Antwort

Berücksichtige den Kontext der Anfrage und handle entsprechend."""