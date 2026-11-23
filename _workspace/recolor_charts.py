"""Re-apply data/team-colors.json to every season's standings (line) chart and republish.

    make recolor                 # every season in _data/charts.json
    make recolor SEASON=15       # just one

Team names are read from each chart's own data in Datawrapper, so the colors
match exactly what the chart plots. Stops before touching a chart if any of its
teams has no color in team-colors.json.
"""
import csv
import io
import json
import os
import sys
from pathlib import Path

import requests

import dw_helpers as dw

HERE = Path(__file__).resolve().parent
team_colors = json.loads((HERE / 'data' / 'team-colors.json').read_text(encoding='utf-8'))


def chart_teams(chart_id):
    """Series names in a line chart = its data's column headers after the x column."""
    r = requests.get(f'{dw.BASE_URL}/{chart_id}/data', headers=dw.headers('text/csv'))
    dw.check(r)
    header = next(csv.reader(io.StringIO(r.text)))
    return [h for h in header[1:] if h]


def recolor(season, chart_id):
    teams = chart_teams(chart_id)
    missing = [t for t in teams if not str(team_colors.get(t, '')).startswith('#')]
    if missing:
        print(f'Season {season}: skipped, no color for {missing}')
        return False
    color_map = {t: team_colors[t] for t in teams}
    r = requests.patch(
        f'{dw.BASE_URL}/{chart_id}',
        json={'metadata': {'visualize': {'color-category': {'map': color_map}}}},
        headers=dw.headers(),
    )
    dw.check(r)
    dw.publish(chart_id, season, 'standings')
    print(f'Season {season}: recolored {len(teams)} teams')
    return True


def main():
    charts = dw.load_charts()
    only = os.environ.get('SEASON', '').strip()
    seasons = [only] if only else sorted(charts, key=int)
    results = [recolor(s, charts[s]['standings']['chart_id']) for s in seasons]
    if not all(results):
        sys.exit(1)


if __name__ == '__main__':
    main()
