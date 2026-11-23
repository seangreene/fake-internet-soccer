# Fake Internet Soccer

The website for the Fake Internet Soccer fantasy league: a bump chart of the standings race, a head-to-head grid and a current-form table for each season, built with the LA Times' [Baker](https://github.com/datadesk/baker) and charted in Datawrapper.

## How it works

1. **Data:** `_workspace/standings.ipynb` and `_workspace/scores.ipynb` pull each gameweek from Fantrax.
2. **Charts:** the same notebooks upload the data to Datawrapper and publish the charts.
3. **Site:** Baker builds the page. Before every build, `_workspace/datawrapper-versions.mjs` looks up each chart's newest published version so the page never shows a stale one.
4. **Hosting:** the built `_dist` folder is uploaded to S3.

On GitHub, steps 1–4 run on their own: **Update charts** runs the notebooks Sunday, Monday and Tuesday at 4 p.m. Pacific (5 p.m. during daylight time), commits the data and then starts **Deploy to production**.

## Setup

```sh
npm install
make install          # Python packages for the notebooks
```

Put a Datawrapper API token (scopes: chart:read, chart:write) in a `.env` file at the repo root. It's git-ignored.

```
DATAWRAPPER_API_TOKEN=your-token
```

`.env` takes priority over a token exported in your shell. If your notebooks run in a different Python, pass it along: `make update PYTHON=/path/to/python`.

## Everyday commands

| Command | What it does |
|---|---|
| `npm start` | Local preview with live reload |
| `make update` | Run both notebooks for the newest season |
| `make update LATEST_GW=10` | Force the gameweek instead of auto-detecting it |
| `make update SEASON=15` | Run a specific season |
| `make standings` / `make scores` | Run one notebook |
| `make recolor` | Re-apply `team-colors.json` to every season's bump chart and republish |

The executed notebooks land in `_workspace/runs/`. Open one to see which cell failed.

## Starting a new season

1. Add the Fantrax league ID to `_workspace/seasons.json`:
   ```json
   "17": { "league_id": "..." }
   ```
2. Add any new or renamed teams to `_workspace/data/team-colors.json`.
3. Update the headline in `_data/meta.aml`.
4. Run `make update`. The first run copies last season's Datawrapper charts, strips "(Copy)" from their titles and records the new chart IDs in `_data/charts.json`.

## Team colors

`_workspace/data/team-colors.json` maps every team name from every season to a color, in the same `{"Team name": "#hex"}` shape Datawrapper uses. A team that's missing (or set to `"TK"`) still gets a temporary unused color and a printed warning, so a mid-season rename never breaks a run. Names have to match Fantrax exactly.

## The form table

One Datawrapper table (`JePAw`, set in `_data/form.json`) is overwritten on each run of the newest season, never copied per season. Its columns are always `-4 … Latest` so the cell colors stay attached. Results are ✓ / ✗ / – (en dash), and the colors live in `FORM_BACKGROUND` and `FORM_TEXT` in `scores.ipynb`. The site hides the form table when an older season is selected.

## Deploying

Go to the repo's **Actions** tab, then **Deploy to production**, then **Run workflow**. Publishing a release works too. It needs these repository secrets:

- `BAKER_AWS_ACCESS_KEY_ID`, `BAKER_AWS_SECRET_ACCESS_KEY`
- `BAKER_AWS_S3_PRODUCTION_REGION`, `BAKER_AWS_S3_PRODUCTION_BUCKET`
- `DATAWRAPPER_API_TOKEN` (also used by **Update charts**)

The site is uploaded to the bucket root because `slug` in `meta.aml` is empty.

## Files

| Path | What's in it |
|---|---|
| `_data/charts.json` | Datawrapper chart IDs and versions per season |
| `_data/form.json` | The form table's chart ID and version |
| `_workspace/seasons.json` | Fantrax league ID per season |
| `_workspace/dw_helpers.py` | Datawrapper: token, chart copying, publishing |
| `_workspace/fantrax_helpers.py` | Fantrax: standings requests, latest-gameweek detection |
| `_workspace/recolor_charts.py` | `make recolor` |
| `_workspace/archive/` | Old per-season notebooks (S12–S16) and the old color CSV, for reference only |

## Troubleshooting

- **401/403 from Datawrapper:** the token in `.env` is wrong, deleted or missing a scope.
- **Fantrax step fails or returns nothing:** Fantrax isn't an official API. The requests pretend to be its website (`"v": "185.0.1"` in `fantrax_helpers.py` and the notebooks), and that may need bumping. Fantrax could also be blocking GitHub's servers, in which case run `make update` locally.
- **Wrong gameweek:** auto-detection counts a gameweek once Fantrax adds it to the standings. Override with `LATEST_GW`.
