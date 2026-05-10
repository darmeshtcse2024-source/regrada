import streamlit as st
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://regrada.streamlit.app",
    "X-Title": "RegRadar"
}

st.set_page_config(
    page_title="RegRadar — GST Alerts for MSMEs",
    page_icon="📡",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
    .main-header p  { color: #a8b2d8; font-size: 1rem; margin: 0.5rem 0 0; }
    .alert-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #e94560;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .alert-title { font-size: 1rem; font-weight: 600; color: #1a202c; margin-bottom: 0.5rem; }
    .alert-meta  { font-size: 0.78rem; color: #718096; margin-bottom: 0.8rem; }
    .alert-eng   { font-size: 0.9rem; color: #2d3748; line-height: 1.6; margin-bottom: 0.8rem; }
    .alert-tamil {
        background: #f0fff4;
        border: 1px solid #c6f6d5;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
        color: #276749;
        line-height: 1.7;
    }
    .tamil-label { font-size: 0.72rem; font-weight: 600; color: #38a169; margin-bottom: 4px; }
    .category-badge {
        display: inline-block;
        background: #ebf4ff;
        color: #3182ce;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
        margin-right: 6px;
    }
    .chat-answer {
        background: #f7fafc;
        border-left: 3px solid #4299e1;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        font-size: 0.92rem;
        color: #2d3748;
        line-height: 1.7;
        margin-top: 1rem;
    }
    .stat-box {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-num   { font-size: 2rem; font-weight: 700; color: #e94560; }
    .stat-label { font-size: 0.8rem; color: #718096; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
BUSINESS_KEYWORDS = {
    "restaurant": ["restaurant", "food", "hotel", "catering", "dining"],
    "kirana":     ["kirana", "retail", "shop", "store", "composition", "ecommerce"],
    "textile":    ["textile", "garment", "fabric", "HSN", "clothing", "apparel"],
    "pharmacy":   ["pharmacy", "medicine", "drug", "medical", "prescription"],
    "it_services":["IT", "software", "technology", "services", "export"],
    "general":    ["general", "all", "taxpayer", "GSTR", "filing", "return"]
}

BUSINESS_OPTIONS = {
    "🍽️  Restaurant / Food Business":  "restaurant",
    "🛒  Kirana / Retail Store":        "kirana",
    "👕  Textile / Garment Business":   "textile",
    "💊  Pharmacy / Medical Store":     "pharmacy",
    "💻  IT Services / Consulting":     "it_services",
    "🏢  General / Other Business":     "general",
}

# Try multiple free models in order until one works
FREE_MODELS = [
    "google/gemma-3-1b-it:free",
    "qwen/qwen3-0.6b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "deepseek/deepseek-r1-0528:free",
    "microsoft/phi-3-mini-128k-instruct:free",
]

# ─────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────
def load_alerts():
    try:
        with open("alerts.json", "r", encoding="utf-8") as f:
            return json.load(f).get("alerts", [])
    except:
        return []

def filter_alerts(alerts, business_type):
    relevant = []
    keywords = BUSINESS_KEYWORDS.get(business_type, [])
    for alert in alerts:
        if business_type in alert.get("affects", []) or \
           "general" in alert.get("affects", []):
            if alert not in relevant:
                relevant.append(alert)
            continue
        raw = alert.get("raw_text", "").lower()
        title = alert.get("title", "").lower()
        if any(kw.lower() in raw or kw.lower() in title for kw in keywords):
            if alert not in relevant:
                relevant.append(alert)
    return relevant

def call_ai(prompt):
    # Try each model until one works
    for model in FREE_MODELS:
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0.7
                },
                timeout=30
            )
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                text = data["choices"][0]["message"]["content"].strip()
                if text:
                    return text

            # If this model failed, try next one
            continue

        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    return "All AI models are currently busy. Please try again in 30 seconds."
def call_ai(prompt):
    try:
        response = requests.post(
            API_URL,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        data = response.json()
        if "candidates" in data:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif "error" in data:
            return f"Error: {data['error']['message']}"
        return "No response. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"
def explain_english(alert, business_type):
    return call_ai(f"""You are a GST advisor for Indian small businesses.

A {business_type} owner needs to understand this GST alert:
Title: {alert['title']}
Details: {alert['raw_text']}

Write exactly 3 simple sentences:
1. What the rule says
2. How it affects a {business_type} owner
3. What action to take

No jargon. No bullet points. Plain simple English only.""")

def translate_tamil(text):
    return call_ai(f"""Translate this to simple Tamil for a small shop owner in Tamil Nadu.
Use conversational Tamil, not legal language.
Give only the Tamil translation, nothing else.

English: {text}""")

def answer_question(question, business_type, alerts):
    context = "\n".join([
        f"- {a['title']}: {a['raw_text'][:120]}"
        for a in alerts[:4]
    ])
    return call_ai(f"""You are RegRadar, a GST compliance assistant for Indian small businesses.

Business type: {business_type}
Question: {question}

GST alerts context:
{context}

Answer in 3 clear practical sentences. Say "Please verify with your CA" if unsure.""")


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📡 RegRadar</h1>
    <p>AI-powered GST compliance alerts for Indian MSMEs — in your language</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SCREEN 1 — BUSINESS SELECTOR
# ─────────────────────────────────────────────
st.markdown("### 🏪 Select Your Business Type")
selected_label = st.selectbox("Choose your business:", list(BUSINESS_OPTIONS.keys()))
business_type = BUSINESS_OPTIONS[selected_label]
st.markdown("---")


# ─────────────────────────────────────────────
# SCREEN 2 — ALERT DASHBOARD
# ─────────────────────────────────────────────
st.markdown("### 📋 Your GST Alerts")

all_alerts = load_alerts()
if not all_alerts:
    st.error("alerts.json not found. Please add it to your GitHub repo.")
    st.stop()

relevant_alerts = filter_alerts(all_alerts, business_type)

if not relevant_alerts:
    st.warning("No alerts found for this business type.")
else:
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(relevant_alerts)}</div><div class="stat-label">Active Alerts</div></div>', unsafe_allow_html=True)
    with col2:
        d = len([a for a in relevant_alerts if a.get("category") == "Filing Deadline"])
        st.markdown(f'<div class="stat-box"><div class="stat-num">{d}</div><div class="stat-label">Deadlines</div></div>', unsafe_allow_html=True)
    with col3:
        r = len([a for a in relevant_alerts if a.get("category") == "Rate Change"])
