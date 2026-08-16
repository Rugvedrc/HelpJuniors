import os
import sqlite3
from datetime import datetime

import streamlit as st
import pandas as pd
from db.database import get_eligible_jobs_from_db, get_quarantined_jobs_from_db, get_rejected_jobs_from_db
from telegram_bot import format_jobs_message, send_message, get_telegram_token

st.set_page_config(
    page_title="Job-Discovery Agent — Access Restricted",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0b0f19; }
.main { background-color: #0b0f19; }

.lock-container {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 45px 35px;
    text-align: center;
    margin-top: 60px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.lock-icon {
    font-size: 3.5rem;
    margin-bottom: 16px;
    display: inline-block;
}

.lock-title {
    color: #f8fafc;
    font-size: 1.9rem;
    font-weight: 800;
    margin-bottom: 10px;
    letter-spacing: -0.02em;
}

.lock-sub {
    color: #f59e0b;
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 24px;
}

.lock-msg {
    color: #94a3b8;
    font-size: 1.0rem;
    line-height: 1.6;
    margin-bottom: 28px;
}

.contact-box {
    background: #0284c715;
    border: 1px solid #0284c740;
    border-radius: 12px;
    padding: 16px 20px;
    display: inline-block;
    color: #38bdf8;
    font-weight: 700;
    font-size: 1.05rem;
    text-decoration: none !important;
}

.contact-box a {
    color: #38bdf8 !important;
    text-decoration: underline !important;
}

.tg-badge {
    margin-top: 24px;
    font-size: 0.88rem;
    color: #64748b;
}

.tg-badge a {
    color: #f59e0b !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def start_background_telegram_daemon():
    token = get_telegram_token()
    if token:
        import threading
        from telegram_bot import run_telegram_bot_polling
        t = threading.Thread(target=run_telegram_bot_polling, args=(token,), daemon=True)
        t.start()
        print("🤖 Background Telegram Bot Listener active on Streamlit Cloud!")


def main():
    # 1. Keep Telegram Bot Daemon active 24/7 in background thread
    start_background_telegram_daemon()

    # 2. Sidebar Admin Login (Optional for Rugved)
    passcode = st.sidebar.text_input("🔑 Admin Access Key", type="password")

    # If passcode matched, show full dashboard
    if passcode and passcode.strip() == "rugved2026":
        st.sidebar.success("Admin Authenticated")
        render_admin_dashboard()
        return

    # 3. Restricted Access Screen for general visitors
    st.markdown("""
    <div class="lock-container">
        <div class="lock-icon">🔒</div>
        <div class="lock-title">ACCESS RESTRICTED</div>
        <div class="lock-sub">Personal Job-Discovery Agent — Candidate Engine</div>
        <div class="lock-msg">
            You cannot access this dashboard directly.<br/>
            If you want to access or know more about it, please contact:
        </div>
        <div class="contact-box">
            📧 <a href="mailto:rugvedchandekar@gmail.com">rugvedchandekar@gmail.com</a>
        </div>
        <div class="tg-badge">
            🤖 Telegram Bot Active: <a href="https://t.me/RugvedJobBot" target="_blank">@RugvedJobBot</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_admin_dashboard():
    """Render full dashboard if admin passcode is entered."""
    from db.database import get_eligible_jobs_from_db, get_quarantined_jobs_from_db, get_rejected_jobs_from_db

    st.markdown("## 🎯 Personal Job-Discovery Agent — Admin Panel")
    eligible_df = get_eligible_jobs_from_db()

    if st.button("🔄 Run Discovery Pipeline"):
        with st.spinner("Running pipeline..."):
            from pipeline.runner import run_job_discovery_pipeline
            run_job_discovery_pipeline()
            st.success("Pipeline complete!")
            st.rerun()

    st.markdown(f"**Eligible Jobs ({len(eligible_df)}):**")
    st.dataframe(eligible_df[["company", "title", "location", "experience_text", "canonical_url"]], width=None)


if __name__ == "__main__":
    main()
