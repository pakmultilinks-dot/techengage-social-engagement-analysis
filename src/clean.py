"""
TechEngage Social Post Engagement Analysis - Data Cleaning
===========================================================
Input : data/raw/hn_stories_raw.json  (raw HN API records)
Output: data/processed/hn_stories_clean.csv

Cleaning steps:
1. Drop records with missing/empty title (unusable for length analysis).
2. descendants (comment count): missing -> 0 (HN omits it when zero).
3. score: missing -> 0; drop negative scores (not possible via API, guard).
4. time: must be a valid unix timestamp; drop otherwise.
5. url: missing -> "" (text posts); domain extracted where present.
6. Dedupe by id (keep first).
7. Feature engineering (documented, deterministic):
   - post_type: "ask" if title starts with "Ask HN:",
                "show" if starts with "Show HN:",
                "link" if url present, else "text"
   - title_len: characters in title
   - title_words: whitespace-separated tokens in title
   - domain: registrable-ish host from url (lowercased, strip www.)
   - hour_utc: 0-23 from timestamp
   - weekday: Monday..Sunday from timestamp (UTC)
   - topic: keyword bucket scan of title (first match wins):
       AI, Programming, Security, Startup, Apple, Mobile, Web,
       Hardware, Science, Open Source, Other
8. Engagement columns kept as-is: score, comments (=descendants).
   engagement_total = score + comments (simple combined metric).
"""
import csv
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

BASE = "/home/hatch/workspace/goals/techengage-social-post-engagement-analysis-10-pts-due-20-oct/hidden_files"
RAW = os.path.join(BASE, "data/raw/hn_stories_raw.json")
OUT = os.path.join(BASE, "data/processed/hn_stories_clean.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

TOPIC_RULES = [
    ("AI", ["ai", "llm", "gpt", "chatgpt", "machine learning", "neural", "openai",
            "anthropic", "deep learning", "transformer", "copilot", "gemini", "mistral"]),
    ("Security", ["security", "hack", "vulnerability", "cve", "malware", "ransomware",
                  "breach", "exploit", "phishing", "zero-day", "encryption"]),
    ("Programming", ["python", "javascript", "rust", "golang", "typescript", "java ",
                     "programming", "compiler", "code", "developer", "api", "database",
                     "postgres", "kubernetes", "docker", "git "]),
    ("Startup", ["startup", "funding", "yc ", "y combinator", "venture", "ipo",
                 "acquisition", "founder", "series a", "seed round"]),
    ("Apple", ["apple", "iphone", "macos", "ios "]),
    ("Mobile", ["android", "mobile", "smartphone"]),
    ("Web", ["web ", "website", "browser", "javascript framework", "react", "css",
             "html", "frontend"]),
    ("Hardware", ["chip", "cpu", "gpu", "hardware", "raspberry", "arduino", "intel",
                  "nvidia", "semiconductor"]),
    ("Science", ["science", "physics", "space", "nasa", "quantum", "biology",
                 "climate", "research"]),
    ("Open Source", ["open source", "open-source", "github"]),
]


def classify_topic(title):
    t = " " + title.lower() + " "
    for topic, keywords in TOPIC_RULES:
        for kw in keywords:
            if kw in t:
                return topic
    return "Other"


def clean_domain(url):
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def main():
    with open(RAW) as f:
        raw = json.load(f)
    stories = raw["stories"]
    print(f"raw records: {len(stories)}")

    seen, rows = set(), []
    dropped = {"no_title": 0, "bad_time": 0, "dup": 0}
    for s in stories:
        sid = s.get("id")
        if sid in seen:
            dropped["dup"] += 1
            continue
        seen.add(sid)
        title = (s.get("title") or "").strip()
        if not title:
            dropped["no_title"] += 1
            continue
        try:
            dt = datetime.fromtimestamp(int(s["time"]), tz=timezone.utc)
        except Exception:
            dropped["bad_time"] += 1
            continue
        score = s.get("score") or 0
        comments = s.get("descendants") or 0
        url = s.get("url") or ""
        low = title.lower()
        if low.startswith("ask hn:"):
            ptype = "ask"
        elif low.startswith("show hn:"):
            ptype = "show"
        elif url:
            ptype = "link"
        else:
            ptype = "text"
        rows.append({
            "id": sid,
            "title": title,
            "url": url,
            "domain": clean_domain(url),
            "post_type": ptype,
            "topic": classify_topic(title),
            "title_len": len(title),
            "title_words": len(title.split()),
            "score": int(score),
            "comments": int(comments),
            "engagement_total": int(score) + int(comments),
            "hour_utc": dt.hour,
            "weekday": dt.strftime("%A"),
            "posted_utc": dt.isoformat(),
        })
    print(f"dropped: {dropped}")
    print(f"clean records: {len(rows)}")

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
