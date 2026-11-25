"""Turn a seed CSV of fish fries (from a public list) into records in data/events.json.

Usage: python3 scripts/import_seed.py seed/diocese-of-cleveland-2026.csv

Records already in data/events.json with the same id are replaced; others are kept.
Seeded records carry trust "public_list": they come from someone else's list and are
shown with "call to confirm" until the organizer confirms them.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "data" / "events.json"
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


def slugify(text):
    text = text.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def parse_dates(text, year):
    out = []
    for month, day in re.findall(r"([A-Za-z]+)\s+(\d{1,2})", text):
        m = MONTHS.get(month.lower())
        if m:
            out.append(f"{year}-{m:02d}-{int(day):02d}")
    return sorted(set(out))


def to_24h(clock, default_pm=True):
    clock = clock.strip().lower().replace(".", "")
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", clock)
    if not m:
        return ""
    h, mins, ampm = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ampm == "pm" and h < 12:
        h += 12
    elif ampm is None and default_pm and h < 12:
        h += 12
    return f"{h:02d}:{mins:02d}"


def parse_times(text):
    text = text.strip()
    if not text:
        return "", ""
    parts = re.split(r"\s*(?:until|to|-|–)\s*", text.lower().replace("p.m.", "pm").replace("a.m.", "am"), maxsplit=1)
    if len(parts) != 2:
        return "", ""
    return to_24h(parts[0]), to_24h(parts[1])


def host_kind(name):
    n = name.lower()
    if "knights of columbus" in n:
        return "fraternal"
    if "school" in n:
        return "school"
    if any(w in n for w in ("parish", "church", "shrine", "st.", "ss.", "friars")):
        return "parish"
    return "other"


def main(path):
    year = None
    records = {r["id"]: r for r in json.loads(EVENTS.read_text())} if EVENTS.exists() else {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            year = re.search(r"(\d{4})", row["season"]).group(1)
            raw = row["host"].strip()
            # "St. Mary Parish - Painesville" -> name "St. Mary Parish", place "Painesville"
            name = re.sub(r"\s+-\s+[^-]+$", "", raw).strip() if " - " in raw else raw
            name = re.sub(r"\s+-\s+.*$", "", name) if name.count(" - ") else name
            city = row["city"].strip().rstrip(",").replace("Hts.", "Heights").replace("Hts", "Heights")
            start, end = parse_times(row["times_2026"])
            slug = slugify(f"{name} {city} fish fry")
            rec = {
                "id": f"{slug}-{year}",
                "slug": slug,
                "name": f"{name} Fish Fry",
                "type": "fish_fry",
                "host": {"name": name, "kind": host_kind(name), "phone": row["phone"].strip(), "website": ""},
                "beneficiary": "",
                "venue": {"name": name, "address": row["address"].strip(), "city": city, "state": "OH",
                          "zip": row["zip"].strip(), "county": row["county"].strip()},
                "season": row["season"].strip(),
                "dates": parse_dates(row["dates_2026"], year),
                "start_time": start,
                "end_time": end,
                "price": "",
                "service": [],
                "menu": "",
                "give_link": "",
                "raffle": False,
                "accessibility": {},
                "status": "scheduled",
                "trust": "public_list",
                "source": row["source"].strip(),
                "source_url": row["source_url"].strip(),
                "reviewed_on": row["reviewed_on"].strip(),
            }
            records[rec["id"]] = rec
    out = sorted(records.values(), key=lambda r: (r["venue"]["county"], r["name"]))
    EVENTS.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} records")


if __name__ == "__main__":
    main(sys.argv[1])
