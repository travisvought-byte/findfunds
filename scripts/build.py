"""Build the Ohio community events directory into docs/ from the JSON files in data/.

Usage: python3 scripts/build.py

The output is deterministic (no build date), so CI can rebuild and check that docs/ is current.
"""
import csv
import io
import json
import re
import shutil
from pathlib import Path

import qrcode
import qrcode.image.svg

from ffconfig import (BASE_URL, DOWNLOADS_URL, BRAND_HTML, CURRENT_SEASON, FIND_BINGO_OHIO, GIVING_TUESDAY, GOATCOUNTER,
                  GOATCOUNTER_PREFIX, INDEXNOW_KEY, KINDS, MONTHS_LONG, ONLINE_RAFFLE_SALES_ALLOWED, ORG_TYPES,
                  SITE_NAME, SUBMIT_EMAIL, TYPES, VHG, county_slug, date_list, date_span, e, is_current, long_date,
                  phone_display, phone_href, time_range)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EVENTS = json.loads((ROOT / "data" / "events.json").read_text())
ZIPS = json.loads((ROOT / "data" / "ohio-zips.json").read_text())
SERIES = json.loads((ROOT / "data" / "series.json").read_text())
ORGS = json.loads((ROOT / "data" / "organizers.json").read_text())
ORG_BY_SLUG = {o["slug"]: o for o in ORGS}
COUNTIES = sorted({x["venue"]["county"] for x in EVENTS + SERIES if x["venue"]["county"]} | {o["county"] for o in ORGS if o["county"]})
VENDOR_MAPS = "https://github.com/travisvought-byte"

ICONS = {
    "fish": '<path d="M3 12c3-5 9-6 13-3l4-3v12l-4-3c-4 3-10 2-13-3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="8" cy="11" r="1.3" fill="currentColor"/>',
    "pancakes": '<ellipse cx="12" cy="8" rx="8" ry="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 8v3c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5V8M4 11v3c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-3M4 14v3c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-3" fill="none" stroke="currentColor" stroke-width="2"/>',
    "plate": '<circle cx="12" cy="12" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 4v6M5 4v6M3 10h2M4 10v10M21 4c-2 0-2 4-2 6h2v10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "cards": '<rect x="3" y="6" width="11" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 3h10a2 2 0 0 1 2 2v13" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8.5 11l2 2.5-2 2.5-2-2.5z" fill="currentColor"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "ticket": '<path d="M3 8a2 2 0 0 0 0 4v0a2 2 0 0 1 0 4v2h18v-2a2 2 0 0 1 0-4 2 2 0 0 0 0-4V6H3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M14 6v12" stroke="currentColor" stroke-width="2" stroke-dasharray="2 2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "clock": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7v5l3 2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="10" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/>',
    "phone": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "info": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 11v6M12 7.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "print": '<path d="M6 9V3h12v6M6 18H4v-7h16v7h-2M7 14h10v7H7z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "flag": '<path d="M5 21V4M5 4h11l-2 4 2 4H5" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>',
    "star": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "gift": '<rect x="3" y="9" width="18" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 9v12M3 13h18M12 9c-2-4-6-4-6-1.5S9 9 12 9c3 0 6-.5 6-1.5S14 5 12 9z" fill="none" stroke="currentColor" stroke-width="2"/>',
    "basket": '<path d="M3 10h18l-2 10H5zM8 10l3-6M16 10l-3-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "music": '<path d="M9 18V5l11-2v13" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="6.5" cy="18" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="16" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/>',
    "car": '<path d="M4 16v-4l2-5h12l2 5v4zM4 16v3M20 16v3M3 12h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="7.5" cy="14" r="1" fill="currentColor"/><circle cx="16.5" cy="14" r="1" fill="currentColor"/>',
    "run": '<circle cx="14" cy="4.5" r="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M6 21l4-6 3 2 1 4M9 11l3-3 3 3 3 1M10 15l2-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "book": '<path d="M4 4h6a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4zM20 4h-6a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h6z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "tree": '<path d="M12 3l6 8h-3l4 6H5l4-6H6zM12 17v4" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "users": '<circle cx="9" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5.5a3 3 0 0 1 0 5M18 14c2 .8 3 3 3 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "church": '<path d="M12 2v5M10 4h4M5 21V11l7-4 7 4v10zM10 21v-5h4v5" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "fire": '<path d="M12 21c-4 0-7-2.7-7-6.5C5 10 9 8 9 3c3 2 5 4.5 5 7 1-1 1.5-2.5 1.5-3.5C18 9 19 12 19 14.5 19 18.3 16 21 12 21z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "building": '<path d="M4 21V5l8-2v18M12 8h8v13M2 21h20M7 8h2M7 12h2M7 16h2M15 12h2M15 16h2" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "globe": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" fill="none" stroke="currentColor" stroke-width="2"/>',
    "search": '<circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "share": '<circle cx="6" cy="12" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="6" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="18" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6" stroke="currentColor" stroke-width="2"/>',
}


def icon(name, cls="ic"):
    # Each page carries one copy of each icon it uses (see sprite()); this points at it. Keeps pages small.
    assert name in ICONS, name
    return f'<svg class="{cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def sprite(html):
    """The icons a page uses, defined once, hidden. Nothing here is read aloud."""
    used = sorted(set(re.findall(r'<use href="#i-([a-z]+)"/>', html)))
    if not used:
        return ""
    symbols = "".join(f'<symbol id="i-{n}" viewBox="0 0 24 24">{ICONS[n]}</symbol>' for n in used)
    return f'<svg class="sprite" width="0" height="0" aria-hidden="true" focusable="false">{symbols}</svg>'


def up(depth):
    return "../" * depth if depth else "./"


def zip_point(rec):
    z = rec["venue"].get("zip")
    if z and z in ZIPS:
        return ZIPS[z], False
    # No ZIP: use the middle of the other listings in the same city, marked approximate.
    pt = CITY_POINTS.get(rec["venue"]["city"].lower())
    return (pt, True) if pt else (None, True)


def _city_points():
    acc = {}
    for city, z in ([(r["venue"]["city"], r["venue"].get("zip")) for r in EVENTS + SERIES] + [(o["city"], o.get("zip")) for o in ORGS]):
        if city and z in ZIPS:
            acc.setdefault(city.lower(), []).append(ZIPS[z])
    return {c: [round(sum(p[0] for p in v) / len(v), 3), round(sum(p[1] for p in v) / len(v), 3)] for c, v in acc.items()}


CITY_POINTS = _city_points()


def page(*, title, description, path, depth, body, jsonld=None, scripts=""):
    canonical = BASE_URL + "/" + path
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    r = up(depth)
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{r}assets/site.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="top">
<div class="wrap top-in">
<a class="brand" href="{r}">{icon("pin", "ic brand-ic")}<span>{BRAND_HTML}</span></a>
<nav aria-label="Main">
<ul>
<li><a href="{r}events/">Events</a></li>
<li><a href="{r}fish-fries/">Fish fries</a></li>
<li><a href="{r}organizers/">Who runs them</a></li>
<li><a href="{r}add/">Add your event</a></li>
<li><a href="{r}about/">About</a></li>
</ul>
</nav>
</div>
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer class="foot">
<div class="wrap">
<p>{SITE_NAME} is a free community service of <a href="{VHG}">Veteran Home Guardians</a>, an Ohio 501(c)(3). Listings are free. We never take money for the groups listed here: every gift goes straight to the group through its own link or at the door.</p>
<p>Looking for bingo? <a href="{FIND_BINGO_OHIO}">Find Bingo in Ohio</a>. Support our nursing-home visits: <a href="{GIVING_TUESDAY}">Give to VHG on Giving Tuesday</a>.</p>
<p><a href="{r}data/">Open data (CC BY 4.0)</a> · <a href="{r}about/#privacy">Privacy</a> · <a href="{r}add/">Report a change</a></p>
</div>
</footer>
<script>window.goatcounter={{path:function(p){{return '{GOATCOUNTER_PREFIX}'+p}}}};</script>
<script data-goatcounter="{GOATCOUNTER}" async src="https://gc.zgo.at/count.js"></script>
{scripts}
</body>
</html>
"""
    return html.replace("<body>\n", "<body>\n" + sprite(html) + "\n", 1)


def type_badge(rec):
    t = TYPES[rec["type"]]
    return f'<span class="badge">{icon(t["icon"])}<span>{e(t["label"])}</span></span>'


def schedule_lines(rec):
    """Plain-language date and time lines for a listing."""
    times = time_range(rec.get("start_time", ""), rec.get("end_time", ""))
    dates = date_list(rec.get("dates", []))
    if is_current(rec):
        return dates, times, ""
    season = rec.get("season", "last year")
    note = f"These are {e(season)} dates from the {e(rec['source'])}. {e(CURRENT_SEASON)} dates aren't posted yet, so call before you go."
    return f"{e(dates)} (last year)", times, note


def card(rec, depth):
    r = up(depth)
    v = rec["venue"]
    point, approx = zip_point(rec)
    dates, times, note = schedule_lines(rec)
    attrs = f'data-county="{e(v["county"])}" data-type="{e(rec["type"])}"'
    if point:
        attrs += f' data-lat="{point[0]}" data-lon="{point[1]}"'
    phone = rec["host"].get("phone", "")
    phone_html = f'<li>{icon("phone")}<a href="{phone_href(phone)}">{e(phone_display(phone))}</a></li>' if phone_href(phone) else ""
    time_html = f'<li>{icon("clock")}<span>{e(times)}</span></li>' if times else f'<li>{icon("clock")}<span>Times not listed; call first</span></li>'
    note_html = f'<p class="note">{icon("info")}<span>{note}</span></p>' if note else ""
    return f"""<li class="card" {attrs}>
<article>
<h3><a href="{r}e/{e(rec['slug'])}/">{e(rec['name'])}</a></h3>
<p class="where">{type_badge(rec)} <span>{e(v['city'])}, {e(v['county'])} County</span> <span class="dist" hidden></span></p>
<ul class="facts">
<li>{icon("calendar")}<span>{dates}</span></li>
{time_html}
<li>{icon("pin")}<span>{e(v['address'])}, {e(v['city'])}</span></li>
{phone_html}
</ul>
{note_html}
</article>
</li>"""


def finder_box(depth, heading="Find one near you"):
    return f"""<section class="finder" aria-labelledby="finder-h">
<h2 id="finder-h">{e(heading)}</h2>
<form class="zipform" role="search">
<div class="field"><label for="zip">Your ZIP code</label><input id="zip" name="zip" inputmode="numeric" autocomplete="postal-code" pattern="[0-9]{{5}}" maxlength="5" placeholder="43015"></div>
<div class="field"><label for="miles">Distance</label><select id="miles" name="miles"><option value="10">10 miles</option><option value="25" selected>25 miles</option><option value="50">50 miles</option><option value="0">Any distance</option></select></div>
<button type="submit">Show closest first</button>
</form>
<p class="status" role="status" aria-live="polite"></p>
</section>"""


def listing_section(recs, depth, heading_level="h2"):
    by_county = {}
    for rec in sorted(recs, key=lambda x: (x["venue"]["county"], x["venue"]["city"], x["name"])):
        by_county.setdefault(rec["venue"]["county"], []).append(rec)
    jump = " · ".join(f'<a href="#{county_slug(c)}">{e(c)}</a>' for c in by_county)
    groups = []
    for c, items in by_county.items():
        cards = "\n".join(card(x, depth) for x in items)
        groups.append(f'<section class="county" id="{county_slug(c)}" aria-labelledby="{county_slug(c)}-h"><{heading_level} id="{county_slug(c)}-h">{e(c)} County</{heading_level}><ul class="cards">{cards}</ul></section>')
    return f"""<nav class="jump" aria-label="Jump to a county"><p><strong>Jump to your county:</strong> {jump}</p></nav>
<div class="results" data-results>
{''.join(groups)}
</div>
<ol class="cards sorted" data-sorted hidden></ol>"""


def finder_script(depth):
    return f'<script src="{up(depth)}assets/finder.js" defer data-zips="{up(depth)}data/ohio-zips.json"></script>'


def qr_svg(url):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    svg = svg[svg.index("<svg"):]
    # ElementTree's spacing before "/>" differs between Python versions; normalize it.
    svg = svg.replace(" />", "/>")
    return svg.replace("<svg ", '<svg role="img" aria-label="QR code for this page" class="qr" ', 1)


def event_jsonld(rec, url):
    """One Event per dated occurrence in the current season; none for last year's schedule."""
    if not is_current(rec):
        return None
    v = rec["venue"]
    place = {"@type": "Place", "name": v["name"],
             "address": {"@type": "PostalAddress", "streetAddress": v["address"], "addressLocality": v["city"],
                         "addressRegion": "OH", "postalCode": v.get("zip", ""), "addressCountry": "US"}}
    events = []
    for d in rec["dates"]:
        ev = {"@type": "Event", "name": rec["name"], "url": url, "location": place,
              "eventStatus": "https://schema.org/EventScheduled",
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "organizer": {"@type": "Organization", "name": rec["host"]["name"]},
              "startDate": f"{d}T{rec['start_time']}" if rec.get("start_time") else d}
        if rec.get("end_time"):
            ev["endDate"] = f"{d}T{rec['end_time']}"
        events.append(ev)
    return {"@context": "https://schema.org", "@graph": events}


def event_page(rec):
    depth = 2
    r = up(depth)
    v = rec["venue"]
    url = f"{BASE_URL}/e/{rec['slug']}/"
    dates, times, note = schedule_lines(rec)
    phone = rec["host"].get("phone", "")
    t = TYPES[rec["type"]]
    map_q = f"{v['address']}, {v['city']}, OH {v.get('zip', '')}".strip()
    rows = [
        ("calendar", "Dates", dates),
        ("clock", "Times", e(times) if times else "Not listed; call first"),
        ("pin", "Where", f'{e(v["name"])}<br>{e(v["address"])}<br>{e(v["city"])}, OH {e(v.get("zip", ""))}<br><a href="https://www.openstreetmap.org/search?query={e(map_q.replace(" ", "+"))}">Map and directions</a>'),
    ]
    if phone_href(phone):
        rows.append(("phone", "Call", f'<a href="{phone_href(phone)}">{e(phone_display(phone))}</a>'))
    if rec.get("price"):
        rows.append(("info", "Price", e(rec["price"])))
    if rec.get("menu"):
        rows.append(("fish", "Menu", e(rec["menu"])))
    if rec.get("service"):
        rows.append(("info", "Service", e(", ".join(rec["service"]))))
    give = ""
    if rec.get("give_link"):
        give = f'<p><a class="btn" href="{e(rec["give_link"])}" data-goatcounter-click="give/{e(rec["slug"])}">Give to {e(rec["host"]["name"])}</a></p>'
    raffle = ""
    if rec.get("raffle") and not ONLINE_RAFFLE_SALES_ALLOWED:
        raffle = f'<p class="note">{icon("ticket")}<span>Raffle and 50/50 tickets are sold in person only, as Ohio law requires.</span></p>'
    deductible = ""
    if rec["type"] == "benefit_person":
        deductible = f'<p class="note">{icon("info")}<span>This benefit helps a person, so gifts aren\'t tax-deductible.</span></p>'
    facts = "\n".join(f'<div class="row"><dt>{icon(ic)}<span>{e(label)}</span></dt><dd>{val}</dd></div>' for ic, label, val in rows)
    checked = long_date(rec["reviewed_on"])
    trust = {"public_list": f'From the <a href="{e(rec["source_url"])}">{e(rec["source"])}</a>, checked {checked}. Not yet confirmed by the organizer.',
             "organizer": f'Confirmed by the organizer, {checked}.',
             "claimed": "This page is kept up to date by the organizer."}[rec["trust"]]
    share_text = f"{rec['name']}, {v['city']}"
    body = f"""<div class="wrap narrow event">
<p class="crumbs"><a href="{r}">Home</a> › <a href="{r}{t['path']}/">{e(t['plural'])}</a> › <a href="{r}ohio/{county_slug(v['county'])}/">{e(v['county'])} County</a></p>
<h1>{e(rec['name'])}</h1>
<p class="where">{type_badge(rec)} <span>{e(v['city'])}, {e(v['county'])} County, Ohio</span></p>
{f'<p class="note big">{icon("info")}<span>{note}</span></p>' if note else ''}
<dl class="facts-list">
{facts}
</dl>
{give}{raffle}{deductible}
<div class="actions no-print">
<button type="button" class="btn" data-print data-goatcounter-click="flyer/{e(rec['slug'])}">{icon("print")}<span>Print a flyer</span></button>
<button type="button" class="btn ghost" data-share data-title="{e(share_text)}">{icon("share")}<span>Share this page</span></button>
</div>
<div class="flyer-qr">
{qr_svg(url)}
<p>Scan for times and directions, or visit <strong>{e(url.replace('https://', ''))}</strong></p>
</div>
<p class="trust">{trust}</p>
<p class="no-print">Run this event? <a href="{r}add/?event={e(rec['slug'])}">Send new dates or a correction</a>. It's free.</p>
</div>"""
    desc = f"{rec['name']} in {v['city']}, Ohio: dates, times, address and phone."
    return page(title=f"{rec['name']}, {v['city']} | {SITE_NAME}", description=desc, path=f"e/{rec['slug']}/",
                depth=depth, body=body, jsonld=event_jsonld(rec, url),
                scripts=f'<script src="{r}assets/event.js" defer></script>')


# ---------- recurring events (series) ----------

def cap(text):
    text = re.sub(r"\blent\b", "Lent", text)
    return text[:1].upper() + text[1:]


DATED_SPAN_KINDS = {"fair", "festival", "holiday", "market", "concert", "car_show", "parade", "run_walk"}


def series_when(s):
    """(dates text, is_last_year) for a series."""
    if s["next_dates"]:
        ds, last = s["next_dates"], False
    elif s["last_dates"]:
        ds, last = s["last_dates"], True
    else:
        return "", False
    text = date_span(ds) if (s["kind"] in DATED_SPAN_KINDS or len(ds) == 2 and s["kind"] != "fish_fry") else date_list(ds)
    return text, last


def series_month(s):
    ds = s["next_dates"] or s["last_dates"]
    return int(ds[0][5:7]) if ds else 0


def kind_badge(kind):
    k = KINDS[kind]
    return f'<span class="badge">{icon(k["icon"])}<span>{e(k["label"])}</span></span>'


def org_link(s, depth):
    o = ORG_BY_SLUG.get(s.get("organizer_slug"))
    name = s["organizer"].get("name") or (o["name"] if o else "")
    if o and o["county"]:
        return f'<a href="{up(depth)}ohio/{county_slug(o["county"])}/#{e(o["slug"])}">{e(name)}</a>'
    return e(name)


def series_item(s, depth, show_county=True):
    """Compact list item used on the search page, kind pages and county hubs."""
    r = up(depth)
    v = s["venue"]
    when, last = series_when(s)
    when_html = f"{e(when)} (last year)" if last else e(when)
    if not when_html:
        when_html = e(s["timing"]) or "Dates not posted yet"
    elif s["timing"] and last:
        when_html = f"{e(cap(s['timing']))}. {when_html}"
    text = f"{s['name']} {v['city']} {v['county']}".lower()
    place = f"{e(v['city'])}, {e(v['county'])} County" if show_county else e(v["city"])
    return f"""<li class="item" data-county="{e(v['county'])}" data-month="{series_month(s)}" data-kind="{e(s['kind'])}" data-text="{e(text)}">
<a class="item-name" href="{r}events/{e(s['slug'])}/">{e(s['name'])}</a>
<span class="item-meta">{kind_badge(s['kind'])} <span>{icon("pin")}{place}</span> <span>{icon("calendar")}{when_html}</span></span>
</li>"""


def series_jsonld(s, url):
    if not s["next_dates"]:
        return None
    v = s["venue"]
    ev = {"@context": "https://schema.org", "@type": "Event", "name": s["name"], "url": url,
          "startDate": s["next_dates"][0], "endDate": s["next_dates"][-1],
          "eventStatus": "https://schema.org/EventScheduled",
          "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
          "location": {"@type": "Place", "name": v["name"] or v["city"],
                       "address": {"@type": "PostalAddress", "streetAddress": v["address"], "addressLocality": v["city"],
                                   "addressRegion": "OH", "postalCode": v["zip"], "addressCountry": "US"}}}
    if s["organizer"].get("name"):
        ev["organizer"] = {"@type": "Organization", "name": s["organizer"]["name"]}
    return ev


def series_page(s):
    depth = 2
    r = up(depth)
    v = s["venue"]
    k = KINDS[s["kind"]]
    url = f"{BASE_URL}/events/{s['slug']}/"
    when, last = series_when(s)
    rows = []
    if s["timing"]:
        rows.append(("calendar", "Usually", e(cap(s["timing"]))))
    if when:
        rows.append(("calendar", "Last year" if last else "Dates", e(when)))
    times = time_range(s["start_time"], s["end_time"])
    if times:
        rows.append(("clock", "Times", e(times)))
    where = "<br>".join(e(x) for x in (v["name"], v["address"], f"{v['city']}, OH {v['zip']}".strip()) if x)
    map_q = ", ".join(x for x in (v["name"], v["address"], v["city"], "OH") if x)
    where += f'<br><a href="https://www.openstreetmap.org/search?query={e(map_q.replace(" ", "+"))}">Map and directions</a>'
    rows.append(("pin", "Where", where))
    if s["organizer"].get("name"):
        rows.append(("users", "Run by", org_link(s, depth)))
    phone = s["organizer"].get("phone") or (ORG_BY_SLUG.get(s["organizer_slug"]) or {}).get("phone", "")
    if phone_href(phone):
        rows.append(("phone", "Call", f'<a href="{phone_href(phone)}">{e(phone_display(phone))}</a>'))
    if s["website"]:
        rows.append(("globe", "Website", f'<a href="{e(s["website"])}">Official event page</a>'))
    cost = {"free": "Free to attend", "paid": "Admission or food costs money", "varies": "Some parts cost money"}.get(s["cost"])
    if cost:
        rows.append(("ticket", "Cost", cost))
    facts = "\n".join(f'<div class="row"><dt>{icon(ic)}<span>{e(label)}</span></dt><dd>{val}</dd></div>' for ic, label, val in rows)
    checked = long_date(s["checked_on"]) if s["checked_on"] else ""
    src = f'<a href="{e(s["source_url"])}">{e(s["source"])}</a>' if s["source_url"] else e(s["source"])
    trust = (f"Checked against the organizer's own site on {checked}." if s["trust"] == "organizer_page"
             else f"From {src}, checked {checked}. Not yet confirmed by the organizer.")
    note = ""
    if last:
        note = f'<p class="note big">{icon("info")}<span>This year\'s dates aren\'t posted yet. The dates shown are last year\'s, so check with the organizer before you go.</span></p>'
    body = f"""<div class="wrap narrow event">
<p class="crumbs"><a href="{r}">Home</a> › <a href="{r}{k['path']}/">{e(k['plural'])}</a> › <a href="{r}ohio/{county_slug(v['county'])}/">{e(v['county'])} County</a></p>
<h1>{e(s['name'])}</h1>
<p class="where">{kind_badge(s['kind'])} <span>{e(v['city'])}, {e(v['county'])} County, Ohio</span></p>
{note}
<dl class="facts-list">
{facts}
</dl>
<div class="actions no-print">
<button type="button" class="btn ghost" data-share data-title="{e(s['name'] + ', ' + v['city'])}">{icon("share")}<span>Share this page</span></button>
</div>
<p class="trust">{trust}</p>
<p class="no-print">Run this event? <a href="{r}add/?event={e(s['slug'])}">Send this year's dates or a correction</a>. It's free.</p>
<p class="no-print">More in {e(v['county'])} County: <a href="{r}ohio/{county_slug(v['county'])}/">events and the groups that run them</a>.</p>
</div>"""
    desc = f"{s['name']} in {v['city']}, Ohio: when it happens, where, who runs it and how to reach them."
    return page(title=f"{s['name']}, {v['city']}, Ohio | {SITE_NAME}", description=desc, path=f"events/{s['slug']}/",
                depth=depth, body=body, jsonld=series_jsonld(s, url), scripts=f'<script src="{r}assets/event.js" defer></script>')


def filter_form(depth, kinds, preset_kind=""):
    county_opts = "".join(f'<option value="{e(c)}">{e(c)} County</option>' for c in COUNTIES)
    month_opts = "".join(f'<option value="{i}">{m}</option>' for i, m in enumerate(MONTHS_LONG, 1))
    kind_opts = "".join(f'<option value="{k}"{" selected" if k == preset_kind else ""}>{e(KINDS[k]["plural"])}</option>' for k in kinds)
    kind_field = "" if preset_kind else f'<div class="field"><label for="f-kind">Kind of event</label><select id="f-kind" name="kind"><option value="">All kinds</option>{kind_opts}</select></div>'
    return f"""<section class="finder" aria-labelledby="filter-h">
<h2 id="filter-h">{icon("search")}<span>Search events</span></h2>
<form class="filterform" role="search">
<div class="field"><label for="f-county">County</label><select id="f-county" name="county"><option value="">All counties</option>{county_opts}</select></div>
<div class="field"><label for="f-month">Month</label><select id="f-month" name="month"><option value="">Any month</option>{month_opts}</select></div>
{kind_field}
<div class="field"><label for="f-q">Name or town</label><input id="f-q" name="q" type="search" autocomplete="off"></div>
<button type="submit">Show events</button>
</form>
<p class="status" role="status" aria-live="polite"></p>
</section>"""


def grouped_by_month(items, depth):
    by_month = {}
    for s in items:
        by_month.setdefault(series_month(s), []).append(s)
    out = []
    for m in sorted(by_month, key=lambda m: m or 13):
        name = MONTHS_LONG[m - 1] if m else "Dates not posted yet"
        hid = f"m-{m or 'tbd'}"
        lis = "\n".join(series_item(s, depth) for s in sorted(by_month[m], key=lambda s: ((s["next_dates"] or s["last_dates"] or [""])[0], s["name"])))
        out.append(f'<section class="month" id="{hid}" aria-labelledby="{hid}-h" data-month-group><h2 id="{hid}-h">{e(name)}</h2><ul class="items">{lis}</ul></section>')
    jump = " · ".join(f'<a href="#m-{m or "tbd"}">{e(MONTHS_LONG[m - 1] if m else "Not posted")}</a>' for m in sorted(by_month, key=lambda m: m or 13))
    return f'<nav class="jump" aria-label="Jump to a month"><p><strong>Jump to a month:</strong> {jump}</p></nav>\n<div data-filterable>{"".join(out)}</div>\n<p class="empty" data-empty hidden>No events match. Try another month or county, or <a href="{up(depth)}add/">add one you know about</a>.</p>'


def events_index():
    kinds = [k for k in KINDS if any(s["kind"] == k for s in SERIES)]
    body = f"""<div class="wrap">
<h1>{icon("calendar")}<span>Ohio community events</span></h1>
<p class="lead">Fairs, festivals, fish fries, parades, holiday events and more, by county and month. Most dates shown are last year's, since organizers post the coming year's dates in the spring; each listing says which.</p>
{filter_form(1, kinds)}
<p>Fish fries with ZIP code search are on the <a href="../fish-fries/">fish fry page</a>.</p>
{grouped_by_month(SERIES, 1)}
</div>"""
    return page(title=f"Ohio community events by county and month | {SITE_NAME}",
                description="Find Ohio county fairs, festivals, fish fries, parades and holiday events by county and month, with who runs them.",
                path="events/", depth=1, body=body, scripts='<script src="../assets/filter.js" defer></script>')


def kind_page(kind):
    k = KINDS[kind]
    items = [s for s in SERIES if s["kind"] == kind]
    intro = {
        "fair": "Every Ohio county fair and independent fair, run by the county agricultural societies. Fair season runs from June through October.",
        "festival": "Town, church and heritage festivals across Ohio, from strawberry and sweet corn festivals to Oktoberfests.",
        "holiday": "Holiday lights, parades, tree lightings and Christmas walks across Ohio.",
    }.get(kind, f"{k['plural']} across Ohio.")
    body = f"""<div class="wrap">
<p class="crumbs"><a href="../">Home</a> › <a href="../events/">Events</a></p>
<h1>{icon(k['icon'])}<span>Ohio {e(k['plural'].lower())}</span></h1>
<p class="lead">{e(intro)} Dates marked "last year" are last year's schedule; check with the organizer before you go.</p>
{filter_form(1, [kind], preset_kind=kind)}
{grouped_by_month(items, 1)}
</div>"""
    return page(title=f"Ohio {k['plural'].lower()}: dates and places | {SITE_NAME}",
                description=f"Ohio {k['plural'].lower()} by county and month, with dates, places and who runs them.",
                path=f"{k['path']}/", depth=1, body=body, scripts='<script src="../assets/filter.js" defer></script>')


def fish_page():
    fish_events = [x for x in EVENTS if x["type"] == "fish_fry"]
    fish_series = [s for s in SERIES if s["kind"] == "fish_fry"]
    t = TYPES["fish_fry"]
    lis = "\n".join(series_item(s, 1) for s in sorted(fish_series, key=lambda s: (s["venue"]["county"], s["venue"]["city"], s["name"])))
    body = f"""<div class="wrap">
<p class="crumbs"><a href="../">Home</a> › <a href="../events/">Events</a></p>
<h1>{icon(t['icon'])}<span>Ohio fish fries</span></h1>
<p class="lead">Lent 2027 runs from Ash Wednesday, February 10, to Easter, March 28. Most fish fries are on Fridays. Listings showing 2026 dates are last year's schedule; call before you go.</p>
{finder_box(1)}
{listing_section(fish_events, 1)}
<section aria-labelledby="more-fish-h">
<h2 id="more-fish-h">More fish fries around Ohio</h2>
<p>From diocesan and local news fish fry lists, last Lent. Each has its own page with the details we have.</p>
<ul class="items">{lis}</ul>
</section>
</div>"""
    return page(title=f"Ohio fish fries near you, Lent 2027 | {SITE_NAME}",
                description="Find Ohio fish fries by ZIP code and county: parish, Legion, VFW and fire department fish fries with dates, times and phone numbers.",
                path="fish-fries/", depth=1, body=body, scripts=finder_script(1))


# ---------- organizers ----------

def org_row(o, depth, show_county=False):
    bits = []
    place = ", ".join(x for x in (o["address"], o["city"]) if x)
    if show_county and o["county"]:
        place += f" ({o['county']} County)"
    if place:
        bits.append(f'<span>{icon("pin")}{e(place)}</span>')
    if phone_href(o["phone"]):
        bits.append(f'<span>{icon("phone")}<a href="{phone_href(o["phone"])}">{e(phone_display(o["phone"]))}</a></span>')
    if o["events_url"]:
        bits.append(f'<span>{icon("calendar")}<a href="{e(o["events_url"])}">Events calendar<span class="sr-only"> for {e(o["name"])}</span></a></span>')
    if o["website"] and o["website"] != o["events_url"]:
        bits.append(f'<span>{icon("globe")}<a href="{e(o["website"])}">Website<span class="sr-only"> for {e(o["name"])}</span></a></span>')
    hosted = [s for s in SERIES if s.get("organizer_slug") == o["slug"]]
    if hosted:
        links = ", ".join(f'<a href="{up(depth)}events/{e(s["slug"])}/">{e(s["name"])}</a>' for s in hosted[:6])
        bits.append(f'<span>{icon("star")}Runs {links}</span>')
    return f'<li class="item org" id="{e(o["slug"])}"><span class="item-name">{e(o["name"])}</span><span class="item-meta">{" ".join(bits)}</span></li>'


def organizers_index():
    present = [t for t in ORG_TYPES if any(o["type"] == t for o in ORGS)]
    tiles = "".join(f'<li><a class="tile" href="{ORG_TYPES[t]["path"]}/">{icon(ORG_TYPES[t]["icon"])}<span>{e(ORG_TYPES[t]["plural"])}</span></a></li>' for t in present)
    counties = "".join(f'<li><a href="../ohio/{county_slug(c)}/">{e(c)}</a></li>' for c in COUNTIES)
    body = f"""<div class="wrap">
<h1>{icon("users")}<span>Who runs community events in Ohio</span></h1>
<p class="lead">Veterans posts, parishes, fire departments, libraries, park districts, fair boards, chambers and visitors bureaus: the groups that put on the fairs, dinners, breakfasts and festivals in every county. Reach out to them to go, volunteer or join.</p>
<h2>By kind of group</h2>
<ul class="tiles">{tiles}</ul>
<h2>By county</h2>
<ul class="county-grid">{counties}</ul>
</div>"""
    return page(title=f"Who runs community events in Ohio | {SITE_NAME}",
                description="Ohio veterans posts, parishes, fire departments, libraries, park districts, fair boards and chambers that run community events, by county.",
                path="organizers/", depth=1, body=body)


def org_type_page(t):
    ot = ORG_TYPES[t]
    orgs = [o for o in ORGS if o["type"] == t]
    by_county = {}
    for o in orgs:
        by_county.setdefault(o["county"] or "County not listed", []).append(o)
    keys = sorted(by_county, key=lambda c: (c == "County not listed", c))
    jump = " · ".join(f'<a href="#{slugify_id(c)}">{e(c)}</a>' for c in keys)
    groups = "".join(
        f'<section id="{slugify_id(c)}" aria-labelledby="{slugify_id(c)}-h"><h2 id="{slugify_id(c)}-h">{e(c if c == "County not listed" else c + " County")}</h2><ul class="items">{"".join(org_row(o, 2) for o in sorted(by_county[c], key=lambda o: (o["city"], o["name"])))}</ul></section>'
        for c in keys)
    body = f"""<div class="wrap">
<p class="crumbs"><a href="../../">Home</a> › <a href="../">Who runs them</a></p>
<h1>{icon(ot['icon'])}<span>{e(ot['plural'])} in Ohio</span></h1>
<p class="lead">Contact details come from public rosters and each group's own site. Call ahead before visiting; hours and events change.</p>
<nav class="jump" aria-label="Jump to a county"><p><strong>Jump to a county:</strong> {jump}</p></nav>
{groups}
</div>"""
    return page(title=f"{ot['plural']} in Ohio, by county | {SITE_NAME}",
                description=f"Ohio {ot['plural'].lower()} by county, with addresses, phone numbers and events calendars.",
                path=f"organizers/{ot['path']}/", depth=2, body=body)


def slugify_id(text):
    from ffconfig import slugify
    return "c-" + slugify(text)


def county_hub(county):
    depth = 2
    r = up(depth)
    fish = [x for x in EVENTS if x["venue"]["county"] == county]
    series = [s for s in SERIES if s["venue"]["county"] == county]
    orgs = [o for o in ORGS if o["county"] == county]
    sections = []
    if fish:
        sections.append(f'<section aria-labelledby="fish-h"><h2 id="fish-h">{icon("fish")}<span>Fish fries</span></h2><ul class="cards">{"".join(card(x, depth) for x in sorted(fish, key=lambda x: (x["venue"]["city"], x["name"])))}</ul></section>')
    if series:
        by_kind = {}
        for s in series:
            by_kind.setdefault(s["kind"], []).append(s)
        parts = []
        for k in KINDS:
            if k in by_kind:
                lis = "".join(series_item(s, depth, show_county=False) for s in sorted(by_kind[k], key=lambda s: (series_month(s) or 13, s["name"])))
                parts.append(f'<h3>{icon(KINDS[k]["icon"])}<span>{e(KINDS[k]["plural"])}</span></h3><ul class="items">{lis}</ul>')
        sections.append(f'<section aria-labelledby="ev-h"><h2 id="ev-h">{icon("calendar")}<span>Events through the year</span></h2>{"".join(parts)}</section>')
    if orgs:
        by_type = {}
        for o in orgs:
            by_type.setdefault(o["type"], []).append(o)
        parts = []
        for t in ORG_TYPES:
            if t in by_type:
                parts.append(f'<h3>{icon(ORG_TYPES[t]["icon"])}<span>{e(ORG_TYPES[t]["plural"])}</span></h3><ul class="items">{"".join(org_row(o, depth) for o in sorted(by_type[t], key=lambda o: (o["city"], o["name"])))}</ul>')
        sections.append(f'<section aria-labelledby="org-h"><h2 id="org-h">{icon("users")}<span>Who runs events here</span></h2><p>Call or visit their calendars to go, volunteer or join.</p>{"".join(parts)}</section>')
    body = f"""<div class="wrap">
<p class="crumbs"><a href="{r}">Home</a> › <a href="{r}organizers/">Counties</a> › {e(county)} County</p>
<h1>Community events in {e(county)} County, Ohio</h1>
<p class="lead">Fairs, festivals, fish fries and more in {e(county)} County, and the posts, parishes, libraries and other groups that run them. Dates marked "last year" are last year's schedule; check before you go.</p>
{"".join(sections)}
<p>Don't see your event or group? <a href="{r}add/">Add it for free</a>.</p>
</div>"""
    return page(title=f"{county} County, Ohio community events and who runs them | {SITE_NAME}",
                description=f"Fairs, festivals, fish fries and community groups in {county} County, Ohio, with dates, places, phone numbers and calendars.",
                path=f"ohio/{county_slug(county)}/", depth=depth, body=body)


def home_page():
    kinds = ["fair", "festival", "fish_fry", "holiday"]
    tiles = "".join(f'<li><a href="{KINDS[k]["path"]}/" class="tile">{icon(KINDS[k]["icon"])}<span>{e(KINDS[k]["plural"])}</span></a></li>' for k in kinds)
    tiles += f'<li><a href="events/" class="tile">{icon("calendar")}<span>All events by month</span></a></li>'
    tiles += f'<li><a href="organizers/" class="tile">{icon("users")}<span>Who runs them</span></a></li>'
    tiles += f'<li><a href="add/" class="tile add">{icon("heart")}<span>Add your event</span></a></li>'
    county_opts = "".join(f'<option value="{e(c)}">{e(c)} County</option>' for c in COUNTIES)
    month_opts = "".join(f'<option value="{i}">{m}</option>' for i, m in enumerate(MONTHS_LONG, 1))
    counties = "".join(f'<li><a href="ohio/{county_slug(c)}/">{e(c)}</a></li>' for c in COUNTIES)
    body = f"""<section class="hero">
<div class="wrap">
<h1>Find community events near you in Ohio</h1>
<p class="lead">County fairs, festivals, fish fries, parades and holiday events, and the posts, parishes, libraries and groups that run them. Free, in every county.</p>
<form class="homesearch" action="events/" method="get" role="search" aria-label="Search events">
<div class="field"><label for="h-county">County</label><select id="h-county" name="county"><option value="">All counties</option>{county_opts}</select></div>
<div class="field"><label for="h-month">Month</label><select id="h-month" name="month"><option value="">Any month</option>{month_opts}</select></div>
<button type="submit">{icon("search")}<span>Find events</span></button>
</form>
<ul class="tiles">{tiles}</ul>
</div>
</section>
<div class="wrap">
<section class="lent" aria-labelledby="lent-h">
<h2 id="lent-h">{icon("fish")}<span>Lenten fish fries</span></h2>
<p>Lent 2027 starts on Ash Wednesday, February 10. Parishes and posts usually post their fish fry dates in January. Until then, each listing shows last year's schedule so you know who holds one. <a href="fish-fries/">Find a fish fry by ZIP code</a>.</p>
</section>
<section aria-labelledby="county-h">
<h2 id="county-h">{icon("pin")}<span>Everything in your county</span></h2>
<ul class="county-grid">{counties}</ul>
</section>
</div>"""
    return page(title=f"Find community events in Ohio: fairs, festivals, fish fries | {SITE_NAME}",
                description="Free Ohio guide to county fairs, festivals, fish fries, parades and holiday events by county and month, and the groups that run them.",
                path="", depth=0, body=body,
                jsonld={"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE_URL + "/",
                        "publisher": {"@type": "Organization", "name": "Veteran Home Guardians", "url": VHG}})


def add_page():
    types = "".join(f'<option value="{e(t["label"])}">{e(t["label"])}</option>' for t in TYPES.values())
    days = "".join(f'<label class="check"><input type="checkbox" name="service" value="{v}"> {v}</label>' for v in ("Dine-in", "Carry-out", "Drive-thru"))
    body = f"""<div class="wrap narrow">
<h1>Add your event, free</h1>
<p class="lead">Fish fry, breakfast, euchre night, benefit dinner or raffle: tell us about it and we'll give it its own page and a printable flyer. Listings are always free.</p>
<form class="addform" data-mailto="{SUBMIT_EMAIL}">
<fieldset><legend>The event</legend>
<div class="field"><label for="f-name">Event name</label><input id="f-name" name="Event name" required></div>
<div class="field"><label for="f-type">Kind of event</label><select id="f-type" name="Kind of event">{types}</select></div>
<div class="field"><label for="f-host">Group hosting it</label><input id="f-host" name="Group hosting it" required placeholder="American Legion Post 123"></div>
<div class="field"><label for="f-for">Who the money goes to</label><input id="f-for" name="Who the money goes to"></div>
</fieldset>
<fieldset><legend>When and where</legend>
<div class="field"><label for="f-addr">Street address, city and ZIP</label><input id="f-addr" name="Address" required autocomplete="street-address"></div>
<div class="field"><label for="f-dates">Date or dates</label><input id="f-dates" name="Dates" required placeholder="Every Friday in Lent, or March 5"></div>
<div class="field"><label for="f-time">Times</label><input id="f-time" name="Times" placeholder="4:30 to 7 p.m."></div>
</fieldset>
<fieldset><legend>Details people ask about</legend>
<div class="field"><label for="f-price">Prices</label><input id="f-price" name="Prices" placeholder="Adults $15, kids $8"></div>
<div class="checks" role="group" aria-label="Service">{days}</div>
<div class="field"><label for="f-menu">Menu, in a sentence</label><input id="f-menu" name="Menu"></div>
<div class="field"><label for="f-give">Link where people can give or buy tickets online (optional)</label><input id="f-give" name="Give link" type="url" inputmode="url"><p class="hint">Ohio allows raffle tickets to be sold in person only, so please don't send an online raffle ticket link.</p></div>
<div class="field"><label for="f-access">Step-free entrance and accessible parking?</label><select id="f-access" name="Accessibility"><option>Not sure</option><option>Yes, both</option><option>Step-free entrance only</option><option>Accessible parking only</option><option>No</option></select></div>
<div class="field"><label for="f-phone">Public phone or website for questions</label><input id="f-phone" name="Public phone or website"></div>
</fieldset>
<fieldset><legend>About you (never published)</legend>
<div class="field"><label for="f-you">Your name and how to reach you</label><input id="f-you" name="Contact (private)" required></div>
<div class="field"><label for="f-role">You are</label><select id="f-role" name="Sender"><option>An organizer</option><option>A member</option><option>Someone who saw a flyer</option></select></div>
</fieldset>
<button type="submit" class="btn">Open my email to send this</button>
<p class="hint">This opens an email to {SUBMIT_EMAIL} with your answers filled in. Nothing is sent until you press Send. We check every listing before it goes up.</p>
</form>
</div>"""
    return page(title=f"Add your fundraiser or fish fry, free | {SITE_NAME}",
                description="List your Ohio fish fry, breakfast, euchre night or benefit dinner for free and get a page and printable flyer.",
                path="add/", depth=1, body=body, scripts='<script src="../assets/add.js" defer></script>')


def about_page():
    body = f"""<div class="wrap narrow prose">
<h1>About {SITE_NAME}</h1>
<p class="lead">{SITE_NAME} maps the fairs, festivals, fish fries, dinners and holiday events that bring Ohio towns together, and the posts, parishes, libraries, fire departments and other groups that run them, so anyone can find them and join in.</p>
<h2>Where listings come from</h2>
<ul>
<li>Public lists: the Ohio fair schedule, diocesan fish fry lists, festival calendars, and the rosters of veterans posts, libraries, park districts, chambers and visitors bureaus.</li>
<li>Organizers' own sites. A listing says whether it was checked there or only on someone else's list.</li>
<li>Anyone can send an event or a correction. We check each one before it goes up.</li>
</ul>
<p>Every listing shows its source and the date we last checked it. Listings we haven't rechecked in six months get checked again. Most dates shown in the off-season are last year's, and the listing says so.</p>
<h2>Money</h2>
<p>Listings are free. We never collect or hold money for anyone. Ohio allows raffle and 50/50 tickets to be sold in person only, so we never link to online raffle ticket sales.</p>
<h2>Related guides</h2>
<ul>
<li><a href="{FIND_BINGO_OHIO}">Find Bingo in Ohio</a>: bingo halls and sessions.</li>
<li><a href="{VHG}">Veteran Home Guardians</a>: veteran visitors for people in long-term care, and resources for veterans and families.</li>
</ul>
<h2>Open data</h2>
<p>The full lists are free to reuse under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. See <a href="../data/">the data page</a>.</p>
<h2 id="privacy">Privacy</h2>
<p>We count visits with GoatCounter, which uses no cookies and doesn't store your IP address. The site is hosted on GitHub Pages, which may keep server logs for security. Contact details you send with an event are used only to check it and are never published.</p>
<h2>Who runs it</h2>
<p>{SITE_NAME} is a free community service of <a href="{VHG}">Veteran Home Guardians</a>, an Ohio 501(c)(3) that places veteran visitors in long-term care facilities.</p>
</div>"""
    return page(title=f"About {SITE_NAME}", description=f"How {SITE_NAME} maps Ohio community events and the groups that run them, where listings come from, and privacy.",
                path="about/", depth=1, body=body)


def data_page():
    body = f"""<div class="wrap narrow prose">
<h1>Open data</h1>
<p class="lead">Every list is free to reuse under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Please credit "{SITE_NAME}, a service of Veteran Home Guardians".</p>
<ul>
<li><a href="{DOWNLOADS_URL}/series.json">series.json</a> and <a href="{DOWNLOADS_URL}/series.csv">series.csv</a>: recurring events (fairs, festivals, fish fries, holiday events and more) with place, organizer, last and next dates, source and last-checked date.</li>
<li><a href="{DOWNLOADS_URL}/organizers.json">organizers.json</a> and <a href="{DOWNLOADS_URL}/organizers.csv">organizers.csv</a>: the groups that run events, with address, phone, website, events calendar, source and last-checked date.</li>
<li><a href="{DOWNLOADS_URL}/events.json">events.json</a> and <a href="{DOWNLOADS_URL}/events.csv">events.csv</a>: dated fish fry listings with flyers.</li>
</ul>
<p>The download files are served from the GitHub copy of this site.</p>
<p>Event pages carry schema.org Event markup only for dates that are posted for the coming season. "trust" says how far a record was checked: "official_list" (from an official roster), "public_list" (from someone else's list), "organizer_page" (checked on the organizer's own site), "organizer" (confirmed by the organizer) or "claimed" (kept up to date by the organizer).</p>
</div>"""
    return page(title=f"Open data | {SITE_NAME}", description=f"Download {SITE_NAME}'s lists of Ohio community events and organizers as JSON or CSV, free under CC BY 4.0.",
                path="data/", depth=1, body=body)


def not_found():
    # Served for any missing path, so every link is absolute.
    body = f"""<div class="wrap narrow"><h1>We couldn't find that page</h1><p>The event may have moved. <a href="{BASE_URL}/events/">Search all events</a> or <a href="{BASE_URL}/add/">tell us what you were looking for</a>.</p></div>"""
    html = page(title=f"Page not found | {SITE_NAME}", description="Page not found.", path="404.html", depth=0, body=body)
    return html.replace('href="./', f'href="{BASE_URL}/').replace('src="./', f'src="{BASE_URL}/').replace('data-zips="./', f'data-zips="{BASE_URL}/')


def write(rel, text):
    p = DOCS / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def to_csv(rows, header):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    shutil.copytree(ROOT / "assets", DOCS / "assets")
    (DOCS / ".nojekyll").write_text("")
    urls = [""]
    write("index.html", home_page())
    write("events/index.html", events_index())
    urls.append("events/")
    write("fish-fries/index.html", fish_page())
    urls.append("fish-fries/")
    for k in KINDS:
        if k == "fish_fry" or not any(s["kind"] == k for s in SERIES):
            continue
        write(f"{KINDS[k]['path']}/index.html", kind_page(k))
        urls.append(f"{KINDS[k]['path']}/")
    for s in SERIES:
        write(f"events/{s['slug']}/index.html", series_page(s))
        urls.append(f"events/{s['slug']}/")
    for rec in EVENTS:
        write(f"e/{rec['slug']}/index.html", event_page(rec))
        urls.append(f"e/{rec['slug']}/")
    for c in COUNTIES:
        write(f"ohio/{county_slug(c)}/index.html", county_hub(c))
        urls.append(f"ohio/{county_slug(c)}/")
    write("organizers/index.html", organizers_index())
    urls.append("organizers/")
    for t in ORG_TYPES:
        if any(o["type"] == t for o in ORGS):
            write(f"organizers/{ORG_TYPES[t]['path']}/index.html", org_type_page(t))
            urls.append(f"organizers/{ORG_TYPES[t]['path']}/")
    write("add/index.html", add_page())
    write("about/index.html", about_page())
    write("data/index.html", data_page())
    urls += ["add/", "about/", "data/"]
    write("404.html", not_found())
    for name, data in (("events", EVENTS), ("series", SERIES), ("organizers", ORGS)):
        write(f"data/{name}.json", json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    shutil.copy(ROOT / "data" / "ohio-zips.json", DOCS / "data" / "ohio-zips.json")
    write("data/events.csv", to_csv(
        [[x["slug"], x["name"], x["type"], x["host"]["name"], x["host"]["kind"], x["host"].get("phone", ""),
          x["venue"]["address"], x["venue"]["city"], x["venue"].get("zip", ""), x["venue"]["county"], x["season"], " ".join(x["dates"]),
          x.get("start_time", ""), x.get("end_time", ""), x.get("price", ""), x.get("give_link", ""),
          "yes" if x.get("raffle") else "no", x["trust"], x["source"], x["source_url"], x["reviewed_on"]] for x in EVENTS],
        ["slug", "name", "type", "host", "host_kind", "phone", "address", "city", "zip", "county", "season",
         "dates", "start_time", "end_time", "price", "give_link", "raffle", "trust", "source", "source_url", "reviewed_on"]))
    write("data/series.csv", to_csv(
        [[s["slug"], s["name"], s["kind"], s["recurrence"], s["timing"], " ".join(s["next_dates"]), " ".join(s["last_dates"]),
          s["start_time"], s["end_time"], s["venue"]["name"], s["venue"]["address"], s["venue"]["city"], s["venue"]["county"],
          s["venue"]["zip"], s["organizer"].get("name", ""), s["organizer"].get("type", ""), s.get("organizer_slug") or "",
          s["website"], s["cost"], s["trust"], s["source"], s["source_url"], s["checked_on"]] for s in SERIES],
        ["slug", "name", "kind", "recurrence", "timing", "next_dates", "last_dates", "start_time", "end_time", "venue", "address",
         "city", "county", "zip", "organizer", "organizer_type", "organizer_slug", "website", "cost", "trust", "source", "source_url", "checked_on"]))
    write("data/organizers.csv", to_csv(
        [[o["slug"], o["name"], o["type"], o["number"], o["address"], o["city"], o["county"], o["zip"], o["phone"], o["website"],
          o["events_url"], "; ".join(o["hosts"]), o["trust"], o["source"], o["source_url"], o["checked_on"]] for o in ORGS],
        ["slug", "name", "type", "number", "address", "city", "county", "zip", "phone", "website", "events_url", "hosts",
         "trust", "source", "source_url", "checked_on"]))
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    sm = "".join(f"<url><loc>{e(BASE_URL + '/' + u)}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    write("urls.txt", "".join(f"{BASE_URL}/{u}\n" for u in urls))
    print(f"built {len(urls)} pages into docs/")


if __name__ == "__main__":
    main()
