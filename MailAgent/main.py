import json
from gmail_reader import list_gmail_messages
from ai_module import process_emails
from datetime import datetime

def run_mail_assistant(message: str, time: str):
    print("Lese alle Gmail-Nachrichten...")
    email_list = list_gmail_messages()
    print("Sende an KI-Modul...")
    output = process_emails(message, email_list)
    print("Fertig.")
    return output

# #Beispiel für den Funktionsaufruf:
# if __name__ == "__main__":
#     result = run_mail_assistant("Mails von heute", "2025-06-26T00:00:00+02:00")
#     with open("output.json", "w", encoding="utf-8") as f:
#         json.dump(result, f, indent=2, ensure_ascii=False)