"""Shared Fantrax helpers for the season notebooks."""
import os

import requests

FANTRAX_URL = 'https://www.fantrax.com/fxpa/req'
MAX_GW = 38


def get_standings(league_id, period):
    """Raw getStandings response data for one gameweek (cumulative from season start)."""
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
        'tz': 'America/Los_Angeles', 'v': '185.0.1',
    }
    headers = {
        'accept': 'application/json',
        'content-type': 'text/plain',
        'referer': ref,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    r = requests.post(f'{FANTRAX_URL}?leagueId={league_id}', headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()['responses'][0]['data']


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
