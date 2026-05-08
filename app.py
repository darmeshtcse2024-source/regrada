import streamlit as st
import json
import os
from dotenv import load_dotenv
from ai_engine import (
    process_alerts_for_business,
    answer_question,
    filter_alerts_for_business
)

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RegRadar — GST Alerts for MSMEs",
    page_icon="📡",
    layout="wide"
)

# ─────────────────────────────────────────────
# CUSTOM STYLING
# ─────────────────────────────────────────────
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
    .tamil-label  { font-size: 0.72rem; font-weight: 600; color: #38a169; margin-bottom: 4px; }

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
        margin-top: 0.5rem;
    }
    .stat-box {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .stat-num  { font-size: 2rem; font-weight: 700; color: #e94560; }
    .stat-label{ font-size: 0.8rem; color: #718096; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD ALERTS FROM FILE
# ─────────────────────────────────────────────
def load_raw_alerts():
    if not os.path.exists("alerts.json"):
        return []
    with open("alerts.json", "r", encoding="utf-8") as f:
        return json.load(f).get("alerts", [])

def load_enriched(business_type):
    filepath = f"enriched_{business_type}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


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
st.markdown("RegRadar will show only the GST alerts that affect your specific business.")

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
    list(BUSINESS_OPTIONS.keys()),
    index=0
)
business_type = BUSINESS_OPTIONS[selected_label]

st.markdown("---")


# ─────────────────────────────────────────────
# SCREEN 2 — ALERT DASHBOARD
# ─────────────────────────────────────────────
st.markdown("### 📋 Your GST Alerts")

raw_alerts = load_raw_alerts()

if not raw_alerts:
    st.error("⚠️ alerts.json not found. Please run scraper.py first.")
    st.code("python scraper.py", language="bash")
    st.stop()

# Check if enriched file exists (already processed)
enriched = load_enriched(business_type)

if enriched is None:
    with st.spinner(f"🤖 RegRadar AI is reading GST alerts for your {selected_label.strip()}..."):
        enriched = process_alerts_for_business(business_type)

if not enriched:
    st.warning("No specific alerts found for your business type right now. Check back tomorrow!")
else:
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-num">{len(enriched)}</div>
            <div class="stat-label">Active Alerts</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-num">{len([a for a in enriched if a['category'] == 'Filing Deadline'])}</div>
            <div class="stat-label">Deadlines</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-num">{len([a for a in enriched if a['category'] == 'Rate Change'])}</div>
            <div class="stat-label">Rate Changes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Alert cards
    for alert in enriched:
        sample_note = " &nbsp;🔖 <em>Sample data</em>" if alert.get("is_sample") else ""
        st.markdown(f"""
        <div class="alert-card">
            <div class="alert-title">{alert['title']}</div>
            <div class="alert-meta">
                <span class="category-badge">{alert['category']}</span>
                📅 {alert['date']}{sample_note}
            </div>
            <div class="alert-eng">{alert['english_explanation']}</div>
            <div class="tamil-label">🇮🇳 தமிழில் படிக்கவும் (Tamil)</div>
            <div class="alert-tamil">{alert['tamil_explanation']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")


# ─────────────────────────────────────────────
# SCREEN 3 — AI CHAT (Q&A)
# ─────────────────────────────────────────────
st.markdown("### 💬 Ask RegRadar a Question")
st.markdown("Type any GST question in your own words — RegRadar will answer based on the latest alerts.")

# Suggested questions
st.markdown("**Quick questions:**")
q_col1, q_col2, q_col3 = st.columns(3)
suggested_q = None
with q_col1:
    if st.button("📅 Do I need to file GSTR-9?"):
        suggested_q = "Do I need to file GSTR-9 this year?"
with q_col2:
    if st.button("💰 Any rate changes for me?"):
        suggested_q = f"Are there any GST rate changes affecting my {business_type} business?"
with q_col3:
    if st.button("⚠️ What deadlines are coming?"):
        suggested_q = "What GST deadlines are coming up that I should know about?"

# Chat input
user_question = st.text_input(
    "Your question:",
    value=suggested_q if suggested_q else "",
    placeholder="e.g. Do I need e-invoicing? When is my next filing deadline?"
)

if st.button("🔍 Get Answer", type="primary") and user_question.strip():
    with st.spinner("RegRadar is thinking..."):
        answer = answer_question(user_question, business_type, raw_alerts)
    st.markdown(f"""
    <div class="chat-answer">
        <strong>RegRadar:</strong><br><br>{answer}
    </div>
    """, unsafe_allow_html=True)

    # Show source alerts
    with st.expander("📚 Source alerts used for this answer"):
        relevant = filter_alerts_for_business(raw_alerts, business_type)
        for a in relevant[:3]:
            st.markdown(f"- **{a['title']}** ({a['date']})")

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#a0aec0;font-size:0.8rem'>"
    "RegRadar — Built for ET AI Hackathon 2.0 | "
    "Data sourced from gst.gov.in | Not a substitute for professional CA advice"
    "</p>",
    unsafe_allow_html=True
)