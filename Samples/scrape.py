"""Pulls free-sample posts from RSS feeds into data/samples.json (stdlib only).
Add or remove sources in FEEDS. Any WordPress-style blog works at <site>/feed/."""
import json, re, html, urllib.request as U, xml.etree.ElementTree as ET
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

FEEDS = {  # edit me: name -> feed URL
    "smartcanucks.ca": "https://smartcanucks.ca/category/canadian-freebies-free-stuff-canada/feed/",
    "hotcanadadeals.ca": "https://hotcanadadeals.ca/feed/",
    "smartcanucks.ca (all)": "https://feeds2.feedburner.com/smartcanucks",
}
WANT = re.compile(r"free|sample", re.I)
SKIP = re.compile(r"contest|giveaway|sweepstake|\bwin\b|expired|ended", re.I)
C = "{http://purl.org/rss/1.0/modules/content/}encoded"
OUT = "data/samples.json"

def fetch(url):
    req = U.Request(url, headers={"User-Agent": "Mozilla/5.0 sample-finder"})
    return U.urlopen(req, timeout=25).read()

def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def form_link(body, post):
    host = urlparse(post).netloc
    for h in re.findall(r'href="(https?://[^"]+)"', body or ""):
        if urlparse(h).netloc != host and not re.search(r"facebook|twitter|pinterest|instagram|wp\.com", h):
            return h
    return post

try: items = {i["id"]: i for i in json.load(open(OUT))}
except Exception: items = {}

for src, url in FEEDS.items():
    try:
        for it in ET.fromstring(fetch(url)).iter("item"):
            t, link = clean(it.findtext("title")), (it.findtext("link") or "").strip()
            body = it.findtext(C) or it.findtext("description") or ""
            if not link or not WANT.search(t) or SKIP.search(t): continue
            items[link] = {"id": link, "title": t, "source": src, "url": link,
                           "form": form_link(body, link), "summary": clean(body)[:220],
                           "date": it.findtext("pubDate") or ""}
    except Exception as e:
        print("failed", src, e)

cut = datetime.now(timezone.utc) - timedelta(days=60)
def fresh(i):
    try: return datetime.strptime(i["date"][:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc) > cut
    except Exception: return True
out = sorted(filter(fresh, items.values()), key=lambda i: i["date"], reverse=True)
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
print(len(out), "samples")
