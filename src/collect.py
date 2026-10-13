"""
TechEngage Social Post Engagement Analysis - Data Collection
=============================================================
Source: Hacker News public API (https://github.com/HackerNews/API)
- Fully public, no authentication required, no API key.
- Endpoint docs: https://hacker-news.firebaseio.com/v0/

Collection method (2026-10-14):
1. GET /v0/topstories.json -> 500 current top story IDs
2. GET /v0/beststories.json -> 500 best story IDs (dedupe against top)
3. GET /v0/item/<id>.json for each unique ID (concurrent, 20 workers)
4. Keep only type == "story" (drops jobs/polls), keep raw fields.

Concurrency: ThreadPoolExecutor(20). HN's Firebase API tolerates this volume;
3 retries with backoff on transient failures.

Output: data/raw/hn_stories_raw.json
Each record: id, title, url, score, descendants, time, type, by
(collected_at timestamp added for provenance)
"""
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

BASE = "https://hacker-news.firebaseio.com/v0"
OUT = "/home/hatch/workspace/goals/techengage-social-post-engagement-analysis-10-pts-due-20-oct/hidden_files/data/raw/hn_stories_raw.json"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
WORKERS = 20


def get(path, retries=3):
    url = BASE + path
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            time.sleep(1 + attempt * 2)
    return None


def fetch_story(sid):
    item = get(f"/item/{sid}.json")
    if not item or item.get("type") != "story":
        return None
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "url": item.get("url"),
        "score": item.get("score"),
        "descendants": item.get("descendants"),
        "time": item.get("time"),
        "type": item.get("type"),
        "by": item.get("by"),
    }


def main():
    top = get("/topstories.json") or []
    best = get("/beststories.json") or []
    print(f"topstories: {len(top)}, beststories: {len(best)}", flush=True)
    ids = list(dict.fromkeys(top + best))
    print(f"unique ids: {len(ids)}", flush=True)

    stories = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, s in enumerate(ex.map(fetch_story, ids)):
            if s:
                stories.append(s)
            if (i + 1) % 100 == 0:
                print(f"  fetched {i + 1}/{len(ids)}", flush=True)

    payload = {
        "source": "Hacker News public API (https://hacker-news.firebaseio.com/v0/)",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "endpoints": ["/topstories.json", "/beststories.json", "/item/<id>.json"],
        "workers": WORKERS,
        "n_stories": len(stories),
        "stories": stories,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f)
    print(f"saved {len(stories)} stories -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
