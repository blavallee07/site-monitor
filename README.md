# site-monitor

A small Python script that checks whether a web page has changed, without downloading the whole page every time.

1. **Cheap check:** stream only the first ~4 KB of the page and look for a "last published" timestamp. If it matches the last run, stop.
2. **Full check:** if the timestamp changed, fetch the page, strip scripts and styles, and hash the visible text to confirm the content actually changed.

## Usage

```bash
pip install httpx beautifulsoup4 lxml
python site_monitor.py
```

Set `URL`, `TS` (the timestamp regex) and the item selectors at the top of `site_monitor.py` for the page you want to watch.
