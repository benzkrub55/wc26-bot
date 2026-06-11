# -*- coding: utf-8 -*-
"""WC2026 pre-match notifier (runs at :29 and :59 via GitHub Actions).

Two alerts per match:
  * T-60 min  : kickoff in (35, 65] minutes  -> full alert + work checklist
  * T-1  min  : kickoff in (0, 10] minutes   -> sleep until T-60s, send final reminder
"""
import csv
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
THAI_TZ = timezone(timedelta(hours=7))
BASE = os.path.dirname(os.path.abspath(__file__))


def load_checklist():
    path = os.path.join(BASE, "checklist.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def checklist_block():
    items = load_checklist()
    if not items:
        return ""
    return "\n\n📋 Checklist ทีมงาน:\n" + "\n".join(f"☐ {i}" for i in items)


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:120])


def now_thai():
    return datetime.now(THAI_TZ).replace(tzinfo=None)


def main():
    matches = []
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["ko"] = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            matches.append(row)

    now = now_thai()
    sent = 0

    # --- T-60 alerts -------------------------------------------------------
    for m in matches:
        delta = (m["ko"] - now).total_seconds() / 60
        if 35 < delta <= 65:
            send(
                f"⏰ อีกประมาณ {int(delta)} นาที บอลโลกเตะ!\n\n"
                f"🏆 {m['round']} (นัด/กลุ่ม {m['match']})\n"
                f"🆚 {m['fixture']}\n"
                f"🕐 {m['ko'].strftime('%H:%M')} น. (เวลาไทย)\n"
                f"🏟️ {m['venue']}"
                f"{checklist_block()}"
            )
            sent += 1

    # --- T-1 final reminders ----------------------------------------------
    for m in matches:
        delta_s = (m["ko"] - now_thai()).total_seconds()
        if 0 < delta_s <= 10 * 60:
            wait = delta_s - 60
            if wait > 0:
                print(f"sleeping {int(wait)}s until T-1 of {m['fixture']}")
                time.sleep(wait)
            send(
                f"🚨 1 นาทีสุดท้าย! {m['fixture']} กำลังจะเตะ\n"
                f"เช็คให้ครบก่อนบอลเริ่ม 👇"
                f"{checklist_block()}"
            )
            sent += 1

    print(f"run at {now:%Y-%m-%d %H:%M} Thai, sent {sent} message(s)")


if __name__ == "__main__":
    sys.exit(main())
