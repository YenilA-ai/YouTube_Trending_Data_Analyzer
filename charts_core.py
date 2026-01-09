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

def dashboard_filter_metric(rows):
    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid:
            continue
        v = r.get("views", 0)
        if vid not in best or v > best[vid].get("views", 0):
            best[vid] = r
    base = list(best.values())

    cats = sorted({r.get("category_id") for r in base}, key=lambda x: str(x))
    chans = sorted({r.get("channel_title") for r in base if r.get("channel_title")}, key=lambda x: x.lower())

    win = tk.Toplevel()
    win.title("Dashboard")
    win.geometry("980x620")

    top = ttk.Frame(win, padding=10)
    top.pack(fill="x")

    ttk.Label(top, text="Category").grid(row=0, column=0, sticky="w")
    catv = tk.StringVar(value="All")
    catcb = ttk.Combobox(top, textvariable=catv, state="readonly", values=["All"] + [str(c) for c in cats], width=16)
    catcb.grid(row=0, column=1, padx=(6, 16), sticky="w")

    ttk.Label(top, text="Channel").grid(row=0, column=2, sticky="w")
    chv = tk.StringVar(value="All")
    chcb = ttk.Combobox(top, textvariable=chv, state="readonly", values=["All"] + chans, width=34)
    chcb.grid(row=0, column=3, padx=(6, 16), sticky="w")

    ttk.Label(top, text="Metric").grid(row=0, column=4, sticky="w")
    mv = tk.StringVar(value="likes")
    mcb = ttk.Combobox(top, textvariable=mv, state="readonly", values=["likes", "dislikes", "comment_count"], width=18)
    mcb.grid(row=0, column=5, padx=(6, 0), sticky="w")

    fig = plt.Figure(figsize=(8.6, 5.4))
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def filt():
        r = base
        if catv.get() != "All":
            r = [x for x in r if str(x.get("category_id")) == catv.get()]
        if chv.get() != "All":
            r = [x for x in r if (x.get("channel_title") or "") == chv.get()]
        return r

    def draw(*_):
        r = filt()
        xs = [x.get("views", 0) for x in r]
        m = mv.get()
        ys = [x.get(m, 0) for x in r]

        ax.clear()
        ax.set_title("Views vs Selected Metric")
        ax.set_xlabel("Views")
        ax.set_ylabel(m)
        if xs and ys:
            ax.scatter(xs, ys)
        canvas.draw_idle()

    catcb.bind("<<ComboboxSelected>>", draw)
    chcb.bind("<<ComboboxSelected>>", draw)
    mcb.bind("<<ComboboxSelected>>", draw)

    draw()
    win.grab_set()


def anomaly_overlay(rows):
    best = {}
    for r in rows:
        vid = r.get("video_id")
        if not vid:
            continue
        v = r.get("views", 0)
        if vid not in best or v > best[vid].get("views", 0):
            best[vid] = r
    base = list(best.values())

    by_cat = defaultdict(list)
    for r in base:
        by_cat[r.get("category_id")].append(r)

    avg_views = {}
    for cid, lst in by_cat.items():
        s = 0
        n = 0
        for r in lst:
            s += r.get("views", 0)
            n += 1
        avg_views[cid] = (s / n) if n else 0

    xs = []
    ys = []
    axx = []
    axy = []

    for r in base:
        views = r.get("views", 0)
        likes = r.get("likes", 0)
        dislikes = r.get("dislikes", 0)

        xs.append(views)
        ys.append(likes)

        cid = r.get("category_id")
        spike = avg_views.get(cid, 0) > 0 and views >= avg_views[cid] * 3

        ratio = False
        if dislikes == 0:
            ratio = likes >= 10000
        else:
            ratio = (likes / dislikes) >= 50

        if spike or ratio:
            axx.append(views)
            axy.append(likes)

    plt.figure()
    plt.title("Anomaly Overlay (View Spike OR High Like/Dislike Ratio)")
    plt.scatter(xs, ys, label="All")
    if axx:
        plt.scatter(axx, axy, label="Anomalies")
    plt.xlabel("Views")
    plt.ylabel("Likes")
    plt.legend()
    plt.tight_layout()
    plt.show()


def tag_frequency_chart(rows):
    c = Counter()
    for r in rows:
        tags = (r.get("tags") or "").strip()
        if not tags or tags == "[none]":
            continue
        for t in tags.replace("|", " ").split():
            k = t.strip().lower()
            if len(k) > 2:
                c[k] += 1

    common = c.most_common(25)
    words = [w for w, _ in common]
    freq = [n for _, n in common]

    plt.figure()
    plt.title("Top Tag Keywords")
    plt.bar(words, freq)
    plt.xticks(rotation=60, ha="right")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.show()
