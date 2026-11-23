"""Shared Datawrapper helpers for the season notebooks."""
import json
import os
import re
from pathlib import Path

import requests

BASE_URL = 'https://api.datawrapper.de/v3/charts'
CHARTS_JSON = Path(__file__).resolve().parent.parent / '_data' / 'charts.json'


ENV_FILE = Path(__file__).resolve().parent.parent / '.env'


def get_token():
    """Read the token from the environment, or from a .env file at the repo root."""
    token = os.environ.get('DATAWRAPPER_API_TOKEN')
    if not token and ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            key, _, value = line.partition('=')
            if key.replace('export ', '').strip() == 'DATAWRAPPER_API_TOKEN':
                token = value.strip().strip('"').strip("'")
    if not token:
        raise RuntimeError(
            f'No Datawrapper token found. Add this line to {ENV_FILE}:\n'
            '  DATAWRAPPER_API_TOKEN=your-token'
        )
    return token


def headers(content_type='application/json'):
    return {
        'accept': '*/*',
        'Authorization': f'Bearer {get_token()}',
        'content-type': content_type,
    }


def load_charts():
    with CHARTS_JSON.open(encoding='utf-8') as f:
        return json.load(f)


def save_charts(charts):
    with CHARTS_JSON.open('w', encoding='utf-8') as f:
        json.dump(charts, f, indent=2)


def fix_title(chart_id, season, template_season):
    """Drop Datawrapper's "(Copy)" suffix and swap the old season number for the new one."""
    r = requests.get(f'{BASE_URL}/{chart_id}', headers=headers())
    r.raise_for_status()
    old_title = r.json().get('title') or ''
    new_title = re.sub(r'\s*\(Copy\)\s*$', '', old_title)
    new_title = new_title.replace(f'Season {template_season}', f'Season {season}')
    if new_title != old_title:
        p = requests.patch(f'{BASE_URL}/{chart_id}', json={'title': new_title}, headers=headers())
        p.raise_for_status()
        print(f'Retitled {chart_id}: {old_title!r} -> {new_title!r}')


def ensure_season_charts(season, template_season):
    """Make sure `season` has standings + h2h charts in charts.json.

    Missing charts are created by copying the template season's charts in
    Datawrapper. Both chart types are created together so the site never
    sees a season with only one of them.
    """
    season, template_season = str(season), str(template_season)
    charts = load_charts()
    entry = charts.get(season, {})

    for kind in ('standings', 'h2h'):
        if entry.get(kind, {}).get('chart_id'):
            # already exists; still tidy the title in case an earlier run left "(Copy)"
            fix_title(entry[kind]['chart_id'], season, template_season)
            continue
        src_id = charts[template_season][kind]['chart_id']
        r = requests.post(f'{BASE_URL}/{src_id}/copy', headers=headers())
        r.raise_for_status()
        new_id = r.json()['id']
        print(f'Created Season {season} {kind} chart {new_id} (copy of {src_id})')
        entry[kind] = {'chart_id': new_id, 'version': 0}
        charts[season] = entry
        save_charts(charts)  # save right away so a later error can't cause duplicate copies
        fix_title(new_id, season, template_season)

    charts[season] = entry
    save_charts(charts)
    return entry


def publish(chart_id, season, kind):
    """Publish a chart and record its new public version in charts.json."""
    r = requests.post(f'{BASE_URL}/{chart_id}/publish', headers=headers())
    r.raise_for_status()
    version = r.json()['data']['publicVersion']
    charts = load_charts()
    charts[str(season)][kind]['version'] = version
    save_charts(charts)
    print(f'Published {kind} chart {chart_id} v{version}')
    return version
