# The Promise Ledger

Twelve promises of the second Trump administration, each quoted from its primary source (the inaugural address of
January 20, 2025, executive orders, a presidential memorandum), measured every Monday at 9:00 a.m. US Eastern against
official data, from a fixed baseline: the last data before the inauguration.

- **No hand on the numbers.** A GitHub Action (`.github/workflows/weekly.yml`) fetches every indicator from the
  publishing agency, evaluates it by fixed rules (`scripts/evaluate.py`) and commits the result. There is no manual
  entry, no language model, no weighting and no total score. The commit history is the audit trail.
- **When a change counts.** Only if it exceeds the spread of changes over the same span in the series' own history
  from 2010 to 2024 (pandemic months left out).
- **Statuses.** Indicators: toward the promise / within normal range / away from the promise / stale (direction only, no verdict). Promises: on track (at least half
  toward the promise, none away from the promise), off track (at least half away from the promise), mixed, no current data. Headline: promises on track among those with current data.

## Sources (no API keys)

BLS public API · EIA history files · Federal Reserve G.17 · Treasury Monthly and Daily Treasury Statement
(fiscaldata) · Census FT-900 · CBP Nationwide Encounters and ICE Detention Statistics (read from the Deportation Data
Project's CC0 mirrors, because cbp.gov and ice.gov refuse automated requests) · ICE removal records released under
FOIA to the Deportation Data Project (CC0).

DHS's monthly enforcement tables stop at November 2024; the ledger says so on the page instead of filling the gap.

## Files

- `scripts/registry.py`: promises, quotations, indicators. `scripts/fetch.py`: source adapters.
  `scripts/evaluate.py`: baseline, band, status. `scripts/run.py`: the weekly run.
- `data/series/*.json`: the archive of every series (a source that drops old months never erases them here).
  `data/cache/`: aggregates of the large FOIA files, re-read only when the files change.
- `site/`: the static page (Netlify publishes this folder). `site/data/status.json` and `site/data/history.jsonl`.

Run locally: `pip install openpyxl xlrd && python scripts/run.py`

Licence: code MIT; texts CC BY 4.0; data public domain or CC0 (see `LICENSE`).
