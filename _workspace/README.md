# What is this?

This folder is a safe place for putting scripts and other files you don't want Baker to serve or publish. It's a good spot to put AI files, notebooks and other hodge podge.

## Updating the league charts

- `standings.ipynb` and `scores.ipynb` run any season listed in `seasons.json` (newest by default). Run both with `make update` from the repo root; GitHub Actions does this on a schedule (`.github/workflows/update-charts.yml`).
- New season: add `"17": { "league_id": "..." }` to `seasons.json`. The first run copies last season's Datawrapper charts and records them in `_data/charts.json`.
- The Datawrapper token goes in `.env` at the repo root as `DATAWRAPPER_API_TOKEN=...` (git-ignored).
- `archive/` holds the old one-notebook-per-season versions (Seasons 12–16), kept for reference. They aren't meant to be re-run from there.
