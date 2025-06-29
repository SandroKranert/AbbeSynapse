import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from serpapi.google_search import GoogleSearch  # Geändert!

def create_web_search_agent(prompt: str):
    """
    Der WebSearch-Agent führt eine Websuche für einen gegebenen Prompt durch und erstellt eine KI-gestützte
    Zusammenfassung.
    """
    try:
        # Lade .env aus dem Backend-Root-Verzeichnis
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(backend_root, '.env')
        load_dotenv(env_path)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")

        # Websuche
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
            return {
                "search_query": prompt,
                "ai_summary": "Keine Suchergebnisse gefunden.",
                "search_results": []
            }

        # KI-Zusammenfassung
        context_for_ai = "\n\n".join(
            [f"Titel: {res.get('title')}\nSnippet: {res.get('snippet')}" for res in organic_results[:10]]
        )

        system_prompt = "Du bist ein Experte für die Zusammenfassung von Webinhalten. Fasse die folgenden Informationen prägnant und auf Deutsch zusammen."
        user_content = f"Fasse die Kerninformationen aus den Suchergebnissen zum Thema '{prompt}' zusammen:\n\n{context_for_ai}"

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        ai_summary = response.choices[0].message.content

        return {
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

    except Exception as e:
        return {
            "search_query": prompt,
            "ai_summary": f"Fehler bei der Websuche: {str(e)}",
            "search_results": [],
            "error": str(e)
        }

# Zum Testen außerhalb des Orchestrators
if __name__ == "__main__":
    search_query = input("Suchbegriff eingeben: ")
    if search_query:
        result = create_web_search_agent(search_query)
        if result:
            print(json.dumps(result, indent=4, ensure_ascii=False))
    else:
        print("Kein Suchbegriff eingegeben.")