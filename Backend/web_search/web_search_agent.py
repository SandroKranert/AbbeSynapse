import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch


def create_web_search_agent(prompt: str):
    """
    Der WebSearch-Agent führt eine Websuche für einen gegebenen Prompt durch und erstellt eine KI-gestützte
    Zusammenfassung.

    Args:
        prompt (str): Der Suchbegriff für die Websuche.
    """
    try:
        # Status: Lade Umgebungsvariablen
        print("🔄 Bereite die Websuche vor...")
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")

        # Websuche
        print(f"📥 Starte Websuche zu: '{prompt}'")
        search_params = {
            "q": prompt,
            "api_key": serpapi_api_key,
            "engine": "google",
            "gl": "de",
            "hl": "de"
        }
        search = GoogleSearch(search_params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])

        if not organic_results:
            print("⚠️ Keine Suchergebnisse gefunden.")
            return

        print(f"✅ Websuche erfolgreich. {len(organic_results)} Ergebnisse erhalten")

        # KI-Zusammenfassung
        print("🤖 Erstelle KI-Zusammenfassung der Suchergebnisse...")

        # Bereite den Kontext für die KI vor
        context_for_ai = "\n\n".join(
            [f"Titel: {res.get('title')}\nSnippet: {res.get('snippet')}" for res in organic_results[:10]]
        )

        system_prompt = "Du bist ein Experte für die Zusammenfassung von Webinhalten. Fasse die folgenden Informationen prägnant und auf Deutsch zusammen."
        user_content = f"Fasse die Kerninformationen aus den Suchergebnissen zum Thema '{prompt}' zusammen:\n\n{context_for_ai}"

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        ai_summary = response.choices[0].message.content
        print("✅ KI-Zusammenfassung erfolgreich erstellt.")

        # JSON-Output
        output_data = {
            "search_query": prompt,
            "ai_summary": ai_summary,
            "search_results": [
                {
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "source": result.get("source")
                } for result in organic_results
            ]
        }

        # Gibt das finale JSON-Objekt formatiert in der Konsole aus
        print(json.dumps(output_data, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    # Zum Testen außerhalb des Orchestrators
if __name__ == "__main__":
    # Starte den Agenten und frage den Benutzer nach einem Input
    search_query = input("Hallo! Gib ein Thema ein, zu dem ich suchen und eine Zusammenfassung erstellen soll: ")
    if search_query:
        create_web_search_agent(search_query)
    else:
        print("Es wurde kein Suchbegriff eingegeben. Das Programm wird beendet.")