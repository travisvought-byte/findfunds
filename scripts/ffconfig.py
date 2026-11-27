"""Shared settings and helpers for the Ohio community events directory build."""
import os
import html
import re
from datetime import date

# Working name until a domain is chosen. Change SITE_NAME, BRAND_HTML and BASE_URL together.
SITE_NAME = "Ohio Community Events"
BRAND_HTML = "Ohio <b>Community Events</b>"
# Where the site is served. GitHub Pages' default address until a domain is pointed here.
BASE_URL = os.environ.get("FF_BASE_URL", "https://travisvought-byte.github.io/findfunds")
GOATCOUNTER_PREFIX = "/findfunds"
# IndexNow key; the matching key file is written to docs/<key>.txt.
INDEXNOW_KEY = "6f1c2b9e4a7d43c58e0b1f2a9c3d7e51"
# Records whose season matches this are current; any other season is shown as last year's schedule.
CURRENT_SEASON = "Lent 2027"
ASH_WEDNESDAY = "2027-02-10"
SUBMIT_EMAIL = "travis@vethomeguard.org"
GOATCOUNTER = "https://vhg-guide.goatcounter.com/count"
GIVING_TUESDAY = "https://www.zeffy.com/en-US/donation-form/giving-tuesday-no-veteran-left-isolated"
VHG = "https://www.vethomeguard.org/"
FIND_BINGO_OHIO = "https://www.findbingo.org/ohio/"
# Ohio law allows raffle tickets to be sold in person only (HB 476 would change this; not law as of Nov 2026).
ONLINE_RAFFLE_SALES_ALLOWED = False

TYPES = {
    "fish_fry": {"label": "Fish fry", "plural": "Fish fries", "icon": "fish", "path": "fish-fries"},
    "breakfast": {"label": "Breakfast", "plural": "Breakfasts", "icon": "pancakes", "path": "breakfasts"},
    "benefit_dinner": {"label": "Benefit dinner", "plural": "Benefit dinners", "icon": "plate", "path": "benefit-dinners"},
    "cards": {"label": "Euchre and cards", "plural": "Euchre and card nights", "icon": "cards", "path": "euchre"},
    "benefit_person": {"label": "Benefit for a neighbor", "plural": "Benefits for neighbors", "icon": "heart", "path": "benefits"},
    "raffle": {"label": "Raffle or 50/50", "plural": "Raffles and 50/50s", "icon": "ticket", "path": "raffles"},
    "other": {"label": "Community event", "plural": "Other community events", "icon": "calendar", "path": "other"},
}

# Kinds of recurring community events (data/series.json).
KINDS = {
    "fair": {"label": "County fair", "plural": "County and independent fairs", "icon": "flag", "path": "fairs"},
    "festival": {"label": "Festival", "plural": "Festivals", "icon": "star", "path": "festivals"},
    "fish_fry": {"label": "Fish fry", "plural": "Fish fries", "icon": "fish", "path": "fish-fries"},
    "holiday": {"label": "Holiday event", "plural": "Holiday events", "icon": "gift", "path": "holiday-events"},
    "breakfast": {"label": "Breakfast", "plural": "Breakfasts", "icon": "pancakes", "path": "breakfasts"},
    "benefit_dinner": {"label": "Benefit dinner", "plural": "Benefit dinners", "icon": "plate", "path": "benefit-dinners"},
    "cards": {"label": "Euchre and cards", "plural": "Euchre and card nights", "icon": "cards", "path": "euchre"},
    "raffle": {"label": "Raffle", "plural": "Raffles", "icon": "ticket", "path": "raffles"},
    "parade": {"label": "Parade", "plural": "Parades", "icon": "flag", "path": "parades"},
    "market": {"label": "Market", "plural": "Markets and flea markets", "icon": "basket", "path": "markets"},
    "concert": {"label": "Concert", "plural": "Concerts", "icon": "music", "path": "concerts"},
    "car_show": {"label": "Car show", "plural": "Car shows", "icon": "car", "path": "car-shows"},
    "run_walk": {"label": "Run or walk", "plural": "Runs and walks", "icon": "run", "path": "runs-and-walks"},
    "library_program": {"label": "Library program", "plural": "Library programs", "icon": "book", "path": "library-programs"},
    "park_program": {"label": "Park program", "plural": "Park programs", "icon": "tree", "path": "park-programs"},
    "other": {"label": "Community event", "plural": "Other community events", "icon": "calendar", "path": "other-events"},
}

# Groups that run community events (data/organizers.json), in the order shown.
ORG_TYPES = {
    "legion": {"label": "American Legion post", "plural": "American Legion posts", "icon": "flag", "path": "american-legion"},
    "vfw": {"label": "VFW post", "plural": "VFW posts", "icon": "flag", "path": "vfw"},
    "amvets": {"label": "AMVETS post", "plural": "AMVETS posts", "icon": "flag", "path": "amvets"},
    "elks": {"label": "Elks lodge", "plural": "Elks lodges", "icon": "users", "path": "elks"},
    "eagles": {"label": "Eagles aerie", "plural": "Eagles aeries", "icon": "users", "path": "eagles"},
    "moose": {"label": "Moose lodge", "plural": "Moose lodges", "icon": "users", "path": "moose"},
    "kofc": {"label": "Knights of Columbus council", "plural": "Knights of Columbus councils", "icon": "users", "path": "knights-of-columbus"},
    "lions": {"label": "Lions Club", "plural": "Lions Clubs", "icon": "users", "path": "lions"},
    "rotary": {"label": "Rotary Club", "plural": "Rotary Clubs", "icon": "users", "path": "rotary"},
    "kiwanis": {"label": "Kiwanis Club", "plural": "Kiwanis Clubs", "icon": "users", "path": "kiwanis"},
    "parish": {"label": "Catholic parish", "plural": "Catholic parishes", "icon": "church", "path": "parishes"},
    "church": {"label": "Church", "plural": "Churches", "icon": "church", "path": "churches"},
    "fire_dept": {"label": "Fire department", "plural": "Fire departments", "icon": "fire", "path": "fire-departments"},
    "library": {"label": "Public library", "plural": "Public libraries", "icon": "book", "path": "libraries"},
    "park_district": {"label": "Park district", "plural": "Park districts", "icon": "tree", "path": "park-districts"},
    "state_park": {"label": "State parks", "plural": "State parks", "icon": "tree", "path": "state-parks"},
    "fair_board": {"label": "Fair board", "plural": "Fair boards (agricultural societies)", "icon": "flag", "path": "fair-boards"},
    "chamber": {"label": "Chamber of commerce", "plural": "Chambers of commerce", "icon": "building", "path": "chambers"},
    "cvb": {"label": "Visitors bureau", "plural": "Visitors bureaus and tourism offices", "icon": "building", "path": "visitors-bureaus"},
    "festival_committee": {"label": "Festival committee", "plural": "Festival committees", "icon": "star", "path": "festival-committees"},
    "historical_society": {"label": "Historical society", "plural": "Historical societies", "icon": "book", "path": "historical-societies"},
    "school": {"label": "School", "plural": "Schools", "icon": "building", "path": "schools"},
    "nonprofit": {"label": "Nonprofit", "plural": "Nonprofits", "icon": "heart", "path": "nonprofits"},
    "government": {"label": "Local government", "plural": "Local governments", "icon": "building", "path": "local-government"},
    "other": {"label": "Community group", "plural": "Other community groups", "icon": "users", "path": "other-groups"},
}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

e = html.escape


def slugify(text):
    text = text.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def clock(hhmm):
    """'16:30' -> ('4:30', 'p.m.')"""
    h, m = (int(x) for x in hhmm.split(":"))
    suffix = "a.m." if h < 12 else "p.m."
    h12 = h % 12 or 12
    return (f"{h12}" if m == 0 else f"{h12}:{m:02d}"), suffix


def time_range(start, end):
    if not start:
        return ""
    s, s_sfx = clock(start)
    if not end:
        return f"{s} {s_sfx}"
    t, t_sfx = clock(end)
    if s_sfx == t_sfx:
        return f"{s} to {t} {t_sfx}"
    return f"{s} {s_sfx} to {t} {t_sfx}"


def date_list(dates):
    """['2026-02-20','2026-02-27','2026-03-06'] -> 'Feb 20 and 27, Mar 6, 2026'"""
    if not dates:
        return ""
    by_month = {}
    for d in dates:
        y, m, dd = d.split("-")
        by_month.setdefault((y, int(m)), []).append(str(int(dd)))
    parts = []
    for (y, m), days in by_month.items():
        days_text = days[0] if len(days) == 1 else ", ".join(days[:-1]) + " and " + days[-1]
        parts.append(f"{MONTHS[m - 1]} {days_text}")
    year = dates[-1][:4]
    return "; ".join(parts) + f", {year}"


def date_span(dates):
    """First-to-last span for multi-day events: 'July 10 to 12, 2026'."""
    if not dates:
        return ""
    a, b = dates[0], dates[-1]
    ya, ma, da = a.split("-")
    yb, mb, db = b.split("-")
    if a == b:
        return long_date(a)
    if ma == mb and ya == yb:
        return f"{MONTHS_LONG[int(ma) - 1]} {int(da)} to {int(db)}, {ya}"
    if ya == yb:
        return f"{MONTHS_LONG[int(ma) - 1]} {int(da)} to {MONTHS_LONG[int(mb) - 1]} {int(db)}, {ya}"
    return f"{long_date(a)} to {long_date(b)}"


def long_date(d):
    y, m, dd = d.split("-")
    return f"{MONTHS_LONG[int(m) - 1]} {int(dd)}, {y}"


def weekday(d):
    return WEEKDAYS[date.fromisoformat(d).weekday()]


def phone_display(p):
    digits = re.sub(r"\D", "", p or "")
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return p or ""


def phone_href(p):
    digits = re.sub(r"\D", "", p or "")
    return f"tel:+1{digits}" if len(digits) == 10 else ""


def is_current(rec):
    return rec.get("season") == CURRENT_SEASON


def county_slug(county):
    return slugify(county) + "-county"
