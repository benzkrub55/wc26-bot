# -*- coding: utf-8 -*-
"""WC2026 instant result notifier (runs every 15 min during match hours).

Polls football-data.org; when a match turns FINISHED and hasn't been
announced yet (tracked in sent_results.json, committed by the workflow),
sends the final score to Telegram immediately.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from teams_th import th

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FD_TOKEN = os.environ["FOOTBALL_DATA_TOKEN"]
THAI_TZ = timezone(timedelta(hours=7))
BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "sent_results.json")


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:120])


def fetch_matches():
    today = datetime.now(THAI_TZ).date()
    d1 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    req = urllib.request.Request(
        f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={d1}&dateTo={d2}",
        headers={"X-Auth-Token": FD_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("matches", [])


def result_text(m):
    home, away = th(m["homeTeam"]["name"]), th(m["awayTeam"]["name"])
    score = m.get("score", {})
    ft = score.get("fullTime", {})
    line = f"🏁 จบเกม! {home} {ft.get('home')} - {ft.get('away')} {away}"
    duration = score.get("duration", "REGULAR")
    if duration == "EXTRA_TIME":
        line += "\n(หลังต่อเวลาพิเศษ)"
    elif duration == "PENALTY_SHOOTOUT":
        pen = score.get("penalties", {})
        line += f"\n(ดวลจุดโทษ {pen.get('home')}-{pen.get('away')})"
    return line


def main():
    sent_ids = json.load(open(STATE)) if os.path.exists(STATE) else []
    new = 0
    for m in fetch_matches():
        if m.get("status") == "FINISHED" and m["id"] not in sent_ids:
            send(result_text(m))
            sent_ids.append(m["id"])
            new += 1
    if new:
        json.dump(sent_ids, open(STATE, "w"))
    print(f"announced {new} new result(s)")


if __name__ == "__main__":
    sys.exit(main())
