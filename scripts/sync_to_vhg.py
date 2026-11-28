#!/usr/bin/env python3
"""Copy the built site (docs/) into the vethomeguard repository's fundraisers/ folder.

    python3 scripts/sync_to_vhg.py ../vethomeguard

Wix serves that repository at www.vethomeguard.org and caps the whole site at 20 MiB, so the large data
downloads stay on the GitHub Pages copy (see DOWNLOADS_URL in ffconfig.py) and are left out here.
"""
import shutil
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"
LEAVE_OUT = {".nojekyll", "urls.txt", "data/series.json", "data/series.csv", "data/organizers.json",
             "data/organizers.csv", "data/events.json", "data/events.csv"}
LIMIT_MIB = 17


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    target = Path(argv[0]).resolve() / "fundraisers"
    files = [p for p in sorted(DOCS.rglob("*")) if p.is_file() and p.relative_to(DOCS).as_posix() not in LEAVE_OUT]
    size = sum(p.stat().st_size for p in files) / 2**20
    print(f"{len(files)} files, {size:.1f} MiB")
    if size > LIMIT_MIB:
        sys.exit(f"Stopped: over {LIMIT_MIB} MiB. Wix caps the whole vethomeguard.org site at 20 MiB.")
    if target.exists():
        shutil.rmtree(target)
    for p in files:
        out = target / p.relative_to(DOCS)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
    print(f"Copied into {target}")


if __name__ == "__main__":
    main(sys.argv[1:])
