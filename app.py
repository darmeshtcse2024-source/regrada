import streamlit as st
import json
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
try:
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
    client = genai.Client(api_key=api_key)
    MODEL =  "gemini-2.0-flash"
except Exception as e:
    st.error(f"API setup error: {e}")

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
    .alert-title  { font-size: 1rem; font-weight: 600; color: #1a202c; margin-bottom: 0.5rem; }
    .alert-meta   { font-size: 0.78rem; color: #718096; margin-bottom: 0.8rem; }
    .alert-eng    { font-size: 0.9rem; color: #2d3748; line-height: 1.6; margin-bottom: 0.8rem; }
    .alert-tamil  {
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
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
BUSINESS_KEYWORDS = {
    "restaurant": ["restaurant", "food", "hotel", "catering", "dining"],
    "kirana":     ["kirana", "retail", "shop", "store", "composition", "ecommerce"],
    "textile":    ["textile", "garment", "fabric", "HSN", "clothing", "apparel"],
    "pharmacy":   ["pharmacy", "medicine", "drug", "medical", "prescription"],
    "it_services":["IT", "software", "technology", "services", "export"],
    "general":    ["general", "all", "taxpayer", "GSTR", "filing", "return"]
}

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
        if business_type in alert.get("affects", []) or "general" in alert.get("affects", []):
            if alert not in relevant:
                relevant.append(alert)
            continue
        raw = alert.get("raw_text", "").lower()
        title = alert.get("title", "").lower()
        if any(kw.lower() in raw or kw.lower() in title for kw in keywords):
            if alert not in relevant:
                relevant.append(alert)
    return relevant

def call_gemini(prompt):
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def explain_english(alert, business_type):
    prompt = f"""You are a GST advisor helping Indian small business owners.

A {business_type} owner needs to understand this alert:
Title: {alert['title']}
Details: {alert['raw_text']}

Write exactly 3 simple sentences:
1. What the rule says
2. How it affects a {business_type}
3. What action to take

No jargon. No bullet points. Plain simple English only."""
    return call_gemini(prompt)

def translate_tamil(text):
    prompt = f"""Translate this to simple Tamil that a small shop owner in Tamil Nadu understands.
Use everyday conversational Tamil, not legal Tamil.

Text: {text}

Give only the Tamil translation, nothing else."""
    return call_gemini(prompt)

def answer_question(question, business_type, alerts):
    context = "\n".join([
        f"- {a['title']}: {a['raw_text'][:150]}"
        for a in alerts[:5]
    ])
    prompt = f"""You are RegRadar, a GST compliance assistant for Indian small businesses.

Business type: {business_type}
User question: {question}

Recent GST alerts:
{context}

Answer in 3-4 simple sentences. Be direct and practical.
If unsure, say "Please verify with your CA."
Do not make up rules not mentioned above."""
    return call_gemini(prompt)


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

BUSINESS_OPTIONS = {
    "🍽️  Restaurant / Food Business":  "restaurant",
    "🛒  Kirana / Retail Store":        "kirana",
    "👕  Textile / Garment Business":   "textile",
    "💊  Pharmacy / Medical Store":     "pharmacy",
    "💻  IT Services / Consulting":     "it_services",
    "🏢  General / Other Business":     "general",
}

selected_label = st.selectbox(
    "Choose your business:",
    list(BUSINESS_OPTIONS.keys())
)
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
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-num">{len(relevant_alerts)}</div><div class="stat-label">Active Alerts</div></div>', unsafe_allow_html=True)
    with col2:
        deadlines = len([a for a in relevant_alerts if a.get("category") == "Filing Deadline"])
        st.markdown(f'<div class="stat-box"><div class="stat-num">{deadlines}</div><div class="stat-label">Deadlines</div></div>', unsafe_allow_html=True)
    with col3:
        rates = len([a for a in relevant_alerts if a.get("category") == "Rate Change"])
        st.markdown(f'<div class="stat-box"><div class="stat-num">{rates}</div><div class="stat-label">Rate Changes</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Cache key for this business
    cache_key = f"enriched_{business_type}"

    if cache_key not in st.session_state:
        with st.spinner("🤖 RegRadar AI is reading your GST alerts..."):
            enriched = []
            for alert in relevant_alerts[:4]:
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

    enriched = st.session_state[cache_key]

    for item in enriched:
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
st.markdown("Type any GST question — RegRadar answers based on latest alerts.")

# Quick question buttons
st.markdown("**Quick questions:**")
c1, c2, c3 = st.columns(3)

if "question_input" not in st.session_state:
    st.session_state.question_input = ""

with c1:
    if st.button("📅 Do I need to file GSTR-9?"):
        st.session_state.question_input = "Do I need to file GSTR-9 this year?"
with c2:
    if st.button("💰 Any rate changes for me?"):
        st.session_state.question_input = f"Any GST rate changes for my {business_type} business?"
with c3:
    if st.button("⚠️ What deadlines are coming?"):
        st.session_state.question_input = "What GST deadlines are coming up soon?"

# Text input
user_q = st.text_input(
    "Your question:",
    value=st.session_state.question_input,
    placeholder="e.g. Do I need e-invoicing? When is my GST deadline?"
)

# Get Answer button
if st.button("🔍 Get Answer", type="primary"):
    if user_q.strip():
        with st.spinner("RegRadar is thinking..."):
            ans = answer_question(user_q, business_type, relevant_alerts)
        st.session_state["last_answer"] = ans
        st.session_state["last_question"] = user_q
    else:
        st.warning("Please type a question first.")

# Show answer
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
