# -*- coding: utf-8 -*-
"""WC2026 Telegram pre-match notifier.
Runs hourly via GitHub Actions. Sends a Telegram message for every match
kicking off within the next 60 minutes (Thai time, UTC+7).
"""
import csv
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
THAI_TZ = timezone(timedelta(hours=7))
WINDOW_MIN = 60

BASE = os.path.dirname(os.path.abspath(__file__))


def load_checklist():
    path = os.path.join(BASE, "checklist.txt")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        items = [line.strip() for line in f if line.strip()]
    if not items:
        return ""
    return "\n\n📋 เช็คลิสต์ก่อนบอลเตะ:\n" + "\n".join(f"☐ {i}" for i in items)


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        body = resp.read().decode()
        print("telegram response:", body[:200])


def main():
    now = datetime.now(THAI_TZ).replace(tzinfo=None)
    until = now + timedelta(minutes=WINDOW_MIN)
    checklist = load_checklist()
    sent = 0
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ko = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            if now < ko <= until:
                mins = int((ko - now).total_seconds() // 60)
                text = (
                    f"⚽ อีก {mins} นาที บอลโลกเตะ!\n\n"
                    f"🏆 {row['round']} (นัด/กลุ่ม {row['match']})\n"
                    f"🆚 {row['fixture']}\n"
                    f"🕐 {ko.strftime('%H:%M')} น. (เวลาไทย)\n"
                    f"🏟️ {row['venue']}"
                    f"{checklist}"
                )
                send(text)
                sent += 1
    print(f"checked at {now:%Y-%m-%d %H:%M} Thai, sent {sent} message(s)")


if __name__ == "__main__":
    sys.exit(main())
