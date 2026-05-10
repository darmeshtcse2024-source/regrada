import streamlit as st
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# SETUP — Gemini via REST API
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

def call_ai(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        response = requests.post(
            url,
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

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(relevant_alerts)}</div><div class="stat-label">Active Alerts</div></div>', unsafe_allow_html=True)
    with col2:
        d = len([a for a in relevant_alerts if a.get("category") == "Filing Deadline"])
        st.markdown(f'<div class="stat-box"><div class="stat-num">{d}</div><div class="stat-label">Deadlines</div></div>', unsafe_allow_html=True)
    with col3:
        r = len([a for a in relevant_alerts if a.get("category") == "Rate Change"])
        st.markdown(f'<div class="stat-box"><div class="stat-num">{r}</div><div class="stat-label">Rate Changes</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cache_key = f"enriched_{business_type}"
    if cache_key not in st.session_state:
        with st.spinner("🤖 RegRadar AI is reading your GST alerts..."):
            enriched = []
            for alert in relevant_alerts[:3]:
                eng = explain_english(alert, business_type)
                tam = translate_tamil(eng)
                enriched.append({
                    "title": alert["title"],
                    "date": alert["date"],
                    "category": alert["category"],
                    "english": eng,
                    "tamil": tam
                })
            st.session_state[cache_key] = enriched

    for item in st.session_state[cache_key]:
        st.markdown(f"""
        <div class="alert-card">
            <div class="alert-title">{item['title']}</div>
            <div class="alert-meta">
                <span class="category-badge">{item['category']}</span>
                📅 {item['date']}
            </div>
            <div class="alert-eng">{item['english']}</div>
            <div class="tamil-label">🇮🇳 தமிழில் படிக்கவும்</div>
            <div class="alert-tamil">{item['tamil']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# SCREEN 3 — Q&A CHAT
# ─────────────────────────────────────────────
st.markdown("### 💬 Ask RegRadar")
st.markdown("Type any GST question — RegRadar answers instantly.")

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📅 Do I need to file GSTR-9?"):
        st.session_state.question_input = "Do I need to file GSTR-9 this year?"
with c2:
    if st.button("💰 Any rate changes for me?"):
        st.session_state.question_input = f"Any GST rate changes for my {business_type}?"
with c3:
    if st.button("⚠️ What deadlines are coming?"):
        st.session_state.question_input = "What GST deadlines are coming up soon?"

user_q = st.text_input(
    "Your question:",
    value=st.session_state.question_input,
    placeholder="e.g. Do I need e-invoicing? When is my GST deadline?"
)

if st.button("🔍 Get Answer", type="primary"):
    if user_q.strip():
        with st.spinner("RegRadar is thinking..."):
            ans = answer_question(user_q, business_type, relevant_alerts)
        st.session_state["last_answer"] = ans
    else:
        st.warning("Please type a question first.")

if "last_answer" in st.session_state:
    st.markdown(f"""
    <div class="chat-answer">
        <strong>RegRadar:</strong><br><br>
        {st.session_state['last_answer']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#a0aec0;font-size:0.8rem'>"
    "RegRadar — Built for ET AI Hackathon 2.0 | Not a substitute for professional CA advice"
    "</p>",
    unsafe_allow_html=True
)
