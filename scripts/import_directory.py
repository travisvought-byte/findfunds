"""Turn research CSVs in seed/directory/ into data/organizers.json and data/series.json.

Usage: python3 scripts/import_directory.py

organizers_*.csv and series_*.csv use the headers described in DATA-MODEL.md.
Duplicates (same type or kind, name and city) are merged, keeping the first non-blank value per field.
"""
import csv
import json
import re
from pathlib import Path

from ffconfig import slugify

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "seed" / "directory"
ORG_TYPES = {"parish", "church", "legion", "vfw", "amvets", "elks", "eagles", "moose", "kofc", "lions", "rotary",
             "kiwanis", "fire_dept", "library", "park_district", "state_park", "chamber", "cvb", "fair_board",
             "festival_committee", "historical_society", "school", "nonprofit", "government", "other"}
KINDS = {"fair", "festival", "fish_fry", "breakfast", "benefit_dinner", "cards", "raffle", "parade", "market",
         "concert", "car_show", "run_walk", "holiday", "library_program", "park_program", "other"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME = re.compile(r"^\d{2}:\d{2}$")


def norm(text):
    text = text.lower().replace("&", "and").replace("saint ", "st ").replace("st. ", "st ")
    text = re.sub(r"\b(the|church|parish|of|inc)\b", " ", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def clean(v):
    return re.sub(r"\s+", " ", (v or "").strip())


def url(v):
    v = clean(v)
    return v if v.startswith(("https://", "http://")) and " " not in v else ""


def dates(v):
    return sorted({d.strip() for d in (v or "").split(";") if DATE.match(d.strip())})


def rows(prefix):
    for f in sorted(SEED.glob(f"{prefix}_*.csv")):
        with f.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                yield {k: clean(v) for k, v in r.items() if k}


def city_county_map():
    seen = {}
    for prefix in ("organizers", "series"):
        for r in rows(prefix):
            if r.get("city") and r.get("county"):
                seen.setdefault(r["city"].lower(), {}).setdefault(r["county"], 0)
                seen[r["city"].lower()][r["county"]] += 1
    return {c: max(v, key=v.get) for c, v in seen.items()}


def unique_slug(base, used):
    slug, n = base, 2
    while slug in used:
        slug, n = f"{base}-{n}", n + 1
    used.add(slug)
    return slug


def main():
    cc = city_county_map()
    orgs, okeys = [], {}
    used = set()
    for r in rows("organizers"):
        if r.get("state", "OH") not in ("OH", ""):
            continue
        t = r["type"] if r["type"] in ORG_TYPES else "other"
        county = r["county"] or cc.get(r["city"].lower(), "")
        key = (t, norm(r["name"]), r["city"].lower())
        rec = {"name": r["name"], "type": t, "number": r.get("number", ""), "address": r.get("address", ""),
               "city": r["city"], "county": county, "state": "OH", "zip": r.get("zip", "")[:5],
               "phone": r.get("phone", ""), "website": url(r.get("website")), "events_url": url(r.get("events_url")),
               "hosts": sorted({h.strip() for h in r.get("hosts", "").split(";") if h.strip() in KINDS}),
               "source": r.get("source", ""), "source_url": url(r.get("source_url")),
               "checked_on": r.get("checked_on", ""), "trust": "official_list"}
        if not rec["name"]:
            continue
        if key in okeys:
            old = okeys[key]
            for k, v in rec.items():
                if not old.get(k) and v:
                    old[k] = v
            old["hosts"] = sorted(set(old["hosts"]) | set(rec["hosts"]))
            continue
        rec["slug"] = unique_slug(slugify(f"{rec['name']} {rec['city']}"), used)
        okeys[key] = rec
        orgs.append(rec)
    by_name = {}
    for o in orgs:
        by_name.setdefault(norm(o["name"]), []).append(o)

    series, skeys, used = [], {}, set()
    for r in rows("series"):
        if r.get("state", "OH") not in ("OH", ""):
            continue
        kind = r["kind"] if r["kind"] in KINDS else "other"
        county = r["county"] or cc.get(r["city"].lower(), "")
        key = (kind, norm(r["name"]), r["city"].lower())
        org = None
        if r.get("organizer_name"):
            cands = by_name.get(norm(r["organizer_name"]), [])
            cands = [o for o in cands if o["city"].lower() == r["city"].lower()] or cands[:1]
            org = cands[0] if cands else None
        rec = {"name": r["name"], "kind": kind, "recurrence": r.get("recurrence", ""), "timing": r.get("timing", ""),
               "next_dates": dates(r.get("next_dates")), "last_dates": dates(r.get("last_dates")),
               "start_time": r["start_time"] if TIME.match(r.get("start_time", "")) else "",
               "end_time": r["end_time"] if TIME.match(r.get("end_time", "")) else "",
               "venue": {"name": r.get("venue_name", ""), "address": r.get("address", ""), "city": r["city"],
                         "county": county, "state": "OH", "zip": r.get("zip", "")[:5]},
               "organizer": {"name": r.get("organizer_name", ""), "type": r.get("organizer_type", ""),
                             "number": r.get("organizer_number", ""), "phone": r.get("phone", "")},
               "organizer_slug": org["slug"] if org else "",
               "website": url(r.get("website")), "cost": r.get("cost") if r.get("cost") in ("free", "paid", "varies") else "unknown",
               "source": r.get("source", ""), "source_url": url(r.get("source_url")), "checked_on": r.get("checked_on", ""),
               "trust": "organizer_page" if r.get("verified_on_organizer_site") == "yes" else "public_list"}
        if not rec["name"]:
            continue
        if key in skeys:
            old = skeys[key]
            for k, v in rec.items():
                if not old.get(k) and v:
                    old[k] = v
            continue
        rec["slug"] = unique_slug(slugify(f"{rec['name']} {rec['venue']['city']}"), used)
        skeys[key] = rec
        series.append(rec)
    orgs.sort(key=lambda o: (o["county"], o["type"], o["name"]))
    series.sort(key=lambda s: (s["kind"], s["venue"]["county"], s["name"]))
    (ROOT / "data" / "organizers.json").write_text(json.dumps(orgs, indent=1, ensure_ascii=False) + "\n")
    (ROOT / "data" / "series.json").write_text(json.dumps(series, indent=1, ensure_ascii=False) + "\n")
    print(f"organizers: {len(orgs)}, series: {len(series)}")


if __name__ == "__main__":
    main()
