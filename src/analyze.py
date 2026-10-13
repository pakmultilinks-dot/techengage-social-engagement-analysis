"""
TechEngage Social Post Engagement Analysis - Analysis
======================================================
Input : data/processed/hn_stories_clean.csv
Output: data/processed/summary.json  (aggregates that feed the dashboard)

Metrics:
- score            : HN upvotes (popularity)
- comments         : discussion volume
- engagement_total : score + comments (combined)

Aggregations (medians used as the headline stat: engagement is heavy-tailed,
so the median is more robust than the mean; means also reported):
1. by post_type   -> n, median/mean score, comments, total
2. by title_len bucket (<=40, 41-60, 61-80, 81-100, 100+ chars)
3. by topic       -> same stats, sorted by median total
4. by weekday     -> same stats (Monday..Sunday order)
5. by hour_utc    -> median total per hour bucket (0-23)
6. top domains    -> top 15 by median total (min 5 posts)
7. correlations   -> pearson r of title_len vs score/comments
"""
import csv
import json
import os
from collections import defaultdict
from statistics import median, mean

BASE = "/home/hatch/workspace/goals/techengage-social-post-engagement-analysis-10-pts-due-20-oct/hidden_files"
INP = os.path.join(BASE, "data/processed/hn_stories_clean.csv")
OUT = os.path.join(BASE, "data/processed/summary.json")

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"]


def bucket_len(n):
    if n <= 40:
        return "<=40"
    if n <= 60:
        return "41-60"
    if n <= 80:
        return "61-80"
    if n <= 100:
        return "81-100"
    return "100+"


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return round(num / den, 3) if den else 0.0


def stats(rows):
    scores = [r["score"] for r in rows]
    comments = [r["comments"] for r in rows]
    totals = [r["engagement_total"] for r in rows]
    return {
        "n": len(rows),
        "median_score": round(median(scores), 1),
        "mean_score": round(mean(scores), 1),
        "median_comments": round(median(comments), 1),
        "mean_comments": round(mean(comments), 1),
        "median_total": round(median(totals), 1),
        "mean_total": round(mean(totals), 1),
    }


def group(rows, keyfn):
    groups = defaultdict(list)
    for r in rows:
        groups[keyfn(r)].append(r)
    return {k: stats(v) for k, v in groups.items()}


def main():
    with open(INP) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("score", "comments", "engagement_total", "title_len",
                  "title_words", "hour_utc"):
            r[k] = int(r[k])

    by_type = group(rows, lambda r: r["post_type"])
    by_len = group(rows, lambda r: bucket_len(r["title_len"]))
    by_topic = group(rows, lambda r: r["topic"])
    by_weekday = group(rows, lambda r: r["weekday"])
    by_hour = group(rows, lambda r: r["hour_utc"])
    domains = {k: v for k, v in group(rows, lambda r: r["domain"] or "(no url)").items()
               if v["n"] >= 5 and k != "(no url)"}
    top_domains = dict(sorted(domains.items(),
                              key=lambda kv: kv[1]["median_total"], reverse=True)[:15])

    summary = {
        "n_posts": len(rows),
        "by_post_type": by_type,
        "by_title_length": {k: by_len[k] for k in
                            ["<=40", "41-60", "61-80", "81-100", "100+"] if k in by_len},
        "by_topic": dict(sorted(by_topic.items(),
                                key=lambda kv: kv[1]["median_total"], reverse=True)),
        "by_weekday": {d: by_weekday.get(d) for d in WEEKDAY_ORDER if d in by_weekday},
        "by_hour": {str(h): by_hour.get(h) for h in range(24)},
        "top_domains": top_domains,
        "corr_title_len_vs_score": pearson([r["title_len"] for r in rows],
                                           [r["score"] for r in rows]),
        "corr_title_len_vs_comments": pearson([r["title_len"] for r in rows],
                                             [r["comments"] for r in rows]),
    }
    with open(OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"saved -> {OUT}")

    print("\n== by post_type (median_total) ==")
    for k, v in sorted(by_type.items(), key=lambda kv: kv[1]["median_total"], reverse=True):
        print(f"  {k:6s} n={v['n']:4d} med_score={v['median_score']:7.1f} med_comments={v['median_comments']:6.1f} med_total={v['median_total']:7.1f}")
    print("\n== by topic (median_total) ==")
    for k, v in summary["by_topic"].items():
        print(f"  {k:12s} n={v['n']:4d} med_total={v['median_total']:7.1f}")
    print("\n== by title length (median_total) ==")
    for k, v in summary["by_title_length"].items():
        print(f"  {k:6s} n={v['n']:4d} med_total={v['median_total']:7.1f}")
    print("\n== by weekday (median_total) ==")
    for k, v in summary["by_weekday"].items():
        print(f"  {k:9s} n={v['n']:4d} med_total={v['median_total']:7.1f}")
    print(f"\ncorr title_len vs score: {summary['corr_title_len_vs_score']}, vs comments: {summary['corr_title_len_vs_comments']}")


if __name__ == "__main__":
    main()
