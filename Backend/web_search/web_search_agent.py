import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from serpapi import GoogleSearch
from datetime import datetime

# Lade Umgebungsvariablen
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")

# OpenAI-Client
client = OpenAI(api_key=openai_api_key)

def write_to_log(prompt, summary, results):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "search_query": prompt,
        "ai_summary": summary,
        "num_results": len(results)
    }
    log_path = os.path.join(os.path.dirname(__file__), "log.json")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []
    log_data.append(log_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=4, ensure_ascii=False)

def create_web_search_agent(prompt: str):
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

    context_for_ai = "\n\n".join(
        [f"Titel: {r.get('title')}\nSnippet: {r.get('snippet')}" for r in organic_results[:10]]
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein Experte für Webinhalte."},
            {"role": "user", "content": f"Fasse zusammen: {context_for_ai}"}
        ]
    )
    ai_summary = response.choices[0].message.content

    output_data = {
        "search_query": prompt,
        "ai_summary": ai_summary,
        "search_results": [
            {
                "position": r.get("position"),
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet"),
                "source": r.get("source")
            }
            for r in organic_results
        ]
    }

    write_to_log(prompt, ai_summary, organic_results)

    return output_data
