# -*- coding: utf-8 -*-
"""WC2026 daily digest — resilient mode (retry crons + dedupe via state).

  * ช่วง 23:45-23:59 ไทย -> สรุปผลของวันนี้ (ส่งครั้งเดียว)
  * ช่วง 00:01-00:21 ไทย -> โปรแกรมของวันนี้ (ส่งครั้งเดียว)
    + ถ้าสรุปผลของเมื่อวานหลุด (cron ข้ามทุกรอบ) จะส่งตามให้ด้วย
digest_state.json จำว่าวันไหนส่งอะไรไปแล้ว (committed by the workflow).
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
STATE = os.path.join(BASE, "digest_state.json")


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:100], flush=True)


def programme_lines(day):
    lines = []
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ko = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            if ko.date() == day:
                lines.append(f"🕐 {ko:%H:%M} น. | {row['round']} | {row['fixture']}")
    return lines


def result_lines(day):
    d1 = (day - timedelta(days=1)).strftime("%Y-%m-%d")
    d2 = (day + timedelta(days=1)).strftime("%Y-%m-%d")
    req = urllib.request.Request(
        f"https://api.football-data.org/v4/competitions/WC/matches?dateFrom={d1}&dateTo={d2}",
        headers={"X-Auth-Token": FD_TOKEN},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    lines = []
    for m in data.get("matches", []):
        ko = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=7)
        if ko.date() != day or m.get("status") != "FINISHED":
            continue
        ft = m.get("score", {}).get("fullTime", {})
        lines.append(
            f"✅ {th(m['homeTeam']['name'])} {ft.get('home')} - {ft.get('away')} {th(m['awayTeam']['name'])}"
        )
    return lines


def send_summary(day, late=False):
    try:
        lines = result_lines(day)
    except Exception as e:
        print("football-data error:", e, flush=True)
        return False  # อย่าจดว่าส่งแล้ว เผื่อรอบถัดไปลองใหม่
    body = "\n".join(lines) if lines else "วันนี้ไม่มีนัดที่แข่งจบ"
    tag = " (ส่งย้อนหลัง)" if late else ""
    send(f"🌙 สรุปผลบอลโลกวันที่ {day:%d/%m/%Y}{tag}\n\n{body}")
    return True


def send_programme(day):
    lines = programme_lines(day)
    body = "\n".join(lines) if lines else "วันนี้ไม่มีโปรแกรมแข่งขัน"
    send(f"📅 โปรแกรมบอลโลกวันนี้ ({day:%d/%m/%Y})\n\n{body}")
    return True


def main():
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    now = datetime.now(THAI_TZ).replace(tzinfo=None)
    today = now.date()
    changed = False

    if now.hour >= 21 and state.get("summary") != str(today):
        if send_summary(today):
            state["summary"] = str(today)
            changed = True

    if now.hour < 12:
        yday = today - timedelta(days=1)
        if state.get("summary") not in (str(yday), str(today)):
            if send_summary(yday, late=True):
                state["summary"] = str(yday)
                changed = True
        if state.get("programme") != str(today):
            if send_programme(today):
                state["programme"] = str(today)
                changed = True

    if changed:
        json.dump(state, open(STATE, "w"))
    print(f"digest done, changed={changed}, state={state}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
