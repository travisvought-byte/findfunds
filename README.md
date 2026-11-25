# FindFundraisers.org

A free directory of Ohio community fundraisers: fish fries, pancake breakfasts, benefit dinners, euchre nights and raffles. Every event gets its own page and link that the group can share, plus a printable flyer with a QR code.

The site is static. A Python script turns `data/events.json` into plain HTML in `docs/`, which GitHub Pages serves.

## Build it

```
pip install qrcode==8.2
python3 scripts/build.py
python3 scripts/check.py
```

`check.py` validates the data and every page: one `h1`, a skip link, labeled form fields, icons hidden from screen readers or labeled, valid JSON-LD, no broken internal links, and no online raffle ticket links (not legal in Ohio).

## Add or update events

- `seed/` holds source lists as CSV. `scripts/import_seed.py` turns a seed CSV into records in `data/events.json`.
- Each record has a `trust` level: `public_list` (taken from a public list, not yet confirmed), `organizer` (sent in by the group) or `claimed` (the group verified its page).
- Last season's records stay on the site, clearly labeled with their year. Only current-season dates (`CURRENT_SEASON` in `scripts/ffconfig.py`) get schema.org Event markup.

## Point the domain

1. Buy `findfundraisers.org`.
2. In the repo's Settings > Pages, serve from the `main` branch, `/docs` folder.
3. Add a `docs/CNAME` file containing `findfundraisers.org` (have `build.py` write it so rebuilds keep it), and add the DNS records GitHub Pages lists.
4. Turn on Enforce HTTPS once the certificate is issued.

Until then the pages use absolute links to `https://findfundraisers.org`, so a few links only work once the domain points here.

## License

Code: MIT. Event data (`data/events.json`, `docs/events.json`, `docs/events.csv`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` and `DATA-LICENSE.md`.

A project of Veteran Home Guardians. Sister site: Find Bingo Ohio.
