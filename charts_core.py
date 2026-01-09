from collections import Counter, defaultdict
from datetime import date
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def pie_categories(rows):
    c = Counter()
    for r in rows:
        c[r.get("category_id")] += 1
    labels = [str(k) for k, _ in c.most_common()]
    sizes = [v for _, v in c.most_common()]
    plt.figure()
    plt.title("Videos by Category")
    plt.pie(sizes, labels=labels, autopct="%1.1f%%")
    plt.show()


def histograms_basic(rows):
    views = [r.get("views", 0) for r in rows]
    likes = [r.get("likes", 0) for r in rows]
    comm = [r.get("comment_count", 0) for r in rows]

    plt.figure()
    plt.title("Views Histogram")
    plt.hist(views, bins=40)
    plt.xlabel("Views")
    plt.ylabel("Count")
    plt.show()

    plt.figure()
    plt.title("Likes Histogram")
    plt.hist(likes, bins=40)
    plt.xlabel("Likes")
    plt.ylabel("Count")
    plt.show()

    plt.figure()
    plt.title("Comments Histogram")
    plt.hist(comm, bins=40)
    plt.xlabel("Comments")
    plt.ylabel("Count")
    plt.show()

def line_duration_by_category_over_time(rows):
    dates_by_vid = defaultdict(set)
    cat_by_vid = {}

    for r in rows:
        vid = r.get("video_id")
        d = r.get("trending_date")
        cid = r.get("category_id")
        if vid and isinstance(d, date):
            dates_by_vid[vid].add(d)
            if vid not in cat_by_vid:
                cat_by_vid[vid] = cid

    dur_by_vid = {vid: len(ds) for vid, ds in dates_by_vid.items()}

    sum_by_cat_date = defaultdict(lambda: defaultdict(int))
    cnt_by_cat_date = defaultdict(lambda: defaultdict(int))

    for r in rows:
        vid = r.get("video_id")
        d = r.get("trending_date")
        if not vid or not isinstance(d, date):
            continue
        cid = cat_by_vid.get(vid, r.get("category_id"))
        dur = dur_by_vid.get(vid, 0)
        sum_by_cat_date[cid][d] += dur
        cnt_by_cat_date[cid][d] += 1

    cats = sorted(sum_by_cat_date.keys(), key=lambda x: str(x))
    if not cats:
        return

    plt.figure()
    plt.title("Avg Trending Duration per Category Over Time")
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    for cid in cats:
        xs = sorted(sum_by_cat_date[cid].keys())
        ys = []
        for d in xs:
            n = cnt_by_cat_date[cid][d] if cnt_by_cat_date[cid][d] else 1
            ys.append(sum_by_cat_date[cid][d] / n)
        if xs:
            plt.plot(xs, ys, marker="o", label=str(cid))

    plt.xlabel("Trending Date")
    plt.ylabel("Avg Duration (days)")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Category")
    plt.tight_layout()
    plt.show()


def bar_engagement_top_videos(rows):
    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid:
            continue
        v = r.get("views", 0)
        if vid not in best or v > best[vid].get("views", 0):
            best[vid] = r

    top = sorted(best.values(), key=lambda x: x.get("views", 0), reverse=True)[:10]

    names = []
    likes = []
    dislikes = []
    comm = []

    for r in top:
        t = r.get("title") or ""
        names.append(t[:18] + ("..." if len(t) > 18 else ""))
        likes.append(r.get("likes", 0))
        dislikes.append(r.get("dislikes", 0))
        comm.append(r.get("comment_count", 0))

    x = list(range(len(names)))
    w = 0.25

    plt.figure()
    plt.title("Top 10 Videos: Likes vs Dislikes vs Comments")
    plt.bar([i - w for i in x], likes, width=w, label="Likes")
    plt.bar(x, dislikes, width=w, label="Dislikes")
    plt.bar([i + w for i in x], comm, width=w, label="Comments")
    plt.xticks(x, names, rotation=45, ha="right")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    plt.show()

