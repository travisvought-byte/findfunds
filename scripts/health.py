"""Weekly data health check: flags records not rechecked in 180 days and source or website links that fail.

Usage: python3 scripts/health.py [--links N]
Writes a Markdown report to stdout. Exit code is always 0; the workflow turns the report into an issue.
"""
import argparse
import datetime as dt
import json
import random
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STALE_DAYS = 180


def load(name):
    return json.loads((ROOT / "data" / f"{name}.json").read_text())


def check_link(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "community-events-link-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as err:
        if err.code in (403, 405, 429):  # many sites refuse HEAD or bots; not a dead link
            return err.code
        return err.code
    except Exception as err:  # noqa: BLE001
        return type(err).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", type=int, default=150, help="how many links to sample this run")
    args = ap.parse_args()
    today = dt.date.today()
    series, orgs = load("series"), load("organizers")
    stale = []
    for label, recs in (("event", series), ("organizer", orgs)):
        for r in recs:
            try:
                age = (today - dt.date.fromisoformat(r["checked_on"])).days
            except ValueError:
                age = 9999
            if age > STALE_DAYS:
                stale.append((label, r["name"], r["checked_on"]))
    links = sorted({u for r in series + orgs for u in (r.get("source_url"), r.get("website"), r.get("events_url")) if u})
    rng = random.Random(today.isoformat())
    sample = rng.sample(links, min(args.links, len(links)))
    dead = []
    for u in sample:
        code = check_link(u)
        if code in (404, 410) or isinstance(code, str):
            dead.append((u, code))
    no_dates = [s["name"] for s in series if not s["next_dates"]]
    print(f"## Data health, {today.isoformat()}\n")
    print(f"- Records not rechecked in {STALE_DAYS} days: {len(stale)}")
    print(f"- Links sampled: {len(sample)} of {len(links)}; dead or unreachable: {len(dead)}")
    print(f"- Recurring events without this season's dates yet: {len(no_dates)} of {len(series)}\n")
    if dead:
        print("### Dead or unreachable links\n")
        for u, code in dead:
            print(f"- {code}: {u}")
        print()
    if stale:
        print("### Due for a recheck (oldest first, up to 50)\n")
        for label, name, when in sorted(stale, key=lambda x: x[2])[:50]:
            print(f"- {label}: {name} (checked {when})")


if __name__ == "__main__":
    main()
