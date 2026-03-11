#!/usr/bin/env python3
"""
Build a beautiful single-page birthday timeline for INSEAD 26D cohort.
Primary view: timeline sorted by days until next birthday.
"""

import csv
import json
import re
from datetime import datetime, date
from pathlib import Path

CSV_PATH = Path("/Users/freddiechambers/Library/Mobile Documents/iCloud~md~obsidian/Documents/iCloud/21. PDFs/Proud to be a part of INSEAD 26D! (Dec 2025) (2).csv")
OUTPUT_PATH = Path("/Users/freddiechambers/Projects/insead-tool-repo/birthdays/index.html")


def parse_name(raw_first_name):
    name = raw_first_name.strip()
    if not name:
        return ""
    parts = name.split()
    if len(parts) >= 2 and parts[0].isupper() and not parts[1].isupper():
        first = " ".join(parts[1:])
        last = parts[0]
        return f"{first.title()} {last.title()}"
    first_parts = []
    last_parts = []
    found_upper = False
    for part in parts:
        if part.isupper() and len(part) > 1 and not found_upper:
            found_upper = True
        if found_upper and part.isupper():
            last_parts.append(part)
        elif found_upper and not part.isupper():
            last_parts.append(part)
        else:
            first_parts.append(part)
    if first_parts and last_parts:
        first = " ".join(first_parts)
        last = " ".join(last_parts)
        last_titled = title_case_surname(last)
        return f"{first} {last_titled}"
    return name.title()


def title_case_surname(surname):
    particles = {"DE", "DEL", "EL", "DI", "DA", "DAS", "DO", "DOS", "AL", "ABI", "VAN"}
    parts = surname.split()
    result = []
    for i, p in enumerate(parts):
        if p.upper() in particles and i > 0:
            result.append(p.lower())
        else:
            result.append(p.title())
    return " ".join(result)


def fix_birthday(date_str):
    if not date_str or date_str.strip() == "":
        return None
    date_str = date_str.strip()
    # Handle DD/MM/YYYY and D/M/YYYY
    try:
        parts = date_str.split("/")
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            return None
    except (ValueError, AttributeError):
        return None
    if y == 2025:
        y = 1995
    elif y == 2026:
        y = 1996
    if y < 1980 or y > 2005:
        return None
    if m < 1 or m > 12 or d < 1 or d > 31:
        return None
    try:
        return date(y, m, d)
    except ValueError:
        return None


def get_zodiac(month, day):
    zodiacs = [
        (1, 20, "Aquarius", "\u2652"),
        (2, 19, "Pisces", "\u2653"),
        (3, 21, "Aries", "\u2648"),
        (4, 20, "Taurus", "\u2649"),
        (5, 21, "Gemini", "\u264a"),
        (6, 21, "Cancer", "\u264b"),
        (7, 23, "Leo", "\u264c"),
        (8, 23, "Virgo", "\u264d"),
        (9, 23, "Libra", "\u264e"),
        (10, 23, "Scorpio", "\u264f"),
        (11, 22, "Sagittarius", "\u2650"),
        (12, 22, "Capricorn", "\u2651"),
    ]
    for i, (zm, zd, name, emoji) in enumerate(zodiacs):
        if month == zm and day < zd:
            prev = zodiacs[i - 1]
            return prev[2], prev[3]
        elif month == zm and day >= zd:
            return name, emoji
    return "Capricorn", "\u2651"


def normalize_linkedin(url):
    if not url or url.strip() == "" or url.strip().lower() == "na":
        return ""
    url = url.strip()
    url = re.sub(r'\s+be$', '', url)
    url = url.strip()
    if not url.startswith("http"):
        if url.startswith("www.") or "linkedin" in url.lower():
            url = "https://" + url
        elif url.startswith("/") or "linkedin" not in url.lower():
            url = "https://www.linkedin.com/in/" + url.lstrip("/")
        else:
            url = "https://" + url
    return url


def main():
    people = []
    seen_keys = set()

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header

        for row in reader:
            if len(row) < 36:
                row.extend([""] * (36 - len(row)))

            first_name = row[1].strip()
            campus = row[3].strip()
            email = row[11].strip() if len(row) > 11 else ""
            phone = row[13].strip() if len(row) > 13 else ""
            birthday_raw = row[25].strip() if len(row) > 25 else ""
            linkedin_raw = row[34].strip() if len(row) > 34 else ""

            if not first_name:
                continue

            dedup_key = email.lower().strip() if email else (phone.strip() if phone else first_name.strip().lower())
            if dedup_key and dedup_key in seen_keys:
                continue
            if dedup_key:
                seen_keys.add(dedup_key)

            name = parse_name(first_name)
            birthday = fix_birthday(birthday_raw)
            linkedin = normalize_linkedin(linkedin_raw)

            zodiac_name, zodiac_emoji = ("", "")
            bday_month = 0
            bday_day = 0

            if birthday:
                zodiac_name, zodiac_emoji = get_zodiac(birthday.month, birthday.day)
                bday_month = birthday.month
                bday_day = birthday.day

            people.append({
                "name": name,
                "campus": campus if campus in ("Fonty", "Singy") else "Fonty",
                "month": bday_month,
                "day": bday_day,
                "zodiac": zodiac_name,
                "zodiacEmoji": zodiac_emoji,
                "linkedin": linkedin,
            })

    print(f"Parsed {len(people)} from main CSV")

    # === ADD MISSING PEOPLE from E6 calendar + Section D class contribution analysis ===
    # These people appear in Section D / E6 study group but not in the WhatsApp contacts CSV
    # E6 birthday calendar provides birthdays; Section D analysis confirms full names
    extra_people = [
        # From E6 calendar (with birthdays)
        {"name": "Oussama Obeid",       "campus": "Fonty", "bday": (8, 24)},
        {"name": "Madeleine Kelly",     "campus": "Fonty", "bday": (11, 5)},
        {"name": "Andrew Bauer",        "campus": "Fonty", "bday": (4, 30)},
        {"name": "Chris Johnson",       "campus": "Fonty", "bday": (11, 29)},
        {"name": "Sabine Rihan",        "campus": "Fonty", "bday": (11, 1)},
        {"name": "Lars Ballhausen",     "campus": "Fonty", "bday": (4, 8)},
        {"name": "Mya Ojogwu",          "campus": "Fonty", "bday": (9, 16)},
        # From Section D analysis (no birthday data)
        {"name": "Vernes Rasidkadic",   "campus": "Fonty", "bday": None},
        {"name": "Raja Makhlouf",       "campus": "Fonty", "bday": None},
        {"name": "Eva Sinha",           "campus": "Fonty", "bday": None},
        {"name": "Francesco Danovi",    "campus": "Fonty", "bday": None},
        {"name": "Isabella Isotta",     "campus": "Fonty", "bday": None},
        {"name": "Armand Goze",         "campus": "Fonty", "bday": None},
        {"name": "Michelle Baaklini",   "campus": "Fonty", "bday": None},
        {"name": "Jozef Tanzer",        "campus": "Fonty", "bday": None},
        {"name": "Nassib Abou Nader",   "campus": "Fonty", "bday": None},
        {"name": "Jeff Neukomm",        "campus": "Fonty", "bday": None},
        {"name": "Marta Villagran Prieto", "campus": "Fonty", "bday": None},
        {"name": "Claire Maybank",      "campus": "Fonty", "bday": None},
        {"name": "Yara Bou Maachar",    "campus": "Fonty", "bday": None},
    ]

    # Dedup against existing names
    existing_names = set(p["name"].lower() for p in people)
    added = 0
    for ep in extra_people:
        if ep["name"].lower() in existing_names:
            continue
        entry = {
            "name": ep["name"],
            "campus": ep["campus"],
            "month": 0,
            "day": 0,
            "zodiac": "",
            "zodiacEmoji": "",
            "linkedin": "",
        }
        if ep["bday"]:
            m, d = ep["bday"]
            entry["month"] = m
            entry["day"] = d
            z_name, z_emoji = get_zodiac(m, d)
            entry["zodiac"] = z_name
            entry["zodiacEmoji"] = z_emoji
        people.append(entry)
        existing_names.add(ep["name"].lower())
        added += 1

    print(f"Added {added} extra people from E6 calendar + Section D analysis")
    print(f"Total: {len(people)} people ({len([p for p in people if p['month'] > 0])} with birthdays, {len([p for p in people if p['month'] == 0])} unknown)")

    people_json = json.dumps(people, ensure_ascii=False, indent=2)
    html = generate_html(people_json)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Written to {OUTPUT_PATH} ({len(html):,} bytes)")


def generate_html(people_json):
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INSEAD 26D - Birthday Calendar</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --ink: #1a1a2e;
  --ink-light: #536471;
  --ink-faint: #8899a6;
  --surface: #ffffff;
  --bg: #faf8f5;
  --card-bg: #ffffff;
  --border: #e1e8ed;
  --border-light: #eef0f2;
  --accent: #1d9bf0;
  --fonty: #1e3a5f;
  --fonty-bg: #e8eef5;
  --fonty-border: #b8cce0;
  --singy: #c2610a;
  --singy-bg: #fef3e6;
  --singy-border: #f0c896;
  --green: #00ba7c;
  --pink: #e8457a;
  --purple: #7856ff;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --transition: 0.2s ease;
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e7e9ea;
    --ink-light: #a0aab4;
    --ink-faint: #6e7a85;
    --surface: #1a1a2e;
    --bg: #0f0f1a;
    --card-bg: #1a1a2e;
    --border: #2f2f4a;
    --border-light: #252540;
    --accent: #4da6ff;
    --fonty: #7fb3e0;
    --fonty-bg: #1a2a3f;
    --fonty-border: #2d4a6a;
    --singy: #f0a050;
    --singy-bg: #2f2218;
    --singy-border: #5a3a1a;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  }
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  background: var(--bg);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  padding-bottom: 60px;
}

/* Topbar */
.topbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(250,248,245,0.92);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 0 20px;
}
@media (prefers-color-scheme: dark) {
  .topbar { background: rgba(15,15,26,0.92); }
}
.topbar-inner {
  max-width: 720px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between; height: 52px;
}
.topbar-title { font-size: 15px; font-weight: 700; }
.topbar-date { font-size: 13px; color: var(--ink-light); }

/* Hero */
.hero { text-align: center; padding: 40px 20px 24px; max-width: 720px; margin: 0 auto; }
.hero h1 {
  font-size: 28px; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 4px;
  background: linear-gradient(135deg, var(--fonty), var(--singy));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero p { font-size: 14px; color: var(--ink-light); }

/* Controls */
.controls {
  max-width: 720px; margin: 0 auto 20px; padding: 0 20px;
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
}
.search-box {
  flex: 1; min-width: 160px; padding: 9px 14px;
  border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 14px; background: var(--card-bg); color: var(--ink); outline: none;
}
.search-box:focus { border-color: var(--accent); }
.filter-btn {
  padding: 7px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 13px; font-weight: 600; background: var(--card-bg); color: var(--ink-light);
  cursor: pointer; transition: all var(--transition);
}
.filter-btn:hover { border-color: var(--ink-faint); color: var(--ink); }
.filter-btn.active { background: var(--ink); color: var(--card-bg); border-color: var(--ink); }
@media (prefers-color-scheme: dark) {
  .filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
}

/* Tab bar */
.tabs {
  max-width: 720px; margin: 0 auto 20px; padding: 0 20px;
  display: flex; gap: 0; border-bottom: 2px solid var(--border);
}
.tab {
  padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer;
  color: var(--ink-faint); border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: all var(--transition); background: none; border-top: none; border-left: none; border-right: none;
}
.tab:hover { color: var(--ink); }
.tab.active { color: var(--ink); border-bottom-color: var(--accent); }

/* Timeline container */
.timeline { max-width: 720px; margin: 0 auto; padding: 0 20px; }

/* Timeline row */
.tl-row {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; margin-bottom: 6px;
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
  transition: all var(--transition); cursor: default;
}
.tl-row:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.tl-row.is-today {
  border-color: var(--pink);
  background: linear-gradient(135deg, #fff5f7, #fff);
}
@media (prefers-color-scheme: dark) {
  .tl-row.is-today { background: linear-gradient(135deg, #2a1a22, var(--card-bg)); }
}

/* Days badge */
.tl-days {
  min-width: 56px; text-align: center;
  padding: 6px 4px; border-radius: var(--radius-sm);
  font-weight: 800; font-size: 13px; line-height: 1.2;
  flex-shrink: 0;
}
.tl-days .num { font-size: 20px; display: block; }
.tl-days .label { font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.7; }
.tl-days.today { background: var(--pink); color: #fff; }
.tl-days.soon { background: #fff0f5; color: var(--pink); }
@media (prefers-color-scheme: dark) { .tl-days.soon { background: #2a1a22; } }
.tl-days.mid { background: var(--fonty-bg); color: var(--fonty); }
.tl-days.far { background: var(--border-light); color: var(--ink-faint); }

/* Progress bar */
.tl-bar-wrap {
  flex: 1; min-width: 0;
}
.tl-name-row {
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}
.tl-name { font-size: 14px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tl-linkedin {
  color: var(--ink-faint); text-decoration: none; flex-shrink: 0;
  opacity: 0.5; transition: opacity var(--transition);
}
.tl-linkedin:hover { opacity: 1; color: var(--accent); }
.tl-meta {
  display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--ink-light);
}
.tl-date { font-weight: 600; }
.tl-bar {
  height: 4px; background: var(--border-light); border-radius: 2px;
  margin-top: 6px; overflow: hidden;
}
.tl-bar-fill {
  height: 100%; border-radius: 2px; transition: width 0.6s ease;
}

/* Campus badge */
.campus { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.04em; }
.campus-fonty { background: var(--fonty-bg); color: var(--fonty); border: 1px solid var(--fonty-border); }
.campus-singy { background: var(--singy-bg); color: var(--singy); border: 1px solid var(--singy-border); }

/* Section headers in timeline */
.tl-section-header {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--ink-faint); padding: 16px 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.tl-section-header::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}

/* Stats section */
.stats { max-width: 720px; margin: 0 auto; padding: 0 20px; }
.stats-title {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.1em; color: var(--ink-faint); padding: 16px 0 12px;
  display: flex; align-items: center; gap: 8px;
}
.stats-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-card {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 14px 16px; box-shadow: var(--shadow-sm);
}
.stat-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-faint); margin-bottom: 4px; }
.stat-value { font-size: 22px; font-weight: 800; line-height: 1.1; }
.stat-sub { font-size: 11px; color: var(--ink-light); margin-top: 2px; }
.stats-wide {
  background: var(--card-bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 16px 18px; box-shadow: var(--shadow-sm);
  margin-bottom: 10px;
}
.stats-wide h3 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--ink-faint); margin-bottom: 10px; }

/* Bar chart rows */
.zbar { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.zbar-label { font-size: 11px; width: 80px; text-align: right; color: var(--ink-light); white-space: nowrap; overflow: hidden; }
.zbar-track { flex: 1; height: 16px; background: var(--border-light); border-radius: 3px; overflow: hidden; }
.zbar-fill { height: 100%; border-radius: 3px; min-width: 2px; }
.zbar-val { font-size: 10px; font-weight: 700; width: 20px; color: var(--ink-faint); }

/* Heatmap */
.heat { display: grid; grid-template-columns: auto repeat(12, 1fr); gap: 3px; font-size: 10px; }
.heat-hdr { font-weight: 700; text-align: center; color: var(--ink-faint); padding: 3px 1px; }
.heat-lbl { font-weight: 600; padding: 3px 6px 3px 0; text-align: right; white-space: nowrap; }
.heat-cell { border-radius: 3px; text-align: center; padding: 4px 1px; font-weight: 600; }

/* Twins */
.twins-row { padding: 5px 0; border-bottom: 1px solid var(--border-light); font-size: 12px; }
.twins-row:last-child { border-bottom: none; }
.twins-date { font-weight: 700; color: var(--accent); }

/* Mystery */
.mystery { max-width: 720px; margin: 20px auto; padding: 0 20px; }
.mystery-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-faint); padding: 0 0 10px; display: flex; align-items: center; gap: 8px; }
.mystery-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.mystery-grid { display: flex; flex-wrap: wrap; gap: 6px; }
.mystery-chip {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 5px 10px; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 5px;
}
.mystery-chip a { color: var(--ink-faint); text-decoration: none; }
.mystery-chip a:hover { color: var(--accent); }

/* Footer */
.footer {
  text-align: center; padding: 24px 20px; font-size: 11px; color: var(--ink-faint);
  max-width: 720px; margin: 0 auto;
}

/* Empty state */
.empty { text-align: center; padding: 40px 20px; color: var(--ink-faint); font-size: 14px; }

/* Responsive */
@media (max-width: 600px) {
  .hero h1 { font-size: 22px; }
  .stats-grid { grid-template-columns: 1fr; }
  .controls { flex-direction: column; }
  .search-box { width: 100%; }
  .tl-row { padding: 10px 12px; gap: 10px; }
  .tl-days { min-width: 48px; }
  .tl-days .num { font-size: 17px; }
}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-inner">
    <span class="topbar-title">26D Birthdays</span>
    <span class="topbar-date" id="topbar-date"></span>
  </div>
</div>

<div class="hero">
  <h1>INSEAD 26D Birthday Calendar</h1>
  <p id="hero-sub">Loading...</p>
</div>

<div class="controls">
  <input type="text" class="search-box" id="search-input" placeholder="Search by name...">
  <button class="filter-btn active" data-campus="all" onclick="setCampus('all')">All</button>
  <button class="filter-btn" data-campus="Fonty" onclick="setCampus('Fonty')">Fonty</button>
  <button class="filter-btn" data-campus="Singy" onclick="setCampus('Singy')">Singy</button>
</div>

<div class="tabs">
  <button class="tab active" onclick="setView('timeline')">Timeline</button>
  <button class="tab" onclick="setView('stats')">Stats</button>
</div>

<div id="timeline-view">
  <div class="timeline" id="timeline-container"></div>
  <div class="mystery" id="mystery-container"></div>
</div>

<div id="stats-view" style="display:none">
  <div class="stats" id="stats-container"></div>
</div>

<div class="footer">Made for the INSEAD 26D cohort</div>

<script>
const PEOPLE = """ + people_json + """;

const MN = ['','January','February','March','April','May','June','July','August','September','October','November','December'];
const MS = ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const ZC = {
  Aries:'#ef4444',Taurus:'#22c55e',Gemini:'#eab308',Cancer:'#94a3b8',
  Leo:'#f97316',Virgo:'#84cc16',Libra:'#ec4899',Scorpio:'#8b5cf6',
  Sagittarius:'#f43f5e',Capricorn:'#6366f1',Aquarius:'#06b6d4',Pisces:'#14b8a6'
};
const LI = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>';

let currentCampus = 'all';
let currentSearch = '';
let currentView = 'timeline';

const today = new Date();
today.setHours(0,0,0,0);

document.getElementById('topbar-date').textContent = today.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });

const known = PEOPLE.filter(p => p.month > 0);
const unknown = PEOPLE.filter(p => p.month === 0);

// Add daysUntil to each person
function calcDaysUntil(m, d) {
  const yr = today.getFullYear();
  let next = new Date(yr, m - 1, d);
  next.setHours(0,0,0,0);
  if (next < today) next = new Date(yr + 1, m - 1, d);
  return Math.round((next - today) / 86400000);
}

known.forEach(p => { p.daysUntil = calcDaysUntil(p.month, p.day); });
known.sort((a, b) => a.daysUntil - b.daysUntil);

// Hero subtitle
const todayBdays = known.filter(p => p.daysUntil === 0);
const nextUp = known.find(p => p.daysUntil > 0);
if (todayBdays.length > 0) {
  document.getElementById('hero-sub').innerHTML = '\\u{1F389} Happy Birthday ' + todayBdays.map(p => '<b>' + p.name + '</b>').join(', ') + '!';
} else if (nextUp) {
  const w = nextUp.daysUntil === 1 ? 'tomorrow' : 'in ' + nextUp.daysUntil + ' days';
  document.getElementById('hero-sub').innerHTML = 'Next up: <b>' + nextUp.name + '</b> ' + nextUp.zodiacEmoji + ' - ' + nextUp.day + ' ' + MS[nextUp.month] + ' (' + w + ')';
} else {
  document.getElementById('hero-sub').textContent = known.length + ' birthdays tracked';
}

function daysClass(d) {
  if (d === 0) return 'today';
  if (d <= 7) return 'soon';
  if (d <= 60) return 'mid';
  return 'far';
}

function barColor(d) {
  if (d === 0) return 'var(--pink)';
  if (d <= 7) return 'var(--pink)';
  if (d <= 30) return 'var(--accent)';
  if (d <= 90) return 'var(--fonty)';
  return 'var(--border)';
}

function sectionLabel(d) {
  if (d === 0) return '\\u{1F382} Today';
  if (d <= 7) return '\\u{1F4C5} This week';
  if (d <= 30) return '\\u{1F31F} This month';
  if (d <= 90) return '\\u{23F3} Coming up';
  if (d <= 180) return '\\u{1F4C6} Later this year';
  return '\\u{1F52E} Way out';
}

function renderTimeline() {
  const container = document.getElementById('timeline-container');
  const filtered = known.filter(p => {
    if (currentCampus !== 'all' && p.campus !== currentCampus) return false;
    if (currentSearch && !p.name.toLowerCase().includes(currentSearch.toLowerCase())) return false;
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty">No birthdays match your search</div>';
    return;
  }

  // Sort by daysUntil
  filtered.sort((a, b) => a.daysUntil - b.daysUntil);

  let html = '';
  let lastSection = '';

  filtered.forEach(p => {
    const section = sectionLabel(p.daysUntil);
    if (section !== lastSection) {
      html += '<div class="tl-section-header">' + section + '</div>';
      lastSection = section;
    }

    const dc = daysClass(p.daysUntil);
    const barPct = Math.max(2, 100 - (p.daysUntil / 365 * 100));
    const daysText = p.daysUntil === 0 ? 'Today!' : p.daysUntil === 1 ? 'Tomorrow' : p.daysUntil + ' days';
    const linkedinHtml = p.linkedin ? '<a href="' + p.linkedin + '" target="_blank" rel="noopener" class="tl-linkedin" title="LinkedIn">' + LI + '</a>' : '';
    const todayRow = p.daysUntil === 0 ? ' is-today' : '';

    html += '<div class="tl-row' + todayRow + '">' +
      '<div class="tl-days ' + dc + '">' +
        '<span class="num">' + (p.daysUntil === 0 ? '\\u{1F389}' : p.daysUntil) + '</span>' +
        '<span class="label">' + (p.daysUntil === 0 ? 'today' : 'days') + '</span>' +
      '</div>' +
      '<div class="tl-bar-wrap">' +
        '<div class="tl-name-row">' +
          '<span class="tl-name">' + p.name + '</span>' +
          linkedinHtml +
        '</div>' +
        '<div class="tl-meta">' +
          '<span class="tl-date">' + p.day + ' ' + MS[p.month] + '</span>' +
          '<span class="campus campus-' + p.campus.toLowerCase() + '">' + p.campus + '</span>' +
          '<span>' + p.zodiacEmoji + ' ' + p.zodiac + '</span>' +
        '</div>' +
        '<div class="tl-bar"><div class="tl-bar-fill" style="width:' + barPct + '%;background:' + barColor(p.daysUntil) + '"></div></div>' +
      '</div>' +
    '</div>';
  });

  container.innerHTML = html;
}

function renderMystery() {
  const container = document.getElementById('mystery-container');
  const filtered = unknown.filter(p => {
    if (currentCampus !== 'all' && p.campus !== currentCampus) return false;
    if (currentSearch && !p.name.toLowerCase().includes(currentSearch.toLowerCase())) return false;
    return true;
  });
  if (filtered.length === 0) { container.innerHTML = ''; return; }
  let html = '<div class="mystery-title">\\u{1F52E} Unknown birthdays (' + filtered.length + ')</div><div class="mystery-grid">';
  filtered.forEach(p => {
    const li = p.linkedin ? '<a href="' + p.linkedin + '" target="_blank" rel="noopener">' + LI + '</a>' : '';
    html += '<div class="mystery-chip"><span class="campus campus-' + p.campus.toLowerCase() + '">' + p.campus + '</span>' + p.name + li + '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderStats() {
  const container = document.getElementById('stats-container');
  const zodiacCounts = {};
  const monthCounts = Array(13).fill(0);
  const fontyCounts = Array(13).fill(0);
  const singyCounts = Array(13).fill(0);
  const dateMap = {};

  known.forEach(p => {
    zodiacCounts[p.zodiac] = (zodiacCounts[p.zodiac] || 0) + 1;
    monthCounts[p.month]++;
    if (p.campus === 'Fonty') fontyCounts[p.month]++;
    else singyCounts[p.month]++;
    const key = p.day + '/' + p.month;
    if (!dateMap[key]) dateMap[key] = [];
    dateMap[key].push(p.name);
  });

  let busiestMonth = 1;
  for (let i = 1; i <= 12; i++) { if (monthCounts[i] > monthCounts[busiestMonth]) busiestMonth = i; }
  const topZ = Object.entries(zodiacCounts).sort((a,b) => b[1] - a[1])[0];
  const twins = Object.entries(dateMap).filter(([k,v]) => v.length > 1).sort((a,b) => {
    const [ad,am] = a[0].split('/').map(Number);
    const [bd,bm] = b[0].split('/').map(Number);
    return am - bm || ad - bd;
  });

  // Zodiac bar chart
  const zodiacOrder = ['Capricorn','Aquarius','Pisces','Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius'];
  const ze = {Aries:'\\u2648',Taurus:'\\u2649',Gemini:'\\u264a',Cancer:'\\u264b',Leo:'\\u264c',Virgo:'\\u264d',Libra:'\\u264e',Scorpio:'\\u264f',Sagittarius:'\\u2650',Capricorn:'\\u2651',Aquarius:'\\u2652',Pisces:'\\u2653'};
  const maxZ = Math.max(...Object.values(zodiacCounts));

  let zbars = zodiacOrder.map(z => {
    const c = zodiacCounts[z] || 0;
    const pct = maxZ > 0 ? (c / maxZ * 100) : 0;
    return '<div class="zbar"><span class="zbar-label">' + ze[z] + ' ' + z + '</span><div class="zbar-track"><div class="zbar-fill" style="width:' + pct + '%;background:' + (ZC[z]||'#888') + '"></div></div><span class="zbar-val">' + c + '</span></div>';
  }).join('');

  // Heatmap
  const maxH = Math.max(...fontyCounts.slice(1), ...singyCounts.slice(1), 1);
  function hc(v, isF) {
    if (v === 0) return 'background:var(--border-light);color:var(--ink-faint)';
    const i = Math.min(v / maxH, 1);
    const a = 0.15 + i * 0.65;
    if (isF) return 'background:rgba(30,58,95,' + a + ');color:' + (i > 0.4 ? '#fff' : 'var(--fonty)');
    return 'background:rgba(194,97,10,' + a + ');color:' + (i > 0.4 ? '#fff' : 'var(--singy)');
  }
  let hm = '<div class="heat"><div></div>';
  for (let m=1;m<=12;m++) hm += '<div class="heat-hdr">' + MS[m] + '</div>';
  hm += '<div class="heat-lbl">Fonty</div>';
  for (let m=1;m<=12;m++) hm += '<div class="heat-cell" style="' + hc(fontyCounts[m],true) + '">' + fontyCounts[m] + '</div>';
  hm += '<div class="heat-lbl">Singy</div>';
  for (let m=1;m<=12;m++) hm += '<div class="heat-cell" style="' + hc(singyCounts[m],false) + '">' + singyCounts[m] + '</div>';
  hm += '</div>';

  // Twins
  let tw = '';
  if (twins.length > 0) {
    tw = twins.map(([dt, names]) => {
      const [d,m] = dt.split('/').map(Number);
      return '<div class="twins-row"><span class="twins-date">' + d + ' ' + MS[m] + '</span> - ' + names.join(', ') + '</div>';
    }).join('');
  } else {
    tw = '<div style="color:var(--ink-faint);font-size:12px">No birthday twins found</div>';
  }

  container.innerHTML =
    '<div class="stats-title">Quick stats</div>' +
    '<div class="stats-grid">' +
      '<div class="stat-card"><div class="stat-label">Busiest month</div><div class="stat-value">' + MS[busiestMonth] + '</div><div class="stat-sub">' + monthCounts[busiestMonth] + ' birthdays</div></div>' +
      '<div class="stat-card"><div class="stat-label">Top sign</div><div class="stat-value">' + (topZ ? topZ[0] : '-') + '</div><div class="stat-sub">' + (topZ ? topZ[1] + ' people' : '') + '</div></div>' +
      '<div class="stat-card"><div class="stat-label">Cohort</div><div class="stat-value">' + PEOPLE.length + '</div><div class="stat-sub">' + known.length + ' known, ' + unknown.length + ' unknown</div></div>' +
    '</div>' +
    '<div class="stats-wide"><h3>Zodiac distribution</h3>' + zbars + '</div>' +
    '<div class="stats-wide"><h3>Campus heatmap by month</h3>' + hm + '</div>' +
    '<div class="stats-wide"><h3>Birthday twins \\u{1F46F}</h3>' + tw + '</div>';
}

// Controls
function setCampus(c) {
  currentCampus = c;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.campus === c));
  renderTimeline();
  renderMystery();
}

function setView(v) {
  currentView = v;
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.textContent.toLowerCase() === v));
  document.getElementById('timeline-view').style.display = v === 'timeline' ? '' : 'none';
  document.getElementById('stats-view').style.display = v === 'stats' ? '' : 'none';
  if (v === 'stats') renderStats();
}

document.getElementById('search-input').addEventListener('input', function() {
  currentSearch = this.value;
  renderTimeline();
  renderMystery();
});

// Init
renderTimeline();
renderMystery();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
