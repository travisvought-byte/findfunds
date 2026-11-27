# Operational plan: mapping community events, organizers and partners

## The problem

People lack community and connection. The events that build it (fairs, festivals, fish fries, pancake breakfasts, euchre nights, parades, library and park programs, post and lodge dinners) happen every week in every county, but the information about them is scattered across hundreds of small websites, Facebook pages, church bulletins and paper flyers. Nobody can answer the simple question: what is happening near me, who runs it, and how do I get involved?

## The mission of this directory

Identify every community event and the group behind it, map them, keep them current, and make them readily apparent to anyone who asks "where is the information I need?"

## Information needed to solve it

| Question a person asks | Information required | Record |
|---|---|---|
| What is happening near me, and when? | Event name, kind, dates or recurrence, times, place, county | Event, Series |
| Can I go? Can I afford it? Can I get in? | Cost to attend, accessibility, parking, who it is for | Event |
| Who runs it, and how do I reach them? | Organizer name, type, address, phone, website, events page | Organizer |
| Where is it held? | Venue name, address, county, ZIP, accessibility | Venue |
| How do I help or get involved? | Volunteer, donate, membership, vendor contact | Organizer |
| Is this still true? | Source, source link, date last checked, trust level | Every record |

## Where the information lives

| Source | What it gives | Reliability | How we use it |
|---|---|---|---|
| Ohio Department of Agriculture fair schedule | Every county and independent fair, dates, fair board | Official | Events and organizers, yearly |
| Festival associations and state tourism | Annual festivals with month and town | Good, then check the festival's own site | Series |
| Diocesan and parish lists | Lenten fish fries, parish festivals | Good, then check the parish page | Events, organizers |
| American Legion, VFW, AMVETS, Elks, Eagles, Moose locators | Every post and lodge, address, phone | Official rosters | Organizers |
| State Library of Ohio directory | Every public library system and its events calendar | Official | Organizers, calendar links |
| Park districts and state parks | Programs and seasonal events | Official | Organizers, calendar links |
| Chambers of commerce and visitors bureaus | Community calendars by county | Good | Organizers, calendar links, series |
| Organizer websites and calendars | Dates, times, cost | Best (first-hand) | Verification |
| Public listings (Eventbrite, Meetup) and the Meta Ad Library | Events promoted online | Mixed | Leads only, verified before listing |
| Organizers themselves (submission form, claim) | Corrections and new events | Best once claimed | Updates |

## Gaps

- Most small events (post dinners, breakfasts, benefits) are posted only on Facebook or paper flyers. Closing this gap takes organizer outreach and a free submission and claim process.
- Many organizer sites post dates late. Recurring series fill the gap: a fair held the third week of July every year is still useful before this year's dates are posted.
- Fire departments, schools and smaller nonprofits have no statewide roster with event pages.

## Trust levels

- **official_list**: from a statewide or official roster (state agency, diocese, department headquarters).
- **organizer_page**: checked against the organizer's own site.
- **organizer**: sent in by the organizer.
- **claimed**: the organizer verified and manages the listing.

Every record carries `source`, `source_url` and `checked_on`. Records older than 180 days are flagged for recheck by the refresh workflow.

## Partner fit (internal)

Organizers are scored as potential partners for Veteran Home Guardians in a private list that is not published here. No partner is named on the site until they have accepted.

## Related sites

- Bingo: Find Bingo (findbingo.org).
- Vendors for events: Vendor Maps.
- Veteran services and events: the Veteran Home Guardians resource guide.

## Rollout

1. Ohio: organizers by type and county, fairs, festivals, Lenten fish fries.
2. Refresh: weekly link and staleness check, yearly date roll-over for recurring series.
3. Next states, chosen by how much open, structured event data they publish.
