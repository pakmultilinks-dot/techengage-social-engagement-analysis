# TechEngage: Social Post Engagement Analysis

**Task:** ZR-26-00753 (task 14, Data Scientist) — find which kinds of social posts get the
most engagement, to guide TechEngage's content planning.

## Data source

**Hacker News public API** (`https://hacker-news.firebaseio.com/v0/`) — fully public,
no authentication, no API key. Tech news stories with public engagement signals
(upvotes = `score`, discussion = `descendants`/comments), a close proxy for the
engagement TechEngage's own tech-news posts receive.

- Collected 2026-10-14: 500 current top stories + 500 best stories via
  `/topstories.json`, `/beststories.json`, then `/item/<id>.json` per story.
- Deduplicated; kept `type == "story"` only.
- Raw dump: `data/raw/hn_stories_raw.json` (with collection timestamp + endpoints).
- See `src/collect.py` for the exact collection script.

## Cleaning steps (`src/clean.py`)

1. Drop records with missing/empty title.
2. Missing `descendants` → 0 (HN omits the field when there are no comments).
3. Missing `score` → 0.
4. Drop invalid timestamps; dedupe by story id.
5. Feature engineering (deterministic, documented in `src/clean.py`):
   - `post_type`: `ask` (`Ask HN:`), `show` (`Show HN:`), `link` (has URL), `text`
   - `title_len`, `title_words`, `domain`, `hour_utc`, `weekday`
   - `topic`: keyword-bucket scan of the title (AI, Security, Programming,
     Startup, Apple, Mobile, Web, Hardware, Science, Open Source, Other)
   - `engagement_total = score + comments`
- Cleaned: `data/processed/hn_stories_clean.csv`

## Method (`src/analyze.py`, `notebooks/`)

- Headline stat is the **median** (engagement is heavy-tailed; the median is robust).
- Aggregations: engagement by post type, title-length bucket, topic, weekday,
  hour of day, and top linked domains (min 5 posts).
- Pearson correlation of title length vs score/comments.
- Full walkthrough in `notebooks/engagement_analysis.ipynb`.

## Dashboard

Live: https://techengage-engagement-dashboard-pakmultilinks-dot.vercel.app

Static dashboard (`dashboard/index.html`, Chart.js) with 5 charts and filters
(post type, topic, weekday). Data baked in from `data/processed/summary.json`,
so it runs anywhere with no backend.

## Report

`report/TechEngage-Content-Recommendations.pdf` — one page, three content
recommendations for TechEngage's editors.

## Assumptions and limitations

- HN upvotes/comments proxy social engagement; HN's audience skews
  developer-heavy and US/EU timezones, so absolute numbers don't transfer
  1:1 to TechEngage's audience — relative rankings do.
- "Top/best" endpoints bias the sample toward already-successful posts;
  this is a study of *what wins*, not of average posts.
- Topic buckets are keyword-based, not manual labels; edge cases land in "Other".
- Timestamps are UTC; TechEngage (PKT = UTC+5) should shift hour findings +5.
- No customer or private data used anywhere.

## Reproduce

```bash
python3 src/collect.py    # -> data/raw/hn_stories_raw.json
python3 src/clean.py      # -> data/processed/hn_stories_clean.csv
python3 src/analyze.py    # -> data/processed/summary.json (prints tables)
```

## Layout

```
data/raw/        raw API dump (JSON)
data/processed/  cleaned CSV + summary.json for the dashboard
notebooks/       analysis walkthrough
src/             collect.py, clean.py, analyze.py
dashboard/       static dashboard (index.html)
report/          one-page PDF recommendations
```
