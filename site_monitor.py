import hashlib, json, re, time
from contextlib import contextmanager
from pathlib import Path

import httpx
from bs4 import BeautifulSoup as bs

# --- Settings: change these for the page you want to watch ---
URL = "https://example.com/portfolio"
TS = re.compile(rb"<!-- Last Published: ([^>]+?) -->")  # timestamp near the top of the page
CACHE = Path("cache.json")

ITEM = ".card"           # one element per item
TITLE = "h3"             # item name
DESC = ".description"    # item description
LINK = "a"               # item link
TAG = "data-tag"         # attribute holding tags

client = httpx.Client(timeout=10, follow_redirects=True)


def parse_cards(soup):
    items = []
    for card in soup.select(ITEM):
        title = card.select_one(TITLE)
        desc = card.select_one(DESC)
        link = card.select_one(LINK)
        items.append({
            "name": title.get_text(strip=True) if title else None,
            "link": link.get("href") if link else None,
            "desc": " ".join(desc.get_text(" ").split()) if desc else None,
            "tags": sorted(t[TAG] for t in card.select(f"[{TAG}]")),
        })
    return items


@contextmanager
def timer(label):
    t0 = time.perf_counter()
    yield
    print(f"{label:<12} {(time.perf_counter() - t0) * 1000:7.1f} ms")


def load_cache():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, indent=2))


def get_stamp(headers=None):
    with client.stream("GET", URL, headers=headers or {}) as r:
        buf = b""
        for chunk in r.iter_bytes(512):
            buf += chunk
            if m := TS.search(buf):
                return m.group(1).decode()
            if len(buf) > 4096:
                break
    return None


def content_hash(html):
    """Hash the meaningful content, not the raw page."""
    soup = bs(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    target = soup.body or soup
    text = " ".join(target.get_text(" ").split())  # collapse whitespace
    return hashlib.sha256(text.encode()).hexdigest()


def check(force=False):
    cache = load_cache()

    with timer("stamp"):
        stamp = get_stamp()
    if not force and (stamp is None or stamp == cache.get("stamp")):
        return False

    with timer("full fetch"):
        html = client.get(URL).text
    with timer("hash"):
        h = content_hash(html)

    changed = h != cache.get("hash")
    save_cache({"stamp": stamp, "hash": h})
    return changed


if __name__ == "__main__":
    print("changed" if check() else "no change")
