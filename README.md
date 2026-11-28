# Ohio Community Events

A free map of Ohio community life: county fairs, festivals, fish fries, parades, holiday events and dinners, and the veterans posts, parishes, fire departments, libraries, park districts, fair boards, chambers and visitors bureaus that run them. Every event and every county gets its own page.

Live at https://www.vethomeguard.org/fundraisers/. The name is a working title. GitHub Pages also serves the same build at https://travisvought-byte.github.io/findfunds/, where every page names the vethomeguard.org address as its canonical, and the full data downloads live there.

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

## Publish to vethomeguard.org/fundraisers

vethomeguard.org is a Wix headless site that serves the files in the `travisvought-byte/vethomeguard` repository. This site lives in its `fundraisers/` folder.

1. Merge the change here. CI rebuilds `docs/` and checks it.
2. In the vethomeguard repository, replace `fundraisers/` with a fresh copy of `docs/`, leaving out `.nojekyll`, `urls.txt` and the six download files in `data/` (all but `data/index.html` and `data/ohio-zips.json`):
   `python3 scripts/sync_to_vhg.py ../vethomeguard` does this.
3. Open a pull request there, merge it, and run its "Publish to Wix" workflow in publish mode.

Wix caps a whole site at 20 MiB. The vethomeguard copy of this site is about 14 MiB, so keep an eye on it as listings grow: `sync_to_vhg.py` prints the size and stops above 17 MiB.

## License

Code: MIT. Data (`data/*.json`, `docs/data/*`): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE` and `DATA-LICENSE.md`.

A project of Veteran Home Guardians. Sister site: Find Bingo Ohio.
