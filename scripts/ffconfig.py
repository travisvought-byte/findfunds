"""Shared settings and helpers for the FindFundraisers.org build."""
import html
import re
from datetime import date

SITE_NAME = "FindFundraisers.org"
# The address the site will live at once the domain is bought and pointed here.
BASE_URL = "https://findfundraisers.org"
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
