"""Checks for data/events.json and the built site in docs/. Exit code 1 on any problem.

Usage: python3 scripts/check.py
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ffconfig import TYPES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
problems = []


def bad(msg):
    problems.append(msg)


# ---- data ----
events = json.loads((ROOT / "data" / "events.json").read_text())
seen = set()
for r in events:
    where = r.get("slug", "?")
    for key in ("id", "slug", "name", "type", "host", "venue", "season", "dates", "trust", "source", "source_url", "reviewed_on"):
        if not r.get(key):
            bad(f"{where}: missing {key}")
    if r.get("slug") in seen:
        bad(f"{where}: duplicate slug")
    seen.add(r.get("slug"))
    if r.get("type") not in TYPES:
        bad(f"{where}: unknown type {r.get('type')}")
    if r.get("trust") not in ("public_list", "organizer", "claimed"):
        bad(f"{where}: unknown trust level")
    for d in r.get("dates", []):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            bad(f"{where}: bad date {d}")
    for t in ("start_time", "end_time"):
        if r.get(t) and not re.fullmatch(r"\d{2}:\d{2}", r[t]):
            bad(f"{where}: bad {t}")
    if r.get("raffle") and r.get("give_link") and re.search(r"raffle|ticket|50-?50", r["give_link"], re.I):
        bad(f"{where}: raffle listing links to what looks like online ticket sales (in person only in Ohio)")
    if r["venue"].get("state") != "OH":
        bad(f"{where}: venue state is not OH")


# ---- pages ----
class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.dupes, self.h1, self.links, self.labels_for, self.inputs = set(), [], 0, [], set(), []
        self.lang = None
        self.has_main = self.has_skip = self.has_title = False
        self.ld = []
        self._in_ld = False
        self.svgs_missing_label = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            if a["id"] in self.ids:
                self.dupes.append(a["id"])
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self.has_title = True
        if tag == "a":
            if a.get("class") == "skip":
                self.has_skip = True
            self.links.append(a.get("href"))
        if tag in ("link", "script") and (a.get("href") or a.get("src")):
            self.links.append(a.get("href") or a.get("src"))
        if tag == "label" and a.get("for"):
            self.labels_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") != "checkbox":
            self.inputs.append(a.get("id"))
        if tag == "svg" and a.get("aria-hidden") != "true" and "aria-label" not in a and a.get("xmlns") is None:
            self.svgs_missing_label += 1
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True

    def handle_data(self, data):
        if self._in_ld:
            self.ld.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False


COUNT_WORDS = r"(fish fries|fundraisers|events|listings|parishes|counties|places)"
for f in sorted(DOCS.rglob("*.html")):
    rel = f.relative_to(DOCS)
    text = f.read_text()
    p = Page()
    p.feed(text)
    if p.lang != "en":
        bad(f"{rel}: html lang missing")
    if p.h1 != 1:
        bad(f"{rel}: has {p.h1} h1 elements")
    if not (p.has_main and p.has_skip and p.has_title):
        bad(f"{rel}: missing main, skip link or title")
    if p.dupes:
        bad(f"{rel}: duplicate ids {p.dupes}")
    for i in p.inputs:
        if not i or i not in p.labels_for:
            bad(f"{rel}: form field {i} has no label")
    if p.svgs_missing_label:
        bad(f"{rel}: {p.svgs_missing_label} svg without aria-hidden or a label")
    for block in p.ld:
        try:
            json.loads(block)
        except ValueError:
            bad(f"{rel}: JSON-LD does not parse")
    visible = re.sub(r"<script.*?</script>|<[^>]+>", " ", text, flags=re.S)
    if re.search(r"\b\d[\d,]*\s+" + COUNT_WORDS, visible, re.I):
        bad(f"{rel}: states a count of listings")
    for href in p.links:
        if not href or href.startswith(("http://", "https://", "mailto:", "tel:", "#", "?")):
            continue
        if f.name == "404.html" and href.startswith("/"):
            continue
        target = (f.parent / urlparse(href).path).resolve()
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            bad(f"{rel}: broken link {href}")

for p in problems:
    print("PROBLEM:", p)
print(f"{len(problems)} problems")
sys.exit(1 if problems else 0)
