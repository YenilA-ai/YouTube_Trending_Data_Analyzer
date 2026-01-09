import os
import csv
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import processing_core as proc
import charts_core as charts
import exporting_core as exp


class DataStore:
    def __init__(self):
        self.csv_name = "youtube_trending_videos.csv"
        self.csv_path = self._resolve(self.csv_name)
        self.rows = []
        self.loaded = False

    def _resolve(self, name):
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(here, name)
        if os.path.exists(p):
            return p
        return name

    def load(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(self.csv_path)

        out = []
        with open(self.csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = dict(row)
                r["category_id"] = _to_int(r.get("category_id"))
                r["views"] = _to_int(r.get("views"))
                r["likes"] = _to_int(r.get("likes"))
                r["dislikes"] = _to_int(r.get("dislikes"))
                r["comment_count"] = _to_int(r.get("comment_count"))
                r["trending_date"] = _to_date(r.get("trending_date"))
                r["publish_time"] = _to_datetime(r.get("publish_time"))
                out.append(r)

        self.rows = out
        self.loaded = True
        return len(out)


def _to_int(v):
    if v is None:
        return 0
    s = str(v).strip()
    if s == "":
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _to_date(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    for fmt in ("%Y-%m-%d", "%y.%d.%m", "%Y.%d.%m", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        return None


def _to_datetime(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trending Video Analyzer")
        self.geometry("1200x720")
        self.minsize(1050, 620)

        self.store = DataStore()
        self.pages = {}
        self.outputs = {}
        self.active_page = "Load"

        self._ui()
        self._switch("Load")

    def _ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        sidebar = ttk.Frame(self, padding=10)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.columnconfigure(0, weight=1)

        ttk.Label(sidebar, text="Menu", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        for i, name in enumerate(["Load", "Process", "Visualize", "Export"], start=1):
            ttk.Button(sidebar, text=name, command=lambda n=name: self._switch(n)).grid(row=i, column=0, sticky="ew", pady=4)

        ttk.Separator(sidebar, orient="horizontal").grid(row=6, column=0, sticky="ew", pady=12)
        ttk.Button(sidebar, text="Clear Page Output", command=self._clear_active).grid(row=7, column=0, sticky="ew", pady=4)

        main = ttk.Frame(self, padding=10)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        self.container = ttk.Frame(main)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        bottom = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom.grid(row=1, column=0, columnspan=2, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(bottom, textvariable=self.status_var, anchor="w").grid(row=0, column=0, sticky="ew")

        self._page_load()
        self._page_process()
        self._page_visualize()
        self._page_export()

    def _make_page(self, title):
        page = ttk.Frame(self.container)
        page.grid(row=0, column=0, sticky="nsew")
        page.columnconfigure(0, weight=0)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)
        self.pages[title] = page
        return page

    def _make_output(self, parent, key):
        wrap = ttk.Frame(parent)
        wrap.grid(row=0, column=1, sticky="nsew")
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        txt = tk.Text(wrap, wrap="word")
        txt.grid(row=0, column=0, sticky="nsew")
        scr = ttk.Scrollbar(wrap, orient="vertical", command=txt.yview)
        scr.grid(row=0, column=1, sticky="ns")
        txt.configure(yscrollcommand=scr.set)
        self.outputs[key] = txt

    def _out(self, s):
        txt = self.outputs.get(self.active_page)
        if not txt:
            return
        txt.insert("end", s + "\n")
        txt.see("end")

    def _clear_active(self):
        txt = self.outputs.get(self.active_page)
        if not txt:
            return
        txt.delete("1.0", "end")

    def _switch(self, title):
        self.active_page = title
        for k, p in self.pages.items():
            if k == title:
                p.tkraise()
        self.status_var.set(f"Page: {title}")

    def _need_data(self):
        if not self.store.loaded:
            messagebox.showwarning("Data not loaded", "Go to Load and click Load CSV.")
            return False
        return True

    def _page_load(self):
        page = self._make_page("Load")

        left = ttk.Frame(page, padding=10)
        left.grid(row=0, column=0, sticky="ns")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Load Dataset", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(left, text="CSV path").grid(row=1, column=0, sticky="w")
        self.path_var = tk.StringVar(value=self.store.csv_path)
        ttk.Entry(left, textvariable=self.path_var, width=38).grid(row=2, column=0, sticky="ew", pady=(4, 10))

        ttk.Button(left, text="Load CSV", command=self._do_load).grid(row=3, column=0, sticky="ew")

        self._make_output(page, "Load")

    def _do_load(self):
        self.store.csv_path = self.path_var.get().strip() or self.store.csv_name
        try:
            n = self.store.load()
            self._out(f"Loaded rows: {n}")
            if n > 0:
                self._out("Columns: " + ", ".join(list(self.store.rows[0].keys())))
            self.status_var.set(f"Loaded {n} rows")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))

    def _page_process(self):
        page = self._make_page("Process")

        left = ttk.Frame(page, padding=10)
        left.grid(row=0, column=0, sticky="ns")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Process", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Basic").grid(row=1, column=0, sticky="w")
        ttk.Button(left, text="Summary Counts", command=self._p_counts).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Category Frequency", command=self._p_catfreq).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Search Video Info", command=self._p_search).grid(row=4, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Top 10 by Metric", command=self._p_top10).grid(row=5, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=6, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Intermediate").grid(row=7, column=0, sticky="w")
        ttk.Button(left, text="Avg Engagement per Category", command=self._p_avgeng).grid(row=8, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Trending Duration per Video", command=self._p_duration).grid(row=9, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Like/Dislike Outliers", command=self._p_outliers).grid(row=10, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=11, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Advanced").grid(row=12, column=0, sticky="w")
        ttk.Button(left, text="Similar Video Suggestions", command=self._p_reco).grid(row=13, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Tag Keyword Ranking", command=self._p_tags).grid(row=14, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Engagement Anomaly Scan", command=self._p_anom).grid(row=15, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Trending Duration Estimate", command=self._p_pred).grid(row=16, column=0, sticky="ew", pady=2)

        self._make_output(page, "Process")

    def _page_visualize(self):
        page = self._make_page("Visualize")

        left = ttk.Frame(page, padding=10)
        left.grid(row=0, column=0, sticky="ns")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Visualize", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Basic").grid(row=1, column=0, sticky="w")
        ttk.Button(left, text="Pie: Categories", command=self._v_pie).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Hist: Views/Likes/Comments", command=self._v_hist).grid(row=3, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=4, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Intermediate").grid(row=5, column=0, sticky="w")
        ttk.Button(left, text="Line: Avg Duration per Category Over Time", command=self._v_line).grid(row=6, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Bar: Likes/Dislikes/Comments Top Videos", command=self._v_bar).grid(row=7, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=8, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Advanced").grid(row=9, column=0, sticky="w")
        ttk.Button(left, text="Dashboard: Filter + Metric", command=self._v_dash).grid(row=10, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Overlay: Flag Anomalies", command=self._v_overlay).grid(row=11, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Tags: Frequency Chart", command=self._v_tags).grid(row=12, column=0, sticky="ew", pady=2)

        self._make_output(page, "Visualize")

    def _page_export(self):
        page = self._make_page("Export")

        left = ttk.Frame(page, padding=10)
        left.grid(row=0, column=0, sticky="ns")
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Export", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(left, text="Basic").grid(row=1, column=0, sticky="w")
        ttk.Button(left, text="Export Search Result (JSON)", command=self._e_search_json).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Export Top 10 (CSV/JSON)", command=self._e_top10).grid(row=3, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Export First N Rows (CSV)", command=self._e_firstn).grid(row=4, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=5, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Intermediate").grid(row=6, column=0, sticky="w")
        ttk.Button(left, text="Export Category Averages (JSON)", command=self._e_catavg).grid(row=7, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Export Filtered Dataset (CSV)", command=self._e_filter).grid(row=8, column=0, sticky="ew", pady=2)

        ttk.Separator(left).grid(row=9, column=0, sticky="ew", pady=10)

        ttk.Label(left, text="Advanced").grid(row=10, column=0, sticky="w")
        ttk.Button(left, text="Export Recommendations (JSON)", command=self._e_reco).grid(row=11, column=0, sticky="ew", pady=2)
        ttk.Button(left, text="Export Anomaly Report (JSON)", command=self._e_anom).grid(row=12, column=0, sticky="ew", pady=2)

        self._make_output(page, "Export")

    def _p_counts(self):
        if not self._need_data():
            return
        self._out(_pretty(proc.summary_counts(self.store.rows)))

    def _p_catfreq(self):
        if not self._need_data():
            return
        self._out(_pretty(proc.category_frequency(self.store.rows)))

    def _p_search(self):
        if not self._need_data():
            return
        q = _ask_text(self, "Search", "Enter video_id or part of title:")
        if q is None:
            return
        self._out(_pretty(proc.search_video(self.store.rows, q)))

    def _p_top10(self):
        if not self._need_data():
            return
        m = _ask_choice(self, "Metric", "Select metric:", ["views", "likes", "comment_count"])
        if m is None:
            return
        self._out(_pretty(proc.top10_by_metric(self.store.rows, m)))

    def _p_avgeng(self):
        if not self._need_data():
            return
        self._out(_pretty(proc.avg_engagement_by_category(self.store.rows)))

    def _p_duration(self):
        if not self._need_data():
            return
        self._out(_pretty(proc.trending_days_by_video(self.store.rows)))

    def _p_outliers(self):
        if not self._need_data():
            return
        t = _ask_text(self, "Threshold", "Enter like/dislike ratio threshold (e.g., 30):")
        if t is None:
            return
        try:
            t = float(t)
        except Exception:
            messagebox.showerror("Invalid", "Enter a number")
            return
        self._out(_pretty(proc.ratio_outliers(self.store.rows, t)))

    def _p_reco(self):
        if not self._need_data():
            return
        q = _ask_text(self, "Recommend", "Enter video_id or part of title:")
        if q is None:
            return
        k = _ask_text(self, "How many", "Enter number of recommendations:")
        if k is None:
            return
        try:
            k = int(k)
        except Exception:
            messagebox.showerror("Invalid", "Enter an integer")
            return
        self._out(_pretty(proc.recommend_similar(self.store.rows, q, k)))

    def _p_tags(self):
        if not self._need_data():
            return
        n = _ask_text(self, "Top N", "Enter N for top keywords:")
        if n is None:
            return
        try:
            n = int(n)
        except Exception:
            messagebox.showerror("Invalid", "Enter an integer")
            return
        self._out(_pretty(proc.tag_keyword_rank(self.store.rows, n)))

    def _p_anom(self):
        if not self._need_data():
            return
        self._out(_pretty(proc.anomaly_scan(self.store.rows)))

    def _p_pred(self):
        if not self._need_data():
            return
        q = _ask_text(self, "Predict", "Enter video_id or part of title:")
        if q is None:
            return
        self._out(_pretty(proc.estimate_trending_days(self.store.rows, q)))

    def _v_pie(self):
        if not self._need_data():
            return
        charts.pie_categories(self.store.rows)

    def _v_hist(self):
        if not self._need_data():
            return
        charts.histograms_basic(self.store.rows)

    def _v_line(self):
        if not self._need_data():
            return
        charts.line_duration_by_category_over_time(self.store.rows)

    def _v_bar(self):
        if not self._need_data():
            return
        charts.bar_engagement_top_videos(self.store.rows)

    def _v_dash(self):
        if not self._need_data():
            return
        charts.dashboard_filter_metric(self.store.rows)

    def _v_overlay(self):
        if not self._need_data():
            return
        charts.anomaly_overlay(self.store.rows)

    def _v_tags(self):
        if not self._need_data():
            return
        charts.tag_frequency_chart(self.store.rows)

    def _e_search_json(self):
        if not self._need_data():
            return
        q = _ask_text(self, "Export", "Enter video_id or part of title:")
        if q is None:
            return
        p = exp.export_search_json(self.store.rows, q)
        self._out(f"Saved: {p}")

    def _e_top10(self):
        if not self._need_data():
            return
        fmt = _ask_choice(self, "Format", "Select format:", ["csv", "json"])
        if fmt is None:
            return
        metric = _ask_choice(self, "Metric", "Select metric:", ["views", "likes", "comment_count"])
        if metric is None:
            return
        p = exp.export_top10(self.store.rows, metric, fmt)
        self._out(f"Saved: {p}")

    def _e_firstn(self):
        if not self._need_data():
            return
        n = _ask_text(self, "Rows", "Export first N rows:")
        if n is None:
            return
        try:
            n = int(n)
        except Exception:
            messagebox.showerror("Invalid", "Enter an integer")
            return
        p = exp.export_first_n(self.store.rows, n)
        self._out(f"Saved: {p}")

    def _e_catavg(self):
        if not self._need_data():
            return
        p = exp.export_category_averages(self.store.rows)
        self._out(f"Saved: {p}")

    def _e_filter(self):
        if not self._need_data():
            return
        mode = _ask_choice(self, "Filter", "Filter by:", ["category_id", "channel_title", "trending_date_range"])
        if mode is None:
            return
        filt = {"mode": mode}
        if mode == "category_id":
            v = _ask_text(self, "Category", "Enter category_id:")
            if v is None:
                return
            try:
                filt["category_id"] = int(v)
            except Exception:
                messagebox.showerror("Invalid", "Enter an integer")
                return
        elif mode == "channel_title":
            v = _ask_text(self, "Channel", "Enter exact channel_title:")
            if v is None:
                return
            filt["channel_title"] = v
        else:
            a = _ask_text(self, "Start", "Start date (YYYY-MM-DD):")
            if a is None:
                return
            b = _ask_text(self, "End", "End date (YYYY-MM-DD):")
            if b is None:
                return
            filt["start"] = a
            filt["end"] = b
        p = exp.export_filtered_csv(self.store.rows, filt)
        self._out(f"Saved: {p}")

    def _e_reco(self):
        if not self._need_data():
            return
        q = _ask_text(self, "Recommend Export", "Enter video_id or part of title:")
        if q is None:
            return
        k = _ask_text(self, "How many", "Enter number of recommendations:")
        if k is None:
            return
        try:
            k = int(k)
        except Exception:
            messagebox.showerror("Invalid", "Enter an integer")
            return
        p = exp.export_recommendations(self.store.rows, q, k)
        self._out(f"Saved: {p}")

    def _e_anom(self):
        if not self._need_data():
            return
        p = exp.export_anomalies(self.store.rows)
        self._out(f"Saved: {p}")


def _pretty(x):
    try:
        return json.dumps(x, indent=2, default=str, ensure_ascii=False)
    except Exception:
        return str(x)


def _ask_text(root, title, prompt):
    top = tk.Toplevel(root)
    top.title(title)
    top.transient(root)
    top.grab_set()
    top.resizable(False, False)

    v = {"val": None}

    frm = ttk.Frame(top, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    ttk.Label(frm, text=prompt).grid(row=0, column=0, sticky="w")
    sv = tk.StringVar()
    e = ttk.Entry(frm, textvariable=sv, width=52)
    e.grid(row=1, column=0, sticky="ew", pady=(6, 10))
    e.focus_set()

    btn = ttk.Frame(frm)
    btn.grid(row=2, column=0, sticky="e")

    def ok():
        v["val"] = sv.get().strip()
        top.destroy()

    def cancel():
        v["val"] = None
        top.destroy()

    ttk.Button(btn, text="OK", command=ok).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(btn, text="Cancel", command=cancel).grid(row=0, column=1)

    top.bind("<Return>", lambda _e: ok())
    top.bind("<Escape>", lambda _e: cancel())

    root.wait_window(top)
    return v["val"]


def _ask_choice(root, title, prompt, options):
    top = tk.Toplevel(root)
    top.title(title)
    top.transient(root)
    top.grab_set()
    top.resizable(False, False)

    v = {"val": None}

    frm = ttk.Frame(top, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    ttk.Label(frm, text=prompt).grid(row=0, column=0, sticky="w")

    choice = tk.StringVar(value=options[0] if options else "")
    cb = ttk.Combobox(frm, textvariable=choice, state="readonly", values=options, width=50)
    cb.grid(row=1, column=0, sticky="ew", pady=(6, 10))
    cb.focus_set()

    btn = ttk.Frame(frm)
    btn.grid(row=2, column=0, sticky="e")

    def ok():
        v["val"] = choice.get()
        top.destroy()

    def cancel():
        v["val"] = None
        top.destroy()

    ttk.Button(btn, text="OK", command=ok).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(btn, text="Cancel", command=cancel).grid(row=0, column=1)

    top.bind("<Return>", lambda _e: ok())
    top.bind("<Escape>", lambda _e: cancel())

    root.wait_window(top)
    return v["val"]


if __name__ == "__main__":
    App().mainloop()
