# -*- coding: utf-8 -*-
"""WC2026 daily digest.

  * 00:01 Thai -> today's match programme (from schedule.csv)
  * 23:59 Thai -> summary of today's results (football-data.org)
The mode is chosen from the current Thai hour (morning = programme).
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from teams_th import th

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FD_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
THAI_TZ = timezone(timedelta(hours=7))
BASE = os.path.dirname(os.path.abspath(__file__))


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:120])


def programme(today):
    lines = []
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ko = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            if ko.date() == today:
                lines.append(f"🕐 {ko:%H:%M} น. | {row['round']} | {row['fixture']}")
    return lines


def results(today):
    d1 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    req = urllib.request.Request(
        f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={d1}&dateTo={d2}",
        headers={"X-Auth-Token": FD_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    lines = []
    for m in data.get("matches", []):
        ko = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=7)
        if ko.date() != today or m.get("status") != "FINISHED":
            continue
        ft = m.get("score", {}).get("fullTime", {})
        lines.append(
            f"✅ {th(m['homeTeam']['name'])} {ft.get('home')} - {ft.get('away')} {th(m['awayTeam']['name'])}"
        )
    return lines


def main():
    now = datetime.now(THAI_TZ).replace(tzinfo=None)
    today = now.date()
    if now.hour < 12:  # 00:01 run -> today's programme
        lines = programme(today)
        body = "\n".join(lines) if lines else "วันนี้ไม่มีโปรแกรมแข่งขัน"
        send(f"📅 โปรแกรมบอลโลกวันนี้ ({today:%d/%m/%Y})\n\n{body}")
    else:  # 23:59 run -> today's results
        try:
            lines = results(today)
        except Exception as e:
            print("football-data error:", e)
            lines = None
        if lines is None:
            body = "(ดึงผลไม่สำเร็จ ลองเช็คใน FIFA app)"
        elif lines:
            body = "\n".join(lines)
        else:
            body = "วันนี้ไม่มีนัดที่แข่งจบ"
        send(f"🌙 สรุปผลบอลโลกวันนี้ ({today:%d/%m/%Y})\n\n{body}")
    print("digest sent")


if __name__ == "__main__":
    sys.exit(main())
