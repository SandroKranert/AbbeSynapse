from dotenv import load_dotenv
import os
import openai
import json

load_dotenv()
client = openai.OpenAI()

def process_emails(message, email_list):
    prompt = build_prompt(message, email_list)

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher E-Mail-Filter-Assistent."},
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

def build_prompt(message, email_list):
    return f"""
Du erhältst eine Nutzeranfrage (message) und eine Liste von E-Mails. Deine Aufgabe ist es, die zur Anfrage passenden E-Mails aus der Liste auszuwählen und als JSON zurückzugeben.

Message:
{message}

E-Mails:
{json.dumps(email_list, ensure_ascii=False, indent=2)}
"""