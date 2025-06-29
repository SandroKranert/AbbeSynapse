import sys
import json
from gmail_reader import list_gmail_messages, send_reply, archive_email
from ai_module import process_emails, rank_emails_with_ai
from datetime import datetime

def moderate_emails(email_list):
    beleidigungen = [
        "idiot", "dumm", "blöd", "arsch", "trottel", "depp", "schwachkopf", "spast", "fresse", "scheiße"
    ]
    moderated = []
    for mail in email_list:
        betreff = mail.get("betreff", "").lower()
        inhalt = mail.get("inhalt", "").lower()
        if "spam" in betreff or "spam" in inhalt:
            continue
        if any(wort in betreff for wort in beleidigungen) or any(wort in inhalt for wort in beleidigungen):
            continue
        moderated.append(mail)
    return moderated

def format_for_frontend(output):
    """Formatiert die Mail-Agent-Antwort für das Frontend"""
    relevante_emails = output.get("relevante_emails", [])
    
    if relevante_emails and len(relevante_emails) > 0:
        # Erstelle Frontend-freundliche Antwort
        email_list = []
        for i, email in enumerate(relevante_emails):
            email_list.append(f"{i + 1}. **{email.get('betreff', 'Kein Betreff')}**")
            email_list.append(f"   Von: {email.get('absender', 'Unbekannt')}")
            email_list.append(f"   ID: {email.get('id', '')}")
            email_list.append("")  # Leerzeile
        
        response_text = f"**{len(relevante_emails)} relevante E-Mails gefunden:**\n\n" + "\n".join(email_list)
        
        return {
            **output,
            "response": response_text,
            "success": True,
            "message": f"{len(relevante_emails)} relevante E-Mails gefunden"
        }
    else:
        return {
            **output,
            "response": "Keine relevanten E-Mails zu deiner Anfrage gefunden.",
            "success": True,
            "message": "Keine relevanten E-Mails gefunden"
        }

def run_mail_assistant(message: str, time: str):
    email_list = list_gmail_messages()
    email_list = moderate_emails(email_list)
    
    # 1. KI-Ranking
    top_ids = rank_emails_with_ai(message, email_list, top_n=10)
    top_emails = [mail for mail in email_list if mail["id"] in top_ids]
    
    # 2. KI-Processing
    output = process_emails(message, top_emails, time)
    
    # 3. Frontend-Formatierung
    formatted_output = format_for_frontend(output)
    
    # Automatisches Versenden, wenn Antwortdaten vorhanden sind
    if output.get("reply_text") and output.get("original_id") and output.get("to") and output.get("subject"):
        send_reply(
            message_id=output["original_id"],
            to=output["to"],
            subject=output["subject"],
            body=output["reply_text"]
        )
    
    # Automatisches Archivieren, wenn archive_id vorhanden ist
    if output.get("archive_id"):
        archive_email(output["archive_id"])
    
    return formatted_output

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Ungültige Anzahl von Argumenten"}))
        sys.exit(1)
    
    msg = sys.argv[1]
    time = sys.argv[2]
    
    try:
        result = run_mail_assistant(msg, time)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e), "success": False}))