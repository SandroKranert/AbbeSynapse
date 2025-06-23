import os
import base64
import email
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8085)
        with open('token.json', 'w') as token:
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
        if h["name"] == "Date":
            dt = email.utils.parsedate_to_datetime(h["value"])
            data["uhrzeit"] = dt.strftime("%H:%M")
            data["datum"] = dt.strftime("%Y-%m-%d")
        elif h["name"] == "Subject":
            data["betreff"] = h["value"]
        elif h["name"] == "From":
            data["absender"] = h["value"]
        elif h["name"] == "To":
            data["empfaenger"] = h["value"]
        elif h["name"] == "Cc":
            data["cc"] = h["value"]
        elif h["name"] == "Bcc":
            data["bcc"] = h["value"]

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
        maxResults=50  # oder beliebig viele
    ).execute()
    messages = results.get('messages', [])
    emails = []

    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        parsed = parse_email(msg)
        emails.append(parsed)

    return emails