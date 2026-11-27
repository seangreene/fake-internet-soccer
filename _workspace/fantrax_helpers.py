"""Shared Fantrax helpers for the season notebooks.

All Fantrax requests live here. Fantrax isn't an official API: the requests pose
as its website, so if they start failing, FANTRAX_VERSION is the first thing to bump
(find the current value in your browser's network tab: any fxpa/req request, "v").
"""
import os
from functools import lru_cache

import pandas as pd
import requests

FANTRAX_VERSION = '185.0.1'
FANTRAX_URL = 'https://www.fantrax.com/fxpa/req'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
MAX_GW = 38

_sessions = {}


def _session(league_id):
    """One session per league, opened by visiting the league page for cookies."""
    if league_id not in _sessions:
        s = requests.Session()
        s.headers['user-agent'] = USER_AGENT
        s.get(f'https://www.fantrax.com/fantasy/league/{league_id}/standings', timeout=30)
        _sessions[league_id] = s
    return _sessions[league_id]


@lru_cache(maxsize=None)
def get_standings(league_id, period):
    """Raw getStandings response data for one gameweek.

    The response holds both the cumulative standings ("Standings" table) and that
    gameweek's matchups ("Gameweek N" table). Cached, so detecting the latest
    gameweek and then fetching the data doesn't request anything twice.
    """
    ref = (f'https://www.fantrax.com/fantasy/league/{league_id}/standings;'
           f'view=REGULAR_SEASON;timeframeType=BY_PERIOD;timeStartType=FROM_SEASON_START;period={period}')
    payload = {
        'msgs': [{
            'method': 'getStandings',
            'data': {
                'leagueId': league_id,
                'view': 'REGULAR_SEASON',
                'timeframeType': 'BY_PERIOD',
                'timeStartType': 'FROM_SEASON_START',
                'period': str(period),
            },
        }],
        'uiv': 3, 'refUrl': ref, 'dt': 1, 'at': 0, 'av': '0.0',
        'tz': 'America/Los_Angeles', 'v': FANTRAX_VERSION,
    }
    headers = {
        'accept': 'application/json',
        'content-type': 'text/plain',
        'origin': 'https://www.fantrax.com',
        'referer': ref,
    }
    r = _session(league_id).post(f'{FANTRAX_URL}?leagueId={league_id}', headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()['responses'][0]['data']


def to_number(values):
    """Fantrax formats numbers for display, so 1000+ arrives as "1,012.5". Strip the commas."""
    return pd.to_numeric(pd.Series(values).astype(str).str.replace(',', '', regex=False), errors='coerce')


def _table(data, caption):
    return next((t for t in data.get('tableList', []) if t.get('caption') == caption), None)


def fetch_standings(league_id, latest_gw):
    """Standings after each gameweek, 1..latest_gw. Returns (DataFrame, team_info)."""
    records, team_info = [], {}
    for period in range(1, latest_gw + 1):
        data = get_standings(league_id, period)
        team_info = data.get('fantasyTeamInfo', {})
        tbl = _table(data, 'Standings')
        if not tbl:
            print(f'Period {period}: Standings table not found')
            continue
        for row in tbl.get('rows', []):
            fixed = row.get('fixedCells', [])
            cells = row.get('cells', [])
            cell = lambda i: cells[i].get('content') if len(cells) > i else None
            team_cell = fixed[1] if len(fixed) > 1 else {}
            ti = team_info.get(team_cell.get('teamId'), {})
            records.append({
                'gw': period,
                'rank': fixed[0].get('content') if fixed else None,
                'teamId': team_cell.get('teamId'),
                'team': team_cell.get('content'),
                'shortName': ti.get('shortName'),
                'logo': ti.get('logoUrl512'),
                # header order for cells: W, D, L, Points, Win%, WW, FPtsF, FPtsA, Streak
                'W': cell(0), 'D': cell(1), 'L': cell(2), 'Points': cell(3), 'Win%': cell(4),
                'WW': cell(5), 'FPtsF': cell(6), 'FPtsA': cell(7), 'Streak': cell(8),
            })
    df = pd.DataFrame(records)
    for col in ['rank', 'W', 'D', 'L', 'Points', 'Win%', 'WW', 'FPtsF', 'FPtsA']:
        df[col] = to_number(df[col])
    return df, team_info


def fetch_matchups(league_id, latest_gw):
    """Every head-to-head matchup, gameweeks 1..latest_gw. Returns (DataFrame, team_info)."""
    records, team_info = [], {}
    for period in range(1, latest_gw + 1):
        data = get_standings(league_id, period)
        team_info = data.get('fantasyTeamInfo', {})
        tbl = _table(data, f'Gameweek {period}')
        if not tbl:
            print(f'Period {period}: Head-to-head table not found')
            continue
        for row in tbl['rows']:
            c = row['cells']
            records.append({
                'gw': period,
                'away_team': c[0]['content'],
                'home_team': c[2]['content'],
                'away_score': float(str(c[1]['content']).replace(',', '')),
                'home_score': float(str(c[3]['content']).replace(',', '')),
            })
    return pd.DataFrame(records), team_info


def games_played(data):
    """Total W + D + L across all teams in a standings response, or None if no table."""
    tbl = next((t for t in data.get('tableList', []) if t.get('caption') == 'Standings'), None)
    if not tbl:
        return None
    total = 0
    for row in tbl.get('rows', []):
        for cell in row.get('cells', [])[:3]:  # W, D, L
            try:
                total += int(float(cell.get('content') or 0))
            except ValueError:
                pass
    return total


def latest_completed_gw(league_id):
    """Last gameweek whose results Fantrax has counted in the standings.

    A gameweek counts as complete when the league's total games played went up
    compared with the gameweek before it. Gameweeks that haven't been scored
    yet (or are still in progress) don't move that total.
    """
    latest, prev = 0, 0
    for period in range(1, MAX_GW + 1):
        try:
            gp = games_played(get_standings(league_id, period))
        except (requests.RequestException, KeyError, IndexError, ValueError):
            gp = None
        if gp is None:
            break
        if gp > prev:
            latest = period
        prev = max(prev, gp)
    return latest


def resolve_latest_gw(league_id):
    """LATEST_GW from the environment if set, otherwise auto-detect."""
    override = os.environ.get('LATEST_GW', '').strip()
    gw = int(override) if override else latest_completed_gw(league_id)
    if gw < 1:
        raise RuntimeError('No completed gameweeks found in Fantrax yet.')
    print(f'latest_gw = {gw}' + (' (from LATEST_GW)' if override else ' (auto-detected)'))
    return gw
