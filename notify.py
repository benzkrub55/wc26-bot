# -*- coding: utf-8 -*-
"""WC2026 pre-match notifier (runs at :25 and :55 via GitHub Actions).

Two alerts per kickoff slot (matches at the same time are grouped):
  * T-60 min : kickoff in (50, 65] minutes
  * T-5  min : kickoff in (0, 10] minutes -> sleep until T-5 then send
Both alerts include the team checklist.
"""
import csv
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
THAI_TZ = timezone(timedelta(hours=7))
BASE = os.path.dirname(os.path.abspath(__file__))


def checklist_block():
    path = os.path.join(BASE, "checklist.txt")
    if not os.path.exists(path):
        return ""
    items = [l.strip() for l in open(path, encoding="utf-8") if l.strip()]
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


def match_lines(group):
    return "\n".join(
        f"🆚 {m['fixture']} ({m['round']}) — 🏟️ {m['venue']}" for m in group
    )


def main():
    slots = defaultdict(list)
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ko = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            slots[ko].append(row)

    now = now_thai()
    sent = 0

    # --- T-60 (grouped per kickoff slot) -----------------------------------
    for ko, group in sorted(slots.items()):
        delta = (ko - now).total_seconds() / 60
        if 50 < delta <= 65:
            send(
                f"⏰ อีกประมาณ {int(delta)} นาที บอลโลกเตะ! ({ko:%H:%M} น. เวลาไทย)\n\n"
                f"{match_lines(group)}"
                f"{checklist_block()}"
            )
            sent += 1

    # --- T-5 ----------------------------------------------------------------
    for ko, group in sorted(slots.items()):
        delta_s = (ko - now_thai()).total_seconds()
        if 0 < delta_s <= 10 * 60:
            wait = delta_s - 5 * 60
            if wait > 0:
                print(f"sleeping {int(wait)}s until T-5 of {ko}")
                time.sleep(wait)
            send(
                f"🚨 อีก 5 นาทีเตะ! ({ko:%H:%M} น.)\n\n"
                f"{match_lines(group)}\n\n"
                f"เช็คให้ครบก่อนบอลเริ่ม 👇"
                f"{checklist_block()}"
            )
            sent += 1

    print(f"run at {now:%Y-%m-%d %H:%M} Thai, sent {sent} message(s)")


if __name__ == "__main__":
    sys.exit(main())
