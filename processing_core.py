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



def recommend_similar(rows, query, k):
    base = _find_one(rows, query)
    if not base:
        return []

    base_vid = base.get("video_id")
    base_cat = base.get("category_id")
    base_tags = _tags(base.get("tags"))

    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid or vid == base_vid:
            continue
        if vid not in best:
            best[vid] = r

    scored = []
    for vid, r in best.items():
        score = 0
        if r.get("category_id") == base_cat:
            score += 6
        score += len(base_tags.intersection(_tags(r.get("tags"))))
        if r.get("channel_title") == base.get("channel_title"):
            score += 1
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)

    out = []
    for i in range(min(int(k), len(scored))):
        r = scored[i][1]
        out.append({
            "video_id": r.get("video_id"),
            "title": r.get("title"),
            "channel_title": r.get("channel_title"),
            "category_id": r.get("category_id"),
            "views": r.get("views", 0),
        })
    return out


def tag_keyword_rank(rows, n):
    c = Counter()
    for r in rows:
        for t in _tags(r.get("tags")):
            if len(t) > 2:
                c[t] += 1
    return c.most_common(int(n))


def anomaly_scan(rows):
    best = _best_per_video(rows)

    by_cat = defaultdict(list)
    for r in best:
        by_cat[r.get("category_id")].append(r)

    avg_like = {}
    avg_comm = {}
    for cid, lst in by_cat.items():
        ls = 0
        cs = 0
        n = 0
        for r in lst:
            ls += r.get("likes", 0)
            cs += r.get("comment_count", 0)
            n += 1
        avg_like[cid] = (ls // n) if n else 0
        avg_comm[cid] = (cs // n) if n else 0

    out = []
    for r in best:
        cid = r.get("category_id")
        likes = r.get("likes", 0)
        comm = r.get("comment_count", 0)
        if likes >= max(1, avg_like.get(cid, 0) * 3) and comm <= max(0, avg_comm.get(cid, 0) // 3):
            out.append({
                "video_id": r.get("video_id"),
                "title": r.get("title"),
                "category_id": cid,
                "likes": likes,
                "comment_count": comm,
                "category_avg_likes": avg_like.get(cid, 0),
                "category_avg_comments": avg_comm.get(cid, 0),
            })
    return out


def estimate_trending_days(rows, query):
    base = _find_one(rows, query)
    if not base:
        return {"predicted_days": 0}

    durations = trending_days_by_video(rows)
    cat = base.get("category_id")

    total = 0
    cnt = 0
    for r in rows:
        if r.get("category_id") == cat:
            d = durations.get(r.get("video_id"))
            if d:
                total += d
                cnt += 1

    base_avg = (total // cnt) if cnt else 1

    views = base.get("views", 0)
    likes = base.get("likes", 0)
    comm = base.get("comment_count", 0)

    bump = 0
    if views >= 1_000_000 or likes >= 50_000 or comm >= 5_000:
        bump += 2
    elif views >= 300_000 or likes >= 15_000 or comm >= 1_500:
        bump += 1

    pub = base.get("publish_time")
    hour = getattr(pub, "hour", None)
    if hour is not None:
        if 16 <= hour <= 22:
            bump += 1
        if 0 <= hour <= 6:
            bump -= 1

    pred = base_avg + bump
    if pred < 1:
        pred = 1

    return {
        "predicted_days": pred,
        "category_avg_days": base_avg,
        "adjustment": bump,
    }


def _find_one(rows, query):
    q = str(query).lower()
    for r in rows:
        if str(r.get("video_id", "")).lower() == q or q in str(r.get("title", "")).lower():
            return r
    return None


def _tags(s):
    s = (s or "").strip()
    if not s or s == "[none]":
        return set()
    parts = s.replace("|", " ").split()
    out = set()
    for p in parts:
        t = p.strip().lower()
        if t:
            out.add(t)
    return out


def _best_per_video(rows):
    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid:
            continue
        v = r.get("views", 0)
        if vid not in best or v > best[vid].get("views", 0):
            best[vid] = r
    return list(best.values())
