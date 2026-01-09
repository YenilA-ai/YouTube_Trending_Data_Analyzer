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