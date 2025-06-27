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

def run_mail_assistant(message: str, time: str):
    email_list = list_gmail_messages()
    email_list = moderate_emails(email_list)
    # 1. KI-Ranking
    top_ids = rank_emails_with_ai(message, email_list, top_n=10)
    top_emails = [mail for mail in email_list if mail["id"] in top_ids]
    # 2. KI-Processing
    output = process_emails(message, top_emails, time)
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
    return output

# if __name__ == "__main__":
#     msg = sys.argv[1]
#     time = sys.argv[2]
#     result = run_mail_assistant(msg, time)
#     print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    # Beispiel-Testanfrage direkt im Code
    test_message = "archiviere die mail von Julius"
    test_time = "2025-06-27T00:00:00+02:00"
    result = run_mail_assistant(test_message, test_time)
    print(json.dumps(result, ensure_ascii=False, indent=2))