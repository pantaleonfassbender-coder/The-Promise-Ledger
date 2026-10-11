"""From raw series to statuses. The rules are fixed in code and documented on the methods page:

baseline  the last observation before the inauguration: December 2024 for monthly data, the last week ending
          before January 20, 2025 for weekly data (for trailing windows: the window ending there).
change    percent change, or the difference for rates and balances.
band      a change counts only if it exceeds the spread of changes over the same span before 2025: the standard
          deviation of all changes over that many periods in the series' own history from 2010 to 2024, leaving
          out March 2020 to December 2021. With too little history the band is not computed and the sign decides.
status    better / unchanged / worse, measured in the direction the promise points; "stale" when the latest
          observation is older than the indicator's own limit (stale indicators do not count).
promise   on track: at least half of its counted indicators better and none worse; off track: at least half
          worse; mixed otherwise; no current data when nothing counts. There is no weighting and no total score.
"""
import datetime as dt
import statistics

INAUG = dt.date(2025, 1, 20)


def pdate(key):
    """Reference date of a period key: end of month for 'YYYY-MM', the date itself otherwise."""
    if len(key) == 7:
        y, m = int(key[:4]), int(key[5:])
        return (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
    return dt.date.fromisoformat(key)


def in_pandemic(key):
    return "2020-03" <= key[:7] <= "2021-12"


def consecutive(keys, freq):
    """Check that a run of keys has no gaps (monthly: next month; weekly: 7 days apart)."""
    for a, b in zip(keys, keys[1:]):
        if freq == "M":
            ya, ma = int(a[:4]), int(a[5:7])
            if (ya * 12 + ma) + 1 != int(b[:4]) * 12 + int(b[5:7]):
                return False
        elif freq == "W" and (pdate(b) - pdate(a)).days != 7:
            return False
    return True


def window_keys(last, n, freq):
    if freq == "M":
        y, m = int(last[:4]), int(last[5:7])
        idx = y * 12 + m - 1
        return [f"{(i // 12):04d}-{(i % 12) + 1:02d}" for i in range(idx - n + 1, idx + 1)]
    d = pdate(last)
    return [(d - dt.timedelta(days=7 * j)).isoformat() for j in range(n - 1, -1, -1)]


def transform(series, k):
    keys = sorted(series)
    if k["transform"] == "level":
        return [(x, series[x]) for x in keys]
    if k["transform"] == "trail":
        # A window is the n calendar months (or weeks) ending at a key. Totals need every period; averages accept
        # one missing period (for example the October 2025 data that BLS never collected during the shutdown).
        n, out = k["window"], []
        for x in keys:
            win = window_keys(x, n, k["freq"])
            have = [series[w] for w in win if w in series]
            need = n if k["agg"] == "sum" else n - 1
            if len(have) >= need:
                out.append((x, sum(have) if k["agg"] == "sum" else sum(have) / len(have)))
        return out
    if k["transform"] == "yoy":
        out = []
        for x in keys:
            prev = f"{int(x[:4]) - 1:04d}{x[4:]}"
            if prev in series and series[prev]:
                out.append((x, (series[x] / series[prev] - 1) * 100))
        return out
    raise ValueError(k["transform"])


def change(a, b, kind):
    if kind == "pct":
        return None if a == 0 else (b / a - 1) * 100
    return b - a


def evaluate(k, series, today):
    t = transform(series, k)
    if not t:
        return dict(status="no data")
    pre = [(x, v) for x, v in t if pdate(x) < INAUG and (k["freq"] != "M" or x <= "2024-12")]
    if not pre:
        return dict(status="no baseline")
    bkey, bval = pre[-1]
    lkey, lval = t[-1]
    keys = [x for x, _ in t]
    h = keys.index(lkey) - keys.index(bkey)
    ch = change(bval, lval, k["change"])
    sign = 1 if k["better"] == "higher" else -1
    # noise band from the history before 2025
    hist = [(x, v) for x, v in pre if x >= k.get("band_from", "2010")]
    diffs = []
    for i in range(len(hist) - h if h > 0 else 0):
        (x0, v0), (x1, v1) = hist[i], hist[i + h]
        if in_pandemic(x0) or in_pandemic(x1):
            continue
        c = change(v0, v1, k["change"])
        if c is not None:
            diffs.append(c)
    band = statistics.pstdev(diffs) if len(diffs) >= 8 else None
    age = (today - pdate(lkey)).days
    if h <= 0:
        status = "no new data"
    elif age > k["max_age"]:
        status = "stale"
    elif ch is None:
        status = "no data"
    else:
        imp = sign * ch
        thr = band if band is not None else 0.0
        status = "better" if imp > thr else "worse" if imp < -thr else "unchanged"
    res = dict(baseline=dict(period=bkey, value=bval), latest=dict(period=lkey, value=lval), change=ch, change_kind=k["change"],
               band=band, band_n=len(diffs), status=status, age_days=age, span=h)
    if "target" in k:
        res["target"] = k["target"]
        res["progress"] = None if k["target"] == bval else (lval - bval) / (k["target"] - bval) * 100
    res["spark"] = [(x, round(v, 4)) for x, v in t if x >= "2023-01"]
    return res


def promise_status(kpis):
    counted = [r["status"] for r in kpis if r["status"] in ("better", "unchanged", "worse")]
    if not counted:
        return "no current data"
    n = len(counted)
    if counted.count("better") * 2 >= n and "worse" not in counted:
        return "on track"
    if counted.count("worse") * 2 >= n:
        return "off track"
    return "mixed"
