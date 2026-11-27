# Data model

All data lives in `data/` as JSON and is published as open data (CC BY 4.0).

## Organizer (`data/organizers.json`)

A group that runs events.

| Field | Notes |
|---|---|
| id, slug | stable identifiers |
| name | as the group writes it |
| type | parish, church, legion, vfw, amvets, elks, eagles, moose, kofc, lions, rotary, kiwanis, fire_dept, library, park_district, state_park, chamber, cvb, fair_board, festival_committee, historical_society, school, nonprofit, government, other |
| number | post, lodge, aerie or council number |
| address, city, county, state, zip | mailing or meeting place |
| phone, website, events_url | public contact points only |
| hosts | kinds of events it usually runs |
| source, source_url, checked_on, trust | provenance |

## Series (`data/series.json`)

An event that repeats: an annual fair, a festival, Friday fish fries in Lent, a monthly euchre night.

| Field | Notes |
|---|---|
| id, slug, name, kind | kind: fair, festival, fish_fry, breakfast, benefit_dinner, cards, raffle, parade, market, concert, car_show, run_walk, holiday, library_program, park_program, other |
| recurrence, timing | annual, weekly, monthly, seasonal; timing in words ("third week of July") |
| next_dates | known dates for the coming season, ISO |
| last_dates | last known dates, shown as "last year" |
| venue (name, address, city, county, state, zip) | |
| organizer_id | links to Organizer |
| website | the event's own page |
| cost | free, paid, varies, unknown |
| source, source_url, checked_on, trust | provenance |

## Event (`data/events.json`)

A dated occurrence with its own page, QR flyer and schema.org Event markup (current season only). Fish fries seeded from diocesan lists are Events today and will be grouped into Series.

## Venue

Embedded in Series and Event for now. Venues shared with Find Bingo are matched by address.

## Intake CSVs (`seed/`)

Research batches arrive as CSV with the same field names, plus `verified_on_organizer_site` (yes/no) and `notes`. `scripts/import_directory.py` turns them into the JSON above.
