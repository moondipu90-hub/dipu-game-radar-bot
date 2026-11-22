
import os
import time
import requests
from datetime import datetime, timezone

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

TG = f"https://api.telegram.org/bot{BOT_TOKEN}"
API = "https://api.football-data.org/v4/matches"

subscribers = set()
last_update_id = 0
last_report = 0

def send(chat_id, message):
    requests.post(
        f"{TG}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=30
    )

def get_matches():
    if not FOOTBALL_TOKEN:
        return "Football API key এখনো সেট করা হয়নি।"

    today = datetime.now(timezone.utc).date().isoformat()

    response = requests.get(
        API,
        headers={"X-Auth-Token": FOOTBALL_TOKEN},
        params={"dateFrom": today, "dateTo": today},
        timeout=30
    )
    response.raise_for_status()

    matches = response.json().get("matches", [])

    if not matches:
        return "আজকের জন্য কোনো ম্যাচের তথ্য পাওয়া যায়নি।"

    lines = ["⚽ DIPU GAME RADAR\nআজকের ফুটবল আপডেট:\n"]

    for match in matches[:30]:
        home = match["homeTeam"].get("name", "Unknown")
        away = match["awayTeam"].get("name", "Unknown")
        status = match.get("status", "UNKNOWN")

        score = match.get("score", {}).get("fullTime", {})
        home_score = score.get("home")
        away_score = score.get("away")

        if home_score is not None and away_score is not None:
            result = f"{home_score} - {away_score}"
        else:
            result = "এখনো স্কোর নেই"

        lines.append(
            f"🏟 {home} vs {away}\n"
            f"📊 {result}\n"
            f"📌 Status: {status}\n"
        )

    return "\n".join(lines)

def main():
    global last_update_id, last_report

    print("Dipu Game Radar Bot is running...")

    while True:
        try:
            updates = requests.get(
                f"{TG}/getUpdates",
                params={
                    "offset": last_update_id + 1,
                    "timeout": 30
                },
                timeout=35
            ).json()

            for update in updates.get("result", []):
                last_update_id = update["update_id"]

                msg = update.get("message", {})
                chat = msg.get("chat", {})
                chat_id = chat.get("id")
                command = msg.get("text", "")

                if not chat_id:
                    continue

                if command.startswith("/start"):
                    subscribers.add(chat_id)
                    send(
                        chat_id,
                        "⚽ Welcome to Dipu Game Radar!\n\n"
                        "প্রতি ৩০ মিনিটে ফুটবল আপডেট পাবে।\n"
                        "/today লিখে আজকের ম্যাচ দেখো।"
                    )

                elif command.startswith("/today"):
                    subscribers.add(chat_id)
                    send(chat_id, get_matches())

            if time.time() - last_report >= 1800:
                if subscribers:
                    report = get_matches()
                    for chat_id in list(subscribers):
                        send(chat_id, report)

                last_report = time.time()

        except Exception as error:
            print("Error:", error)
            time.sleep(10)

if __name__ == "__main__":
    main()
