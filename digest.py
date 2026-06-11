# -*- coding: utf-8 -*-
"""WC2026 daily digest (runs 00:01, 08:00, 16:00, 23:59 Thai time).

Sends a summary of today's (Thai date) matches:
  * finished / in-play matches with live scores from football-data.org
  * upcoming matches later today (from schedule.csv, Thai names)
At the 00:01 run also sends the daily work-checklist reminder.
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FD_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
THAI_TZ = timezone(timedelta(hours=7))
BASE = os.path.dirname(os.path.abspath(__file__))

TEAM_TH = {
    "Mexico": "เม็กซิโก", "South Africa": "แอฟริกาใต้", "Korea Republic": "เกาหลีใต้",
    "South Korea": "เกาหลีใต้", "Czechia": "เช็ก", "Czech Republic": "เช็ก",
    "Canada": "แคนาดา", "Bosnia and Herzegovina": "บอสเนียฯ", "United States": "สหรัฐอเมริกา",
    "USA": "สหรัฐอเมริกา", "Paraguay": "ปารากวัย", "Qatar": "กาตาร์",
    "Switzerland": "สวิตเซอร์แลนด์", "Brazil": "บราซิล", "Morocco": "โมร็อกโก",
    "Haiti": "เฮติ", "Scotland": "สกอตแลนด์", "Australia": "ออสเตรเลีย",
    "Türkiye": "ตุรกี", "Turkey": "ตุรกี", "Germany": "เยอรมนี",
    "Curaçao": "กือราเซา", "Curacao": "กือราเซา", "Netherlands": "เนเธอร์แลนด์",
    "Japan": "ญี่ปุ่น", "Côte d'Ivoire": "ไอวอรีโคสต์", "Ivory Coast": "ไอวอรีโคสต์",
    "Ecuador": "เอกวาดอร์", "Sweden": "สวีเดน", "Tunisia": "ตูนิเซีย",
    "Spain": "สเปน", "Cape Verde": "เคปเวิร์ด", "Belgium": "เบลเยียม",
    "Egypt": "อียิปต์", "Saudi Arabia": "ซาอุดีอาระเบีย", "Uruguay": "อุรุกวัย",
    "Iran": "อิหร่าน", "New Zealand": "นิวซีแลนด์", "France": "ฝรั่งเศส",
    "Senegal": "เซเนกัล", "Iraq": "อิรัก", "Norway": "นอร์เวย์",
    "Argentina": "อาร์เจนตินา", "Algeria": "แอลจีเรีย", "Austria": "ออสเตรีย",
    "Jordan": "จอร์แดน", "Portugal": "โปรตุเกส", "DR Congo": "ดีอาร์คองโก",
    "Congo DR": "ดีอาร์คองโก", "England": "อังกฤษ", "Croatia": "โครเอเชีย",
    "Ghana": "กานา", "Panama": "ปานามา", "Uzbekistan": "อุซเบกิสถาน",
    "Colombia": "โคลอมเบีย",
}


def th(name):
    return TEAM_TH.get(name, name)


def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        print("telegram:", resp.read().decode()[:120])


def fetch_results(today):
    """Return list of result lines for matches already played today (Thai date)."""
    if not FD_TOKEN:
        return None  # no token configured
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
        if ko.date() != today:
            continue
        status = m.get("status", "")
        home, away = th(m["homeTeam"]["name"]), th(m["awayTeam"]["name"])
        ft = m.get("score", {}).get("fullTime", {})
        hs, as_ = ft.get("home"), ft.get("away")
        if status == "FINISHED":
            lines.append(f"✅ {home} {hs} - {as_} {away} (จบแล้ว)")
        elif status in ("IN_PLAY", "PAUSED"):
            hs = hs if hs is not None else 0
            as_ = as_ if as_ is not None else 0
            lines.append(f"🔴 {home} {hs} - {as_} {away} (กำลังแข่ง)")
    return lines


def main():
    now = datetime.now(THAI_TZ).replace(tzinfo=None)
    today = now.date()

    upcoming = []
    with open(os.path.join(BASE, "schedule.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ko = datetime.strptime(row["kickoff_thai"], "%Y-%m-%d %H:%M")
            if ko.date() == today and ko > now:
                upcoming.append(f"🕐 {ko:%H:%M} น. | {row['round']} | {row['fixture']}")

    try:
        results = fetch_results(today)
    except Exception as e:  # API down -> degrade gracefully
        print("football-data error:", e)
        results = None

    parts = [f"📅 สรุปบอลโลกประจำวันที่ {today:%d/%m/%Y} ({now:%H:%M} น.)"]
    parts.append("\n— ผลที่แข่งไปแล้ววันนี้ —")
    if results:
        parts.extend(results)
    elif results is None:
        parts.append("(ยังไม่ได้ตั้งค่า FOOTBALL_DATA_TOKEN — แสดงผลบอลไม่ได้)")
    else:
        parts.append("ยังไม่มีนัดที่แข่งจบวันนี้")
    parts.append("\n— โปรแกรมที่เหลือวันนี้ —")
    parts.extend(upcoming if upcoming else ["ไม่มีนัดเตะเหลือแล้ววันนี้"])
    send("\n".join(parts))

    # daily checklist reminder on the 00:01 run only
    if now.hour == 0:
        path = os.path.join(BASE, "checklist.txt")
        items = [l.strip() for l in open(path, encoding="utf-8")] if os.path.exists(path) else []
        items = [i for i in items if i]
        if items:
            send(
                "🌅 เริ่มวันใหม่! อย่าลืมงานประจำวันของทีม\n\n📋 Checklist:\n"
                + "\n".join(f"☐ {i}" for i in items)
            )
    print("digest sent")


if __name__ == "__main__":
    sys.exit(main())
