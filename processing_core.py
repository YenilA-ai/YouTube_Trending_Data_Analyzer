from collections import Counter, defaultdict
from datetime import date


def summary_counts(rows):
    videos = set()
    channels = set()
    for r in rows:
        if r.get("video_id"):
            videos.add(r.get("video_id"))
        if r.get("channel_title"):
            channels.add(r.get("channel_title"))
    return {
        "total_rows": len(rows),
        "unique_videos": len(videos),
        "unique_channels": len(channels),
    }


def category_frequency(rows):
    c = Counter()
    for r in rows:
        c[r.get("category_id")] += 1
    return dict(c)


def search_video(rows, query):
    q = str(query).lower()
    out = []
    for r in rows:
        if str(r.get("video_id", "")).lower() == q or q in str(r.get("title", "")).lower():
            out.append({
                "video_id": r.get("video_id"),
                "title": r.get("title"),
                "channel_title": r.get("channel_title"),
                "category_id": r.get("category_id"),
                "views": r.get("views", 0),
                "likes": r.get("likes", 0),
                "dislikes": r.get("dislikes", 0),
                "comment_count": r.get("comment_count", 0),
                "publish_time": r.get("publish_time"),
                "trending_date": r.get("trending_date"),
                "tags": r.get("tags"),
            })
    return out


def top10_by_metric(rows, metric):
    metric = metric if metric in ("views", "likes", "comment_count") else "views"
    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid:
            continue
        v = r.get(metric, 0)
        if vid not in best or v > best[vid].get(metric, 0):
            best[vid] = r
    top = sorted(best.values(), key=lambda x: x.get(metric, 0), reverse=True)[:10]
    out = []
    for i, r in enumerate(top, 1):
        out.append({
            "rank": i,
            "video_id": r.get("video_id"),
            "title": r.get("title"),
            metric: r.get(metric, 0),
        })
    return out


def avg_engagement_by_category(rows):
    sums = defaultdict(lambda: {"likes": 0, "dislikes": 0, "comments": 0, "n": 0})
    for r in rows:
        cid = r.get("category_id")
        sums[cid]["likes"] += r.get("likes", 0)
        sums[cid]["dislikes"] += r.get("dislikes", 0)
        sums[cid]["comments"] += r.get("comment_count", 0)
        sums[cid]["n"] += 1

    out = {}
    for cid, v in sums.items():
        n = v["n"] if v["n"] else 1
        out[cid] = {
            "avg_likes": v["likes"] // n,
            "avg_dislikes": v["dislikes"] // n,
            "avg_comments": v["comments"] // n,
        }
    return out


def trending_days_by_video(rows):
    days = defaultdict(set)
    for r in rows:
        vid = r.get("video_id")
        d = r.get("trending_date")
        if vid and isinstance(d, date):
            days[vid].add(d)
    return {vid: len(ds) for vid, ds in days.items()}


def ratio_outliers(rows, threshold):
    seen = set()
    out = []
    for r in rows:
        vid = r.get("video_id")
        if not vid or vid in seen:
            continue
        seen.add(vid)
        likes = r.get("likes", 0)
        dislikes = r.get("dislikes", 0)
        if dislikes == 0:
            ratio = float("inf") if likes > 0 else 0.0
        else:
            ratio = likes / dislikes
        if ratio >= float(threshold):
            out.append({
                "video_id": vid,
                "title": r.get("title"),
                "likes": likes,
                "dislikes": dislikes,
                "ratio": ratio,
            })
    return out