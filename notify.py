# -*- coding: utf-8 -*-
"""WC2026 pre-match notifier — resilient mode (runs every 10 min, dedupe via state).

Alerts per kickoff slot (matches at the same time are grouped):
  * T-60 : kickoff in (45, 75] minutes
  * T-5  : kickoff in (0, 22] minutes -> sleep until T-5 then send
sent_alerts.json remembers what was already sent (committed by the workflow),
so skipped cron slots are covered by later runs without duplicates.
"""
import csv
import json
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
STATE = os.path.join(BASE, "sent_alerts.json")


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:100], flush=True)


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

    sent = set(json.load(open(STATE))) if os.path.exists(STATE) else set()
    changed = False

    # --- T-60 (grouped per kickoff slot) -----------------------------------
    now = now_thai()
    for ko, group in sorted(slots.items()):
        key = f"{ko:%Y-%m-%dT%H:%M}|t60"
        delta = (ko - now).total_seconds() / 60
        if 45 < delta <= 75 and key not in sent:
            send(
                f"⏰ อีกประมาณ {int(delta)} นาที บอลโลกเตะ! ({ko:%H:%M} น. เวลาไทย)\n\n"
                f"{match_lines(group)}\n\n"
                f"📋 เตรียมงานทีมให้พร้อม!"
            )
            sent.add(key)
            changed = True

    # --- T-5 ----------------------------------------------------------------
    for ko, group in sorted(slots.items()):
        key = f"{ko:%Y-%m-%dT%H:%M}|t5"
        delta_s = (ko - now_thai()).total_seconds()
        if 0 < delta_s <= 22 * 60 and key not in sent:
            wait = delta_s - 5 * 60
            if wait > 0:
                print(f"sleeping {int(wait)}s until T-5 of {ko}", flush=True)
                time.sleep(wait)
            send(
                f"🚨 อีก 5 นาทีเตะ! ({ko:%H:%M} น.)\n\n"
                f"{match_lines(group)}\n\n"
                f"📋 เช็คงานทีมให้ครบก่อนบอลเริ่ม!"
            )
            sent.add(key)
            changed = True

    if changed:
        json.dump(sorted(sent), open(STATE, "w"))
    print(f"done, sent state has {len(sent)} record(s), changed={changed}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
