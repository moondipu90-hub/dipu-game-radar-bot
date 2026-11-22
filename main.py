

import os
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"
API = "https://api.football-data.org/v4/matches"


def send(chat_id, message):
    if not BOT_TOKEN:
        return
    requests.post(
        f"{TG}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=20
    )


def get_matches():
    if not FOOTBALL_TOKEN:
        return "Football API Token সেট করা নেই।"

    today = datetime.now(timezone.utc).date().isoformat()

    try:
        response = requests.get(
            API,
            headers={"X-Auth-Token": FOOTBALL_TOKEN},
            params={"dateFrom": today, "dateTo": today},
            timeout=25
        )
        response.raise_for_status()
        matches = response.json().get("matches", [])

        if not matches:
            return "আজকের জন্য কোনো ম্যাচের তথ্য পাওয়া যায়নি।"

        lines = ["⚽ DIPU GAME RADAR\nআজকের ফুটবল ম্যাচ:\n"]

        for match in matches[:30]:
            home = match.get("homeTeam", {}).get("name", "Unknown")
            away = match.get("awayTeam", {}).get("name", "Unknown")
            status = match.get("status", "UNKNOWN")
            score = match.get("score", {}).get("fullTime", {})
            hs = score.get("home")
            aws = score.get("away")

            result = f"{hs} - {aws}" if hs is not None and aws is not None else "স্কোর পাওয়া যায়নি"

            lines.append(
                f"⚽ {home} vs {away}\n"
                f"🥅 {result}\n"
                f"📌 Status: {status}\n"
            )

        return "\n".join(lines)

    except Exception as error:
        print("Football API error:", error)
        return "ম্যাচের তথ্য আনতে সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।"


@app.route("/", methods=["GET"])
def home():
    return "Dipu Game Radar Bot is running!"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    if not BOT_TOKEN:
        return "Bot token missing", 500

    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    command = message.get("text", "").strip().lower()

    if not chat_id:
        return jsonify({"ok": True})

    if command.startswith("/start"):
        send(
            chat_id,
            "⚽ Welcome to Dipu Game Radar!\n\n"
            "আজকের ফুটবল ম্যাচ দেখতে /today লিখুন।"
        )

    elif command.startswith("/today"):
        send(chat_id, get_matches())

    return jsonify({"ok": True})


def setup_webhook():
    base_url = os.getenv("RENDER_EXTERNAL_URL")

    if BOT_TOKEN and base_url:
        try:
            response = requests.get(
                f"{TG}/setWebhook",
                params={"url": f"{base_url}/webhook"},
                timeout=20
            )
            print("Webhook setup:", response.text)
        except Exception as error:
            print("Webhook setup error:", error)


setup_webhook()
