"""Build the FindFundraisers.org static site into docs/ from data/events.json.

Usage: python3 scripts/build.py

The output is deterministic (no build date), so CI can rebuild and check that docs/ is current.
"""
import csv
import io
import json
import shutil
from pathlib import Path

import qrcode
import qrcode.image.svg

from ffconfig import (BASE_URL, CURRENT_SEASON, FIND_BINGO_OHIO, GIVING_TUESDAY, GOATCOUNTER,
                  ONLINE_RAFFLE_SALES_ALLOWED, SITE_NAME, SUBMIT_EMAIL, TYPES, VHG, county_slug, date_list, e,
                  is_current, long_date, phone_display, phone_href, time_range)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EVENTS = json.loads((ROOT / "data" / "events.json").read_text())
ZIPS = json.loads((ROOT / "data" / "ohio-zips.json").read_text())

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
    "share": '<circle cx="6" cy="12" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="6" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="18" cy="18" r="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6" stroke="currentColor" stroke-width="2"/>',
}


def icon(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


def up(depth):
    return "../" * depth if depth else "./"


def zip_point(rec):
    z = rec["venue"].get("zip")
    if z and z in ZIPS:
        return ZIPS[z], False
    # No ZIP: use the middle of the other listings in the same city, marked approximate.
    pts = [ZIPS[r["venue"]["zip"]] for r in EVENTS
           if r["venue"]["city"] == rec["venue"]["city"] and r["venue"].get("zip") in ZIPS]
    if pts:
        return [round(sum(p[0] for p in pts) / len(pts), 3), round(sum(p[1] for p in pts) / len(pts), 3)], True
    return None, True


def page(*, title, description, path, depth, body, jsonld=None, scripts=""):
    canonical = BASE_URL + "/" + path
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
    r = up(depth)
    return f"""<!doctype html>
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
<a class="brand" href="{r}">{icon("fish", "ic brand-ic")}<span>Find<b>Fundraisers</b>.org</span></a>
<nav aria-label="Main">
<ul>
<li><a href="{r}fish-fries/">Fish fries</a></li>
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
<script>window.goatcounter={{path:function(p){{return '/findfundraisers'+p}}}};</script>
<script data-goatcounter="{GOATCOUNTER}" async src="https://gc.zgo.at/count.js"></script>
{scripts}
</body>
</html>
"""


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


def home_page():
    fish = [x for x in EVENTS if x["type"] == "fish_fry"]
    types = "".join(
        f'<li><a href="{t["path"]}/" class="tile">{icon(t["icon"])}<span>{e(t["plural"])}</span></a></li>'
        for k, t in TYPES.items() if k == "fish_fry")
    body = f"""<section class="hero">
<div class="wrap">
<h1>Fish fries, breakfasts and benefit dinners near you</h1>
<p class="lead">A free Ohio list of community fundraisers at Legion and VFW halls, parishes, fire departments and clubs. Every gift goes straight to the group.</p>
<ul class="tiles">{types}<li><a href="add/" class="tile add">{icon("calendar")}<span>Add your event</span></a></li></ul>
</div>
</section>
<div class="wrap">
<section class="lent" aria-labelledby="lent-h">
<h2 id="lent-h">{icon("fish")}<span>Lenten fish fries</span></h2>
<p>Lent 2027 starts on Ash Wednesday, February 10. Parishes and posts usually post their fish fry dates in January. Until then, each listing shows last year's schedule so you know who holds one.</p>
</section>
{finder_box(0)}
{listing_section(fish, 0, "h3")}
</div>"""
    return page(title=f"Find a fish fry or community fundraiser in Ohio | {SITE_NAME}",
                description="Free list of Ohio fish fries, pancake breakfasts, euchre nights and benefit dinners, by ZIP code. Every gift goes straight to the group.",
                path="", depth=0, body=body, scripts=finder_script(0),
                jsonld={"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": BASE_URL + "/",
                        "publisher": {"@type": "Organization", "name": "Veteran Home Guardians", "url": VHG}})


def type_page(type_key):
    t = TYPES[type_key]
    recs = [x for x in EVENTS if x["type"] == type_key]
    body = f"""<div class="wrap">
<h1>{icon(t['icon'])}<span>Ohio {e(t['plural'].lower())}</span></h1>
<p class="lead">Lent 2027 runs from Ash Wednesday, February 10, to Easter, March 28. Most fish fries are on Fridays. Listings showing 2026 dates are last year's schedule; call before you go.</p>
{finder_box(1)}
{listing_section(recs, 1)}
</div>"""
    return page(title=f"Ohio {t['plural'].lower()} near you, Lent 2027 | {SITE_NAME}",
                description=f"Find Ohio {t['plural'].lower()} by ZIP code: parish, Legion, VFW and fire department fish fries with dates, times and phone numbers.",
                path=f"{t['path']}/", depth=1, body=body, scripts=finder_script(1))


def county_page(county, recs):
    body = f"""<div class="wrap">
<p class="crumbs"><a href="../../">Home</a> › {e(county)} County</p>
<h1>Fish fries and fundraisers in {e(county)} County, Ohio</h1>
<p class="lead">Community fish fries, breakfasts and benefit dinners in {e(county)} County. Listings showing 2026 dates are last year's schedule; call before you go.</p>
<ul class="cards">{''.join(card(x, 2) for x in sorted(recs, key=lambda x: (x['venue']['city'], x['name'])))}</ul>
<p>Don't see your event? <a href="../../add/">Add it for free</a>.</p>
</div>"""
    return page(title=f"{county} County, Ohio fish fries and fundraisers | {SITE_NAME}",
                description=f"Fish fries, breakfasts and benefit dinners in {county} County, Ohio, with dates, times and phone numbers.",
                path=f"ohio/{county_slug(county)}/", depth=2, body=body)


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
<p class="lead">{SITE_NAME} lists community fundraisers so people can find them, and so the groups that run them get a simple page and flyer without paying anyone.</p>
<h2>How listings work</h2>
<ul>
<li>Anyone can send an event. We check each one before it goes up.</li>
<li>Some listings start from public lists, such as a diocese's fish fry page. Those say where they came from and ask you to call first until the organizer confirms them.</li>
<li>Organizers can send new dates or corrections any time from their event's page.</li>
</ul>
<h2>Money</h2>
<p>We never collect or hold money for anyone. A page links to the group's own way to give, or says to bring cash. Ohio allows raffle and 50/50 tickets to be sold in person only, so we never link to online raffle ticket sales.</p>
<h2>Open data</h2>
<p>The full list is free to reuse under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. See <a href="../data/">the data page</a>.</p>
<h2 id="privacy">Privacy</h2>
<p>We count visits with GoatCounter, which uses no cookies and doesn't store your IP address. The site is hosted on GitHub Pages, which may keep server logs for security. Contact details you send with an event are used only to check it and are never published.</p>
<h2>Who runs it</h2>
<p>{SITE_NAME} is a free community service of <a href="{VHG}">Veteran Home Guardians</a>, an Ohio 501(c)(3) that places veteran visitors in long-term care facilities. It is a sister site of <a href="https://www.findbingo.org/">FindBingo.org</a>.</p>
</div>"""
    return page(title=f"About {SITE_NAME}", description="How FindFundraisers.org lists Ohio community fundraisers, handles data and protects privacy.",
                path="about/", depth=1, body=body)


def data_page():
    body = f"""<div class="wrap narrow prose">
<h1>Open data</h1>
<p class="lead">Every listing is free to reuse under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Please credit "{SITE_NAME}, a service of Veteran Home Guardians".</p>
<ul>
<li><a href="events.json">events.json</a>: every listing, with host, venue, dates, times, source and trust level.</li>
<li><a href="events.csv">events.csv</a>: the same list as a spreadsheet, one row per listing.</li>
</ul>
<p>Each event page also carries schema.org Event markup for its upcoming dates. Fields follow schema.org Event names where they exist; "trust" is "public_list" (from someone else's list, not yet confirmed), "organizer" (confirmed by the organizer) or "claimed" (kept up to date by the organizer).</p>
</div>"""
    return page(title=f"Open data | {SITE_NAME}", description="Download the FindFundraisers.org list of Ohio community fundraisers as JSON or CSV, free under CC BY 4.0.",
                path="data/", depth=1, body=body)


def not_found():
    body = """<div class="wrap narrow"><h1>We couldn't find that page</h1><p>The event may have moved. <a href="/">Search all events</a> or <a href="/add/">tell us what you were looking for</a>.</p></div>"""
    return page(title=f"Page not found | {SITE_NAME}", description="Page not found.", path="404.html", depth=0, body=body)


def write(rel, text):
    p = DOCS / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    shutil.copytree(ROOT / "assets", DOCS / "assets")
    (DOCS / ".nojekyll").write_text("")
    urls = [""]
    write("index.html", home_page())
    for k in sorted({x["type"] for x in EVENTS}):
        write(f"{TYPES[k]['path']}/index.html", type_page(k))
        urls.append(f"{TYPES[k]['path']}/")
    counties = {}
    for rec in EVENTS:
        counties.setdefault(rec["venue"]["county"], []).append(rec)
        write(f"e/{rec['slug']}/index.html", event_page(rec))
        urls.append(f"e/{rec['slug']}/")
    for c, recs in sorted(counties.items()):
        write(f"ohio/{county_slug(c)}/index.html", county_page(c, recs))
        urls.append(f"ohio/{county_slug(c)}/")
    write("add/index.html", add_page())
    write("about/index.html", about_page())
    write("data/index.html", data_page())
    urls += ["add/", "about/", "data/"]
    write("404.html", not_found())
    write("data/events.json", json.dumps(EVENTS, indent=1, ensure_ascii=False) + "\n")
    shutil.copy(ROOT / "data" / "ohio-zips.json", DOCS / "data" / "ohio-zips.json")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["slug", "name", "type", "host", "host_kind", "phone", "address", "city", "zip", "county", "season",
                "dates", "start_time", "end_time", "price", "give_link", "raffle", "trust", "source", "source_url", "reviewed_on"])
    for x in EVENTS:
        v = x["venue"]
        w.writerow([x["slug"], x["name"], x["type"], x["host"]["name"], x["host"]["kind"], x["host"].get("phone", ""),
                    v["address"], v["city"], v.get("zip", ""), v["county"], x["season"], " ".join(x["dates"]),
                    x.get("start_time", ""), x.get("end_time", ""), x.get("price", ""), x.get("give_link", ""),
                    "yes" if x.get("raffle") else "no", x["trust"], x["source"], x["source_url"], x["reviewed_on"]])
    write("data/events.csv", buf.getvalue())
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    sm = "".join(f"<url><loc>{e(BASE_URL + '/' + u)}</loc></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    print(f"built {len(urls)} pages into docs/")


if __name__ == "__main__":
    main()
