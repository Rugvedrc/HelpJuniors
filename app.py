import os
import sqlite3
from datetime import datetime

import streamlit as st
import pandas as pd
from db.database import get_eligible_jobs_from_db, get_quarantined_jobs_from_db, get_rejected_jobs_from_db
from telegram_bot import format_jobs_message, send_message, get_telegram_token

st.set_page_config(
    page_title="Job-Discovery Agent — Rugved",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #0e1117; }
.header-box {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    padding: 22px 28px; border-radius: 14px; border: 1px solid #334155; margin-bottom: 24px;
}
.header-title { color: #f8fafc; font-size: 2.0rem; font-weight: 700; margin: 0; }
.header-title span { color: #f59e0b; }
.header-sub { color: #94a3b8; font-size: 0.95rem; margin-top: 6px; }
.job-card {
    background-color: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 20px; margin-bottom: 14px; transition: border-color 0.2s ease;
}
.job-card:hover { border-color: #f59e0b; }
.job-title { font-size: 1.15rem; font-weight: 700; color: #f8fafc; }
.match-badge {
    background: linear-gradient(90deg, #059669, #10b981);
    color: #ecfdf5; font-size: 0.85rem; font-weight: 700;
    padding: 4px 12px; border-radius: 20px; float: right;
}
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.76rem; font-weight: 600; margin-right: 6px; margin-bottom: 6px;
}
.badge-comp { background-color: #1e40af; color: #bfdbfe; }
.badge-src  { background-color: #3730a3; color: #c7d2fe; }
.badge-loc  { background-color: #0f766e; color: #99f6e4; }
.badge-exp  { background-color: #065f46; color: #6ee7b7; }
.badge-cat  { background-color: #334155; color: #cbd5e1; }
.qualify-box {
    background-color: #0f2027; border-left: 4px solid #10b981;
    padding: 12px 16px; border-radius: 6px; color: #e2e8f0; font-size: 0.88rem; margin-bottom: 12px;
    line-height: 1.7;
}
.apply-btn {
    display: inline-block; background-color: #f59e0b; color: #0f172a !important;
    padding: 9px 20px; font-weight: 700; font-size: 0.88rem;
    border-radius: 8px; text-decoration: none !important; margin-top: 10px;
}
.stat-box {
    background: #1e293b; border: 1px solid #334155; border-radius: 10px;
    padding: 14px 18px; text-align: center;
}
.stat-num { font-size: 2.2rem; font-weight: 800; color: #f59e0b; }
.stat-label { font-size: 0.8rem; color: #94a3b8; margin-top: 2px; }
.warn-box { background: #431407; border-left: 4px solid #ea580c; padding: 10px 14px; border-radius: 6px; color: #fed7aa; margin-bottom: 10px; }
.tg-box { background: #0c4a6e; border-left: 4px solid #0284c7; padding: 14px 18px; border-radius: 8px; color: #e0f2fe; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)


def get_db_stats():
    """Return aggregate counts directly from DB."""
    from db.database import DB_FILE, init_db
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df_all = pd.read_sql_query("SELECT eligibility_status, source, company, rejection_reason FROM jobs", conn)
    conn.close()
    return df_all


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
    start_background_telegram_daemon()
    st.markdown("""
    <div class="header-box">
        <h1 class="header-title">🎯 Personal <span>Job-Discovery Agent</span></h1>
        <div class="header-sub">
            Rugved Rajesh Chandekar &nbsp;|&nbsp; B.Tech IT 2026 &nbsp;|&nbsp; Entry-Level &nbsp;|&nbsp; India Only &nbsp;|&nbsp; Product Tech Companies
            &nbsp;|&nbsp; <em>High-precision filter: only what you realistically qualify for</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────
    st.sidebar.markdown("### ⚙️ Controls")
    if st.sidebar.button("🔄 Run Discovery Pipeline", width="stretch", type="primary"):
        with st.spinner("Running multi-source discovery → eligibility → ranking..."):
            from pipeline.runner import run_job_discovery_pipeline
            run_job_discovery_pipeline()
            st.cache_data.clear()
            st.success("Pipeline complete!")
            st.rerun()

    eligible_df = get_eligible_jobs_from_db()
    if eligible_df.empty:
        st.info("No jobs in database yet. Click **Run Discovery Pipeline** to start.")
        return

    all_stats = get_db_stats()
    total_discovered = len(all_stats)
    total_eligible = int(all_stats["eligibility_status"].sum())
    total_rejected = total_discovered - total_eligible

    # ── Source breakdown ─────────────────────────────────────────────────
    source_dist = all_stats.groupby("source").size().reset_index(name="count").sort_values("count", ascending=False)

    # ── Sidebar filters ──────────────────────────────────────────────────
    search = st.sidebar.text_input("🔍 Search", placeholder="role, company, skill...")
    all_comps = sorted(eligible_df["company"].dropna().unique())
    sel_comps = st.sidebar.multiselect("🏢 Companies", options=all_comps)
    all_cats = sorted(eligible_df["category"].dropna().unique())
    sel_cats = st.sidebar.multiselect("📂 Category", options=all_cats)
    all_srcs = sorted(eligible_df["source"].dropna().unique())
    sel_srcs = st.sidebar.multiselect("📡 Source", options=all_srcs)

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**DB Stats**\n\n"
                        f"- Total discovered: **{total_discovered}**\n"
                        f"- Eligible: **{total_eligible}**\n"
                        f"- Rejected: **{total_rejected}**")

    # ── Apply filters ─────────────────────────────────────────────────────
    fdf = eligible_df.copy()
    if sel_comps:   fdf = fdf[fdf["company"].isin(sel_comps)]
    if sel_cats:    fdf = fdf[fdf["category"].isin(sel_cats)]
    if sel_srcs:    fdf = fdf[fdf["source"].isin(sel_srcs)]
    if search:
        sq = search.lower()
        mask = (
            fdf["title"].str.lower().str.contains(sq, na=False) |
            fdf["company"].str.lower().str.contains(sq, na=False) |
            fdf["qualifications"].str.lower().str.contains(sq, na=False) |
            fdf["description"].str.lower().str.contains(sq, na=False)
        )
        fdf = fdf[mask]

    # ── TABS ──────────────────────────────────────────────────────────────
    tab_elig, tab_stats, tab_rej, tab_quar, tab_telegram = st.tabs([
        f"🔥 Eligible Jobs ({len(fdf)})",
        "📊 Source & Pipeline Stats",
        f"🔍 Rejected Audit ({total_rejected})",
        "🛡️ Quarantined",
        "🤖 Telegram Bot & Deployment"
    ])

    # ── TAB 1: Eligible ───────────────────────────────────────────────────
    with tab_elig:
        PAGE_SIZE = 50
        total_pages = max(1, (len(fdf) - 1) // PAGE_SIZE + 1)
        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.markdown(f"**{len(fdf)} eligible jobs** sorted by match score (page {1}/{total_pages})")
        with col_r:
            page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, label_visibility="collapsed") if total_pages > 1 else 1

        start = (page_num - 1) * PAGE_SIZE
        page_df = fdf.iloc[start : start + PAGE_SIZE]

        for _, row in page_df.iterrows():
            loc_display = row.get("location") or row.get("city") or "India"
            exp_display = str(row.get("experience_text", "Entry-level"))[:80]
            src_display = row.get("source", "")
            cat_display = row.get("category", "")
            score = row.get("relevance_score", 0)

            st.markdown(f"""
            <div class="job-card">
                <span class="match-badge">🎯 {score:.0f}%</span>
                <div class="job-title">[{row['company']}] {row['title']}</div>
                <div style="margin-top: 10px;">
                    <span class="badge badge-src">📡 {src_display}</span>
                    <span class="badge badge-cat">📂 {cat_display}</span>
                    <span class="badge badge-loc">📍 {loc_display}</span>
                    <span class="badge badge-exp">🎓 {exp_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📖 Why it qualifies + Details"):
                st.markdown(f"""
                <div class="qualify-box">
                    <strong>✅ Why This Job Qualifies:</strong><br/>
                    &bull; <strong>Company:</strong> {row['company']} ({row.get('company_type','PRODUCT')})<br/>
                    &bull; <strong>Role:</strong> {row.get('category','')} / {row.get('sub_category','')}<br/>
                    &bull; <strong>Experience:</strong> {row.get('experience_text','Entry-level')}<br/>
                    &bull; <strong>Location:</strong> {loc_display}<br/>
                    &bull; <strong>Source:</strong> {src_display}
                </div>
                """, unsafe_allow_html=True)
                desc = str(row.get("description", ""))
                quals = str(row.get("qualifications", ""))
                if desc and desc != "nan":
                    st.markdown(f"**Description:** {desc[:600]}")
                if quals and quals != "nan":
                    st.markdown(f"**Qualifications:** {quals[:600]}")
                apply_url = row.get("canonical_url") or row.get("apply_url", "#")
                st.markdown(f'<a href="{apply_url}" target="_blank" class="apply-btn">🚀 Apply Now</a>', unsafe_allow_html=True)

            st.markdown("<hr style='margin:6px 0; border-color:#1e293b;'>", unsafe_allow_html=True)

    # ── TAB 2: Pipeline Stats ─────────────────────────────────────────────
    with tab_stats:
        st.markdown("### 📊 Pipeline & Source Statistics")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{total_discovered}</div><div class="stat-label">Total Discovered</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{total_eligible}</div><div class="stat-label">Eligible Jobs</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{total_rejected}</div><div class="stat-label">Rejected</div></div>', unsafe_allow_html=True)
        with c4:
            pct = round(total_eligible / total_discovered * 100, 1) if total_discovered else 0
            st.markdown(f'<div class="stat-box"><div class="stat-num">{pct}%</div><div class="stat-label">Pass Rate</div></div>', unsafe_allow_html=True)

        st.markdown("#### Source Breakdown")
        st.dataframe(source_dist, width=st.session_state.get('use_width', None))

        st.markdown("#### Company Distribution (Eligible Jobs)")
        comp_dist = eligible_df.groupby("company").size().reset_index(name="jobs").sort_values("jobs", ascending=False)
        st.dataframe(comp_dist.head(30), width=st.session_state.get('use_width', None))

        st.markdown("#### Category Distribution (Eligible Jobs)")
        cat_dist = eligible_df.groupby("category").size().reset_index(name="jobs").sort_values("jobs", ascending=False)
        st.dataframe(cat_dist, width=st.session_state.get('use_width', None))

    # ── TAB 3: Rejected Audit ─────────────────────────────────────────────
    with tab_rej:
        rej_df = get_rejected_jobs_from_db()
        st.markdown(f"### 🔍 Rejected Jobs Audit ({len(rej_df)} total)")
        st.write("These jobs were discovered but failed at least one hard eligibility gate.")

        if rej_df.empty:
            st.success("No rejected jobs — all discovered jobs are eligible!")
        else:
            rej_search = st.text_input("🔍 Filter rejections", placeholder="company, reason, location...")
            rdf = rej_df.copy()
            if rej_search:
                rsq = rej_search.lower()
                rdf = rdf[
                    rdf["company"].str.lower().str.contains(rsq, na=False) |
                    rdf["title"].str.lower().str.contains(rsq, na=False) |
                    rdf["rejection_reason"].str.lower().str.contains(rsq, na=False) |
                    rdf["location"].str.lower().str.contains(rsq, na=False)
                ]

            display_cols = ["company", "title", "rejection_reason", "location", "source", "canonical_url"]
            existing = [c for c in display_cols if c in rdf.columns]
            st.dataframe(rdf[existing], width=st.session_state.get('use_width', None))

    # ── TAB 4: Quarantined ────────────────────────────────────────────────
    with tab_quar:
        q_df = get_quarantined_jobs_from_db()
        st.markdown(f"### 🛡️ Quarantined Jobs ({len(q_df)})")
        st.write("These are jobs from unknown companies or unverified locations. Review and whitelist companies in `config/companies.json` if appropriate.")
        if q_df.empty:
            st.success("No quarantined jobs!")
        else:
            qcols = ["company", "title", "location", "source", "canonical_url"]
            existing = [c for c in qcols if c in q_df.columns]
            st.dataframe(q_df[existing], width=st.session_state.get('use_width', None))

    # ── TAB 5: Telegram Bot & Deployment ──────────────────────────────────
    with tab_telegram:
        st.markdown("### 🤖 Telegram Bot & Instant Push Controls")
        st.markdown("""
        <div class="tg-box">
            <strong>🚀 Instant Telegram Job Alerts</strong><br/>
            Connect your Telegram Bot so that sending <code>"hi"</code>, <code>"hello"</code>, <code>/start</code>, or <code>/jobs</code> 
            instantly sends a clean, formatted single message with all eligible jobs & direct apply links.
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns([1, 1])

        with col_a:
            st.markdown("#### 1. Instant Push Test")
            bot_token = st.text_input("Telegram Bot Token", value=get_telegram_token(), type="password", placeholder="e.g. 123456789:ABCdefGhIJK...")
            chat_id = st.text_input("Your Telegram Chat ID", placeholder="e.g. 123456789")

            if st.button("📲 Push All Eligible Jobs to Telegram Now", type="primary"):
                if not bot_token:
                    st.error("Please enter your Telegram Bot Token!")
                elif not chat_id:
                    st.error("Please enter your Telegram Chat ID!")
                else:
                    msg = format_jobs_message()
                    send_message(bot_token, int(chat_id.strip()), msg)
                    st.success("✅ Sent all eligible jobs to your Telegram Chat!")

        with col_b:
            st.markdown("#### 2. Run Local Bot Polling")
            st.markdown("""
            To run the background bot listener locally:
            ```bash
            $env:TELEGRAM_BOT_TOKEN="your_token_from_botfather"
            python telegram_bot.py
            ```
            When running, sending **"hi"** to your Telegram bot will instantly reply with all eligible jobs & apply links!
            """)

        st.markdown("---")
        st.markdown("### ☁️ Streamlit Cloud Deployment Guide")
        st.markdown("""
        To deploy this app for free on **Streamlit Community Cloud**:

        1. **Push Code to GitHub**:
           Push your project directory (`jobhunt`) to a public/private GitHub repository.

        2. **Deploy on Streamlit**:
           - Go to [share.streamlit.io](https://share.streamlit.io)
           - Click **New App** -> Select your GitHub repository, branch (`main`), and file (`app.py`).

        3. **Set Secrets (for Telegram Token)**:
           - Under **App Settings** -> **Secrets**, add:
             ```toml
             TELEGRAM_BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ..."
             ```
           - Click **Save & Deploy**!

        Your app will be live with full database search and Telegram integration!
        """)


if __name__ == "__main__":
    main()
