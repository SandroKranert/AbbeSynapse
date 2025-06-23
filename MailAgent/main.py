import json
from gmail_reader import list_gmail_messages
from ai_module import process_emails
import os

# Get path of script
path_of_script = os.path.dirname(os.path.abspath(__file__))

# Providing the requests library the Cisco Umbrella Root-CA
os.environ['REQUESTS_CA_BUNDLE'] = f'{path_of_script}\\umbrella-cert.pem'

def load_input_json(path="example_input.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_output_json(data, path="output.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Lade Input-Daten...")
    input_data = load_input_json()
    message = input_data.get("message", "")
    print("Lese alle Gmail-Nachrichten...")
    email_list = list_gmail_messages()
    print("Sende an KI-Modul...")
    output = process_emails(message, email_list)
    print("Speichere KI-Output...")
    save_output_json(output)
    print("Fertig. Ergebnis in output.json.")

if __name__ == "__main__":
    main()