import os
import csv
import json
from datetime import datetime, date

import processing_core as proc


def export_search_json(rows, query):
    data = proc.search_video(rows, query)
    p = _out_path("search_result.json")
    _write_json(p, data)
    return p


def export_top10(rows, metric, fmt):
    data = proc.top10_by_metric(rows, metric)
    if fmt == "json":
        p = _out_path("top10.json")
        _write_json(p, data)
        return p
    p = _out_path("top10.csv")
    _write_csv(p, data)
    return p


def export_first_n(rows, n):
    n = int(n)
    if n < 0:
        n = 0
    data = [_clean(r) for r in rows[:n]]
    p = _out_path(f"first_{n}.csv")
    _write_csv(p, data)
    return p


def export_category_averages(rows):
    data = proc.avg_engagement_by_category(rows)
    p = _out_path("category_averages.json")
    _write_json(p, data)
    return p


def export_filtered_csv(rows, filt):
    mode = filt.get("mode")
    out = rows

    if mode == "category_id":
        cid = filt.get("category_id")
        out = [r for r in out if r.get("category_id") == cid]
    elif mode == "channel_title":
        ch = filt.get("channel_title") or ""
        out = [r for r in out if (r.get("channel_title") or "") == ch]
    else:
        a = _ymd(filt.get("start"))
        b = _ymd(filt.get("end"))
        if a and b:
            out = [r for r in out if isinstance(r.get("trending_date"), date) and a <= r.get("trending_date") <= b]

    data = [_clean(r) for r in out]
    p = _out_path("filtered.csv")
    _write_csv(p, data)
    return p


def export_recommendations(rows, query, k):
    data = proc.recommend_similar(rows, query, int(k))
    p = _out_path("recommendations.json")
    _write_json(p, data)
    return p


def export_anomalies(rows):
    data = proc.anomaly_scan(rows)
    p = _out_path("anomalies.json")
    _write_json(p, data)
    return p


def _ymd(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        return None


def _out_path(name):
    base = os.path.join(os.getcwd(), "exports")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, name)


def _clean(r):
    d = dict(r)
    for k, v in list(d.items()):
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
    return d


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _write_csv(path, rows):
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("")
        return
    keys = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
