import os
import email
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Für Senden und Lesen
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Ermittle den aktuelle Pfad dieser Datei
BASE_DIR = os.path.dirname(__file__)
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def authenticate_gmail():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8085, access_type='offline', prompt='consent')
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def parse_email(msg):
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    data = {
        "id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
        "labelIds": msg.get("labelIds", []),
        "uhrzeit": "00:00",
        "datum": "",
        "betreff": "",
        "absender": "",
        "empfaenger": "",
        "cc": "",
        "bcc": "",
        "anhang_vorhanden": False,
        "inhalt": msg.get("snippet", "")
    }

    for h in headers:
        name = h.get("name", "")
        value = h.get("value", "")
        if name == "Date":
            dt = email.utils.parsedate_to_datetime(value)
            data["uhrzeit"] = dt.strftime("%H:%M")
            data["datum"] = dt.strftime("%Y-%m-%d")
        elif name == "Subject":
            data["betreff"] = value
        elif name == "From":
            data["absender"] = value
        elif name == "To":
            data["empfaenger"] = value
        elif name == "Cc":
            data["cc"] = value
        elif name == "Bcc":
            data["bcc"] = value

    def has_attachments(payload):
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    return True
                if has_attachments(part):
                    return True
        return False

    data["anhang_vorhanden"] = has_attachments(payload)
    return data


def list_gmail_messages():
    service = authenticate_gmail()
    results = service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        maxResults=50
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        parsed = parse_email(msg)
        emails.append(parsed)

    return emails

def send_reply(message_id, to, subject, body):
    """
    Antwortet auf eine E-Mail mit der gegebenen ID.
    :param message_id: Die ID der ursprünglichen E-Mail (threadId oder id)
    :param to: Empfängeradresse (z.B. aus der Originalmail)
    :param subject: Betreff der Antwort
    :param body: Text der Antwort
    :return: API-Antwort
    """
    service = authenticate_gmail()
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = "Re: " + subject
    message['In-Reply-To'] = message_id
    message['References'] = message_id

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {
        'raw': raw,
        'threadId': message_id
    }
    sent_message = service.users().messages().send(userId="me", body=body).execute()
    return sent_message

def archive_email(message_id):
    """
    Archiviert eine E-Mail, indem das Label 'INBOX' entfernt wird.
    :param message_id: Die ID der zu archivierenden E-Mail
    :return: API-Antwort
    """
    service = authenticate_gmail()
    result = service.users().messages().modify(
        userId='me',
        id=message_id,
        body={'removeLabelIds': ['INBOX']}
    ).execute()
    return result