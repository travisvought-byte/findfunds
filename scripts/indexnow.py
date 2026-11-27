"""Send changed page URLs to IndexNow (Bing, Yandex and others share it).

Usage: python3 scripts/indexnow.py changed.txt
changed.txt holds paths under docs/ such as "events/some-fair/", one per line.
"""
import json
import sys
import urllib.request

from ffconfig import BASE_URL, INDEXNOW_KEY

paths = [p for p in open(sys.argv[1]).read().split() if p]
urls = [f"{BASE_URL}/{p}" for p in paths][:10000]
if not urls:
    print("no changed pages")
    sys.exit(0)
body = json.dumps({"host": BASE_URL.split("/")[2], "key": INDEXNOW_KEY,
                   "keyLocation": f"{BASE_URL}/{INDEXNOW_KEY}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.status, len(urls), "urls sent")
