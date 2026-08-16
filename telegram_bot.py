import os
import sys
import time
import requests
import sqlite3
import pandas as pd

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import (
    DB_FILE, init_db, get_eligible_jobs_from_db,
    get_unread_eligible_jobs, mark_all_jobs_read
)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


def get_telegram_token() -> str:
    """Fetch token from env var, .env, or streamlit secrets."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not token:
        try:
            import streamlit as st
            token = st.secrets.get("TELEGRAM_BOT_TOKEN", "").strip()
        except Exception:
            pass
    return token


def get_inline_keyboard() -> dict:
    """Prebuilt Telegram Inline Keyboard buttons so user doesn't need to type."""
    return {
        "inline_keyboard": [
            [
                {"text": "🔍 New / Unread Jobs", "callback_data": "unread_jobs"},
                {"text": "📋 All Eligible Jobs", "callback_data": "all_jobs"}
            ],
            [
                {"text": "✅ Mark All as Read", "callback_data": "mark_read"},
                {"text": "🔄 Run Discovery Sync", "callback_data": "run_sync"}
            ]
        ]
    }


def format_jobs_message(df: pd.DataFrame, title_suffix: str = "") -> str:
    """Format jobs dataframe into a single clean Telegram Markdown message."""
    if df.empty:
        return (
            "🎯 *PERSONAL JOB-DISCOVERY AGENT*\n\n"
            "✨ *You're all caught up!* 0 new unread eligible jobs.\n\n"
            "_Tap '📋 All Eligible Jobs' below to review previously seen listings, or '🔄 Run Discovery Sync' to check for fresh postings._"
        )

    lines = [
        f"🎯 *PERSONAL JOB DISCOVERY — {title_suffix.upper() or 'ELIGIBLE JOBS'}*\n",
        f"Showing *{len(df)}* high-precision eligible openings (2026 Grad / Entry-Level / India):\n"
    ]

    for idx, row in df.head(20).iterrows():
        comp = row.get("company", "Company")
        title = row.get("title", "Role")
        loc = row.get("location") or row.get("city") or "India"
        exp = str(row.get("experience_text", "Entry level"))[:50]
        url = row.get("canonical_url") or row.get("apply_url") or "#"
        score = row.get("relevance_score", 0)

        lines.append(
            f"*{idx + 1}. [{comp}] {title}*\n"
            f"📍 *Location:* {loc}\n"
            f"🎓 *Exp:* {exp}\n"
            f"🎯 *Match:* {score:.0f}%\n"
            f"🚀 [Apply Now]({url})\n"
        )

    lines.append("\n_All listings verified 100% hard eligible (No PhD req, No 1+ YOE req, Product Tech, India)_")
    return "\n".join(lines)


def send_telegram_request(token: str, method: str, payload: dict):
    url = TELEGRAM_API_URL.format(token=token, method=method)
    try:
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code != 200 and "can't parse entities" in res.text and "parse_mode" in payload:
            payload.pop("parse_mode", None)
            requests.post(url, json=payload, timeout=12)
        return res
    except Exception as e:
        print(f"Telegram API request failed ({method}): {e}")
        return None


def send_message(token: str, chat_id: int, text: str, keyboard: dict = None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    send_telegram_request(token, "sendMessage", payload)


def handle_update(token: str, update: dict):
    # Handle direct text messages
    if "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip().lower()

        if not chat_id:
            return

        print(f"📩 Received message '{text}' from Chat ID: {chat_id}")

        # Send immediate ping / awake status
        send_message(
            token, chat_id,
            "⚡ *Job Discovery Agent is Active!*\nFetching your matching openings..."
        )

        unread_df = get_unread_eligible_jobs(chat_id)
        if unread_df.empty:
            all_df = get_eligible_jobs_from_db()
            response_text = format_jobs_message(all_df, title_suffix="All Eligible Jobs")
        else:
            response_text = format_jobs_message(unread_df, title_suffix="Unread Matching Jobs")

        send_message(token, chat_id, response_text, keyboard=get_inline_keyboard())

    # Handle inline button callbacks
    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        data = cb.get("data", "")

        if not chat_id:
            return

        # Answer callback query to stop loading spinner on button
        send_telegram_request(token, "answerCallbackQuery", {"callback_query_id": cb["id"]})

        if data == "unread_jobs":
            unread_df = get_unread_eligible_jobs(chat_id)
            msg = format_jobs_message(unread_df, title_suffix="Unread Matching Jobs")
            send_message(token, chat_id, msg, keyboard=get_inline_keyboard())

        elif data == "all_jobs":
            all_df = get_eligible_jobs_from_db()
            msg = format_jobs_message(all_df, title_suffix="All Eligible Jobs")
            send_message(token, chat_id, msg, keyboard=get_inline_keyboard())

        elif data == "mark_read":
            count = mark_all_jobs_read(chat_id)
            send_message(
                token, chat_id,
                "✅ *All current eligible jobs marked as READ!*\n\n"
                "Next time you tap '🔍 New / Unread Jobs', only newly discovered openings will appear.",
                keyboard=get_inline_keyboard()
            )

        elif data == "run_sync":
            send_message(token, chat_id, "🔄 *Executing Multi-Source Discovery Sync...* Please wait ~15 seconds.")
            try:
                from pipeline.runner import run_job_discovery_pipeline
                run_job_discovery_pipeline()
                unread_df = get_unread_eligible_jobs(chat_id)
                msg = "✅ *Sync Completed!*\n\n" + format_jobs_message(unread_df, title_suffix="Fresh Unread Jobs")
                send_message(token, chat_id, msg, keyboard=get_inline_keyboard())
            except Exception as sync_err:
                send_message(token, chat_id, f"⚠️ Sync error: {sync_err}", keyboard=get_inline_keyboard())


def run_telegram_bot_polling(token: str = None):
    token = token or get_telegram_token()
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not provided.")
        return

    print("🤖 Telegram Bot Listener Started with Prebuilt Buttons & Mark-As-Read Tracking...")
    last_update_id = 0

    while True:
        try:
            url = TELEGRAM_API_URL.format(token=token, method="getUpdates")
            params = {"offset": last_update_id + 1, "timeout": 20}
            res = requests.get(url, params=params, timeout=25)

            if res.status_code == 200:
                updates = res.json().get("result", [])
                for update in updates:
                    last_update_id = update["update_id"]
                    handle_update(token, update)

        except Exception as e:
            print(f"Error in polling loop: {e}")
            time.sleep(3)


if __name__ == "__main__":
    bot_token = get_telegram_token()
    if not bot_token:
        bot_token = input("Enter Telegram Bot Token: ").strip()
    run_telegram_bot_polling(bot_token)
