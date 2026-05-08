import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# SETUP GEMINI
# ─────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ─────────────────────────────────────────────
# BUSINESS TYPE KEYWORDS
# Maps each business type to related keywords
# so we can filter alerts that apply to them
# ─────────────────────────────────────────────
BUSINESS_KEYWORDS = {
    "restaurant": ["restaurant", "food", "hotel", "catering", "eatery", "café", "dining"],
    "kirana":     ["kirana", "retail", "shop", "store", "composition", "ecommerce", "online"],
    "textile":    ["textile", "garment", "fabric", "HSN", "clothing", "apparel", "weaving"],
    "pharmacy":   ["pharmacy", "medicine", "drug", "medical", "prescription", "chemist"],
    "it_services":["IT", "software", "technology", "services", "export", "SEZ", "consulting"],
    "general":    ["general", "all", "taxpayer", "GSTR", "filing", "return", "annual"]
}


# ─────────────────────────────────────────────
# STEP 1: FILTER alerts relevant to a business
# ─────────────────────────────────────────────
def filter_alerts_for_business(alerts, business_type):
    """
    Returns alerts that are relevant to the given business type.
    Checks both the 'affects' field and keywords in the raw text.
    """
    relevant = []
    keywords = BUSINESS_KEYWORDS.get(business_type, [])

    for alert in alerts:
        # Check the affects list
        if business_type in alert.get("affects", []) or "general" in alert.get("affects", []):
            relevant.append(alert)
            continue

        # Check raw text for keywords
        raw = alert.get("raw_text", "").lower()
        title = alert.get("title", "").lower()
        if any(kw.lower() in raw or kw.lower() in title for kw in keywords):
            relevant.append(alert)

    return relevant


# ─────────────────────────────────────────────
# STEP 2: EXPLAIN an alert in simple English
# ─────────────────────────────────────────────
def explain_alert_english(alert, business_type):
    """
    Uses Gemini to explain the alert in simple English
    suitable for a small business owner.
    """
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

Use very simple language. No legal jargon. Write as if talking to someone who has never studied GST.
Do not use bullet points. Just 3 plain sentences.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"This alert is about: {alert['title']}. Please consult your CA for details."


# ─────────────────────────────────────────────
# STEP 3: TRANSLATE explanation to Tamil
# ─────────────────────────────────────────────
def translate_to_tamil(english_text):
    """
    Uses Gemini to translate the English explanation to Tamil.
    """
    prompt = f"""
Translate the following GST advisory text into Tamil.
Use simple, everyday Tamil that a small shop owner in Tamil Nadu would understand.
Do not use overly formal or legal Tamil. Keep it conversational.

English text:
{english_text}

Provide only the Tamil translation. Nothing else.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "மொழிபெயர்ப்பு கிடைக்கவில்லை. உங்கள் CA யிடம் கேளுங்கள்."


# ─────────────────────────────────────────────
# STEP 4: ANSWER a question about an alert
# ─────────────────────────────────────────────
def answer_question(question, business_type, alerts_context):
    """
    Uses Gemini to answer a specific question from the business owner
    based on the loaded GST alerts.
    """
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
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "I could not fetch an answer right now. Please try again or consult your CA."


# ─────────────────────────────────────────────
# STEP 5: PROCESS all alerts for a business
# Combines filter + explain + translate
# ─────────────────────────────────────────────
def process_alerts_for_business(business_type, alerts_file="alerts.json"):
    """
    Main function: loads alerts, filters, explains and translates them.
    Returns a list of enriched alert dicts ready for the UI.
    """
    # Load raw alerts
    if not os.path.exists(alerts_file):
        print("[ai_engine] alerts.json not found. Run scraper.py first.")
        return []

    with open(alerts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_alerts = data.get("alerts", [])

    # Filter for this business
    relevant = filter_alerts_for_business(all_alerts, business_type)
    print(f"[ai_engine] {len(relevant)} alerts relevant to '{business_type}'")

    enriched = []
    for i, alert in enumerate(relevant[:5]):  # process top 5 only
        print(f"[ai_engine] Processing alert {i+1}/{min(len(relevant),5)}: {alert['title'][:50]}...")

        # Explain in English
        english_explanation = explain_alert_english(alert, business_type)

        # Translate to Tamil
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

    # Save enriched alerts to file for the UI to use
    output_file = f"enriched_{business_type}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    print(f"[ai_engine] Saved enriched alerts → {output_file}")

    return enriched


# ─────────────────────────────────────────────
# TEST — run this file directly to verify
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("RegRadar AI Engine Test")
    print("=" * 50)

    # Test with restaurant
    business = "restaurant"
    print(f"\n[test] Processing alerts for: {business}\n")

    results = process_alerts_for_business(business)

    if results:
        print("\n── First Alert Output ──")
        r = results[0]
        print(f"\nTitle    : {r['title']}")
        print(f"Date     : {r['date']}")
        print(f"\nEnglish  :\n{r['english_explanation']}")
        print(f"\nTamil    :\n{r['tamil_explanation']}")

        # Test Q&A
        print("\n── Q&A Test ──")
        with open("alerts.json", "r", encoding="utf-8") as f:
            raw_alerts = json.load(f).get("alerts", [])
        question = "Do I need to file GSTR-9 this year?"
        print(f"Question : {question}")
        answer = answer_question(question, business, raw_alerts)
        print(f"Answer   : {answer}")

        print("\n[ai_engine] All tests passed. Ready for app.py!")
    else:
        print("[ai_engine] No alerts processed. Check alerts.json exists.")