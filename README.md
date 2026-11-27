# Ohio Community Events

A free map of Ohio community life: county fairs, festivals, fish fries, parades, holiday events and dinners, and the veterans posts, parishes, fire departments, libraries, park districts, fair boards, chambers and visitors bureaus that run them. Every event and every county gets its own page.

Live at https://travisvought-byte.github.io/findfunds/ until a domain is chosen. The name is a working title.

See [OPERATIONS.md](OPERATIONS.md) for the operational plan (the problem, the information needed, where it lives, the gaps) and [DATA-MODEL.md](DATA-MODEL.md) for the records.

## How it fits together

- `seed/` holds source lists as CSV. `seed/directory/` holds the mined Ohio rosters and event calendars (organizers and recurring events), each row with its source link and the date it was checked.
- `scripts/import_directory.py` dedupes those CSVs into `data/organizers.json` and `data/series.json` and links each event to its organizer.
- `data/events.json` holds dated fish fry listings with printable QR flyers (`scripts/import_seed.py`).
- `scripts/build.py` turns the JSON into static HTML in `docs/`, which GitHub Pages serves: a search page by county, month, kind and name; a page per event; a hub per county; and organizer lists by type.
- `scripts/check.py` validates the data and every page: one `h1`, a skip link, labeled form fields, icons hidden from screen readers, valid JSON-LD, no broken internal links, no stated listing counts, and no online raffle ticket links (not legal in Ohio).

## Build it

```
pip install qrcode==8.2
cd scripts && python3 import_directory.py && cd ..
python3 scripts/build.py
python3 scripts/check.py
```

CI rebuilds on every push and fails if `docs/` doesn't match the data.

## Keeping it current

- `.github/workflows/health.yml` runs every Monday: it flags records not rechecked in 180 days and samples source and website links for dead ones, posting the report to a "Data health report" issue.
- On pushes to `main`, the build workflow sends changed page URLs to IndexNow once the site responds.
- Only dates posted for the coming season get schema.org Event markup. Last year's dates stay visible and are labeled as last year's.
- Partners are never named on the site until they accept. Partner ranking lives outside this repo.

## Point a domain

1. Buy the domain.
2. Set `FF_BASE_URL` (or `BASE_URL` in `scripts/ffconfig.py`) to it, and have `build.py` write `docs/CNAME`.
3. Add the DNS records GitHub Pages lists, then turn on Enforce HTTPS.

## License

Code: MIT. Data (`data/*.json`, `docs/data/*`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` and `DATA-LICENSE.md`.

A project of Veteran Home Guardians. Sister site: Find Bingo Ohio.
