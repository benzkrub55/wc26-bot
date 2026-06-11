# -*- coding: utf-8 -*-
"""English -> Thai team-name mapping for football-data.org results."""
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
