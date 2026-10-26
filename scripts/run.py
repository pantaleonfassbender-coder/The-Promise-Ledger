"""The weekly run (GitHub Action, Mondays from 9:00 a.m. US Eastern, started by GitHub's schedule or by a timer on
Netlify): fetch every source, merge into the archive (data/series/*.json; a source that drops old months never erases
them here), evaluate, write site/data/status.json and append one line to site/data/history.jsonl. The commit history is the audit trail.
Run from the repository root:  python scripts/run.py
"""
import datetime as dt
import json
import os
import sys
import time
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch  # noqa: E402
from evaluate import evaluate, promise_status  # noqa: E402
from registry import PROMISES, SOURCES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "data" / "series"
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "site" / "data"
ET = ZoneInfo("America/New_York")
WEEKLY_KINDS = ("schedule", "external schedule", "catch-up")  # the runs that make up the weekly trend


def kind_of_run(now_utc):
    """Which run is this? Every run is stamped with its own time (US Eastern); nothing is backdated.
    - 'schedule': started by GitHub's schedule on a Monday at or after 9:00 a.m. ET (GitHub may start it late);
    - 'external schedule': started by the timer on Netlify (netlify/functions/weekly-dispatch.mjs), which starts the
      workflow with the switch 'external' on; same rule as 'schedule' (Monday, 9:00 a.m. ET or later);
    - 'catch-up': started by hand with the catch-up switch on a Monday, when both timers missed;
    - 'manual': any other run (e.g. after a correction to the code): shown, but left out of the weekly trend.
    Returns (stamp, kind, weekly) or None when a scheduled run should not write (too early for 9:00 a.m. ET in this
    season, or this Monday's weekly run already exists)."""
    et = now_utc.astimezone(ET)
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    catchup, external = os.environ.get("CATCHUP", "") == "true", os.environ.get("EXTERNAL", "") == "true"
    monday = et.weekday() == 0
    if event == "schedule" or (event == "workflow_dispatch" and external):
        if not monday or et.hour < 9:
            return None
        kind = "schedule" if event == "schedule" else "external schedule"
    elif catchup and monday:
        kind = "catch-up"
    else:
        kind = "manual"
    weekly = kind in WEEKLY_KINDS
    if weekly:
        for line in (OUT / "history.jsonl").read_text(encoding="utf-8").splitlines() if (OUT / "history.jsonl").exists() else []:
            h = json.loads(line)
            if h.get("weekly", h.get("scheduled")) and h.get("trigger") in WEEKLY_KINDS and h["as_of"][:10] == et.date().isoformat():
                return None
    return et.replace(second=0, microsecond=0), kind, weekly


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def main():
    t0 = time.time()
    now = dt.datetime.now(dt.timezone.utc)
    run = kind_of_run(now)
    if run is None:
        print("No weekly run due now (before 9:00 a.m. ET, not a Monday, or this Monday's run already exists).")
        return
    stamp, trigger, weekly = run
    ARCH.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    kpis = [k for p in PROMISES for k in p["kpis"]]
    fetched, errors, meta = {}, {}, {}

    def grab(name, fn):
        try:
            res = fn()
            for key, val in res.items():
                if key.startswith("_"):
                    meta[f"{name}{key}"] = val
                else:
                    fetched[(name, key)] = val
        except Exception as e:  # keep going; the archive keeps the last good data
            errors[name] = f"{type(e).__name__}: {e}"
            traceback.print_exc()

    grab("bls", lambda: fetch.bls(sorted({k["series"] for k in kpis if k["source"] == "bls"})))
    for path in sorted({k["series"] for k in kpis if k["source"] == "eia"}):
        freq = next(k["freq"] for k in kpis if k["series"] == path)
        grab("eia", lambda path=path, freq=freq: fetch.eia(path, freq))
    grab("fed", lambda: fetch.fed(sorted({k["series"] for k in kpis if k["source"] == "fed"})))
    grab("mts_customs", fetch.mts_customs)
    grab("mts_outlays", fetch.mts_outlays)
    grab("dts_customs", fetch.dts_customs)
    grab("ft900", fetch.ft900)
    grab("cbp", fetch.cbp)
    grab("ice_adp", fetch.ice_adp)
    foia_cache = load(CACHE / "foia_removals.json", {})
    grab("foia_removals", lambda: fetch.foia_removals(foia_cache))
    (CACHE / "foia_removals.json").write_text(json.dumps(foia_cache), encoding="utf-8")

    today = now.astimezone(ET).date()
    promises, history_kpis = [], {}
    for p in PROMISES:
        rows = []
        for k in p["kpis"]:
            arch_file = ARCH / f"{k['id']}.json"
            arch = load(arch_file, {})
            new = fetched.get((k["source"], k["series"]))
            if new:
                arch.update({x: v for x, v in new.items()})
                arch_file.write_text(json.dumps(dict(sorted(arch.items()))), encoding="utf-8")
            res = evaluate(k, arch, today) if arch else dict(status="no data")
            res.update(id=k["id"], label=k["label"], unit=k["unit"], promised=k["promised"], tier=k["tier"], freq=k["freq"], band_note=k.get("band_note"), max_age=k["max_age"],
                       source=SOURCES[k["source"]], series=k["series"], fetch_error=errors.get(k["source"]))
            rows.append(res)
            history_kpis[k["id"]] = dict(status=res["status"], latest=res.get("latest"), change=res.get("change"))
        promises.append(dict(id=p["id"], title=p["title"], quote=p["quote"], source=p["source"], url=p["url"],
                             note=p.get("note"), status=promise_status(rows), kpis=rows))
    counted = [p for p in promises if p["status"] != "no current data"]
    on = [p for p in counted if p["status"] == "on track"]
    summary = dict(on_track=len(on), counted=len(counted), total=len(promises),
                   off_track=sum(p["status"] == "off track" for p in promises), mixed=sum(p["status"] == "mixed" for p in promises))
    status = dict(as_of=stamp.isoformat(), scheduled=weekly, weekly=weekly, trigger=trigger, generated_utc=now.isoformat(timespec="seconds"), summary=summary,
                  errors=errors, meta={k: v for k, v in meta.items()}, promises=promises, seconds=round(time.time() - t0))
    (OUT / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT / "history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(as_of=status["as_of"], scheduled=weekly, weekly=weekly, trigger=trigger, generated_utc=status["generated_utc"], summary=summary,
                                promises={p["id"]: p["status"] for p in promises}, kpis=history_kpis, errors=sorted(errors))) + "\n")
    print(json.dumps(summary), "errors:", errors, f"{status['seconds']} s")


if __name__ == "__main__":
    main()
