import streamlit as st
import pandas as pd
import json
import os
from collections import Counter
from datetime import datetime

st.set_page_config(page_title="WebSearch Dashboard", layout="wide")
st.title("WebSearch Dashboard")

log_path = os.path.join(os.path.dirname(__file__), "log.json")


# Lade Daten
if not os.path.exists(log_path):
    st.warning("Noch keine Log-Datei vorhanden. Bitte führe zuerst eine Websuche aus.")
else:
    with open(log_path, "r", encoding="utf-8") as f:
        lines = json.load(f)  # ← vollständig einlesen

    df = pd.DataFrame(lines)

    # Konvertiere Zeit und benenne Spalten
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.rename(columns={
        "search_query": "Suchanfrage",
        "ai_summary": "KI-Zusammenfassung",
        "num_results": "Anzahl Suchergebnisse"
    }, inplace=True)

    # Länge der Zusammenfassung berechnen
    df["Länge der KI-Zusammenfassung"] = df["KI-Zusammenfassung"].apply(len)

    # Log-Einträge
    st.subheader("📂 Log-Einträge")

    def highlight_few_hits(row):
        if row["Anzahl Suchergebnisse"] < 5:
            return ["background-color: #ff6961"] * len(row)
        else:
            return [""] * len(row)

    styled_df = df[["timestamp", "Suchanfrage", "KI-Zusammenfassung", "Anzahl Suchergebnisse"]].sort_values(
        "timestamp", ascending=False
    ).style.apply(highlight_few_hits, axis=1)

    st.dataframe(styled_df, use_container_width=True)

    # Erfolgsanalyse (>=7 Treffer)
    st.subheader("✅ Erfolgsanalyse")
    successful_hits = (df["Anzahl Suchergebnisse"] >= 7).sum()
    total = len(df)
    quote = successful_hits / total * 100
    st.metric("Anfragen mit ≥7 Treffern", f"{successful_hits} von {total}", f"{quote:.1f} %")

    # 🔢 Top-Suchbegriffe
    st.subheader("🔢 Top-Suchbegriffe")
    query_counter = Counter(df["Suchanfrage"])
    top_queries = pd.DataFrame(query_counter.most_common(10), columns=["Suchanfrage", "Häufigkeit"])
    st.table(top_queries)

    # 📈 Zusammenfassungslängen & Suchergebnisse
    st.subheader("📈 Länge der Zusammenfassungen")
    st.bar_chart(df.set_index("timestamp")[["Länge der KI-Zusammenfassung"]])