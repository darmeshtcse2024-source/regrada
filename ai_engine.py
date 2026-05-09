import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# SETUP GEMINI (new google.genai package)
# ─────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.0-flash"

BUSINESS_KEYWORDS = {
    "restaurant": ["restaurant", "food", "hotel", "catering", "eatery", "café", "dining"],
    "kirana":     ["kirana", "retail", "shop", "store", "composition", "ecommerce", "online"],
    "textile":    ["textile", "garment", "fabric", "HSN", "clothing", "apparel", "weaving"],
    "pharmacy":   ["pharmacy", "medicine", "drug", "medical", "prescription", "chemist"],
    "it_services":["IT", "software", "technology", "services", "export", "SEZ", "consulting"],
    "general":    ["general", "all", "taxpayer", "GSTR", "filing", "return", "annual"]
}


def filter_alerts_for_business(alerts, business_type):
    relevant = []
    keywords = BUSINESS_KEYWORDS.get(business_type, [])
    for alert in alerts:
        if business_type in alert.get("affects", []) or "general" in alert.get("affects", []):
            relevant.append(alert)
            continue
        raw = alert.get("raw_text", "").lower()
        title = alert.get("title", "").lower()
        if any(kw.lower() in raw or kw.lower() in title for kw in keywords):
            relevant.append(alert)
    return relevant


def explain_alert_english(alert, business_type):
    prompt = f"""
You are a friendly GST advisor helping small Indian business owners understand tax rules.

A {business_type} owner needs to understand this GST alert:
TITLE: {alert['title']}
DETAILS: {alert['raw_text']}
CATEGORY: {alert['category']}
DATE: {alert['date']}

Write a simple explanation in exactly 3 short sentences:
1. What changed or what is the new rule
2. How it directly affects a {business_type} owner
3. What action they should take (if any)

Use very simple language. No legal jargon. No bullet points. Just 3 plain sentences.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"This alert is about: {alert['title']}. Please consult your CA for details."


def translate_to_tamil(english_text):
    prompt = f"""
Translate the following GST advisory text into Tamil.
Use simple, everyday Tamil that a small shop owner in Tamil Nadu would understand.
Do not use overly formal or legal Tamil. Keep it conversational.

English text:
{english_text}

Provide only the Tamil translation. Nothing else.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return "மொழிபெயர்ப்பு கிடைக்கவில்லை. உங்கள் CA யிடம் கேளுங்கள்."


def answer_question(question, business_type, alerts_context):
    alerts_summary = "\n".join([
        f"- {a['title']} ({a['date']}): {a['raw_text'][:200]}"
        for a in alerts_context[:5]
    ])
    prompt = f"""
You are RegRadar, an AI GST compliance assistant for Indian MSMEs.

The user is a {business_type} owner. They are asking:
"{question}"

Here are the recent GST alerts relevant to their business:
{alerts_summary}

Answer their question in simple, friendly language in 3-4 sentences.
Be specific and practical. If you don't know, say "Please check with your CA."
Do not make up rules that are not in the alerts above.
"""
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return "I could not fetch an answer right now. Please try again or consult your CA."


def process_alerts_for_business(business_type, alerts_file="alerts.json"):
    if not os.path.exists(alerts_file):
        print("[ai_engine] alerts.json not found. Run scraper.py first.")
        return []

    with open(alerts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_alerts = data.get("alerts", [])

    relevant = filter_alerts_for_business(all_alerts, business_type)
    print(f"[ai_engine] {len(relevant)} alerts relevant to '{business_type}'")

    enriched = []
    for i, alert in enumerate(relevant[:5]):
        print(f"[ai_engine] Processing alert {i+1}/{min(len(relevant),5)}...")
        english_explanation = explain_alert_english(alert, business_type)
        tamil_explanation = translate_to_tamil(english_explanation)
        enriched.append({
            "id": alert["id"],
            "title": alert["title"],
            "date": alert["date"],
            "category": alert["category"],
            "url": alert["url"],
            "english_explanation": english_explanation,
            "tamil_explanation": tamil_explanation,
            "is_sample": alert.get("is_sample", False)
        })

    output_file = f"enriched_{business_type}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    return enriched
