// Looks up the latest published version of every Datawrapper chart listed in
// _data/charts.json and _data/form.json and writes them to _data/datawrapper_versions.json, which
// Baker exposes to templates as `datawrapper_versions`. scripts/app.js uses
// those versions ahead of the ones in charts.json, so the page always embeds
// the newest published chart instead of a cached older one.
//
// Runs automatically before `npm start` and `npm run build` (see package.json).
// It never fails the build: if a lookup fails, the chart falls back to the
// `version` in charts.json.
//
// If a Datawrapper token is available (DATAWRAPPER_TOKEN or
// DATAWRAPPER_API_TOKEN in the environment, or DATAWRAPPER_API_TOKEN in the
// repo's .env file), it asks the Datawrapper API (most reliable). Otherwise it
// reads the redirect on the chart's versionless dwcdn URL.
//
// Uses node:https rather than fetch so it runs on any Node version.

import { readFile, writeFile } from 'node:fs/promises';
import https from 'node:https';

const CHARTS_PATH = '_data/charts.json';
const FORM_PATH = '_data/form.json';
const OUT_PATH = '_data/datawrapper_versions.json';

async function getToken() {
  const fromEnv = process.env.DATAWRAPPER_TOKEN || process.env.DATAWRAPPER_API_TOKEN;
  if (fromEnv) return fromEnv;
  try {
    const dotenv = await readFile('.env', 'utf8');
    const match = dotenv.match(/^\s*(?:export\s+)?DATAWRAPPER_API_TOKEN\s*=\s*["']?([^"'\s]+)/m);
    return match ? match[1] : undefined;
  } catch {
    return undefined;
  }
}

// GET a URL, following redirects. Resolves to { status, url, body }.
function get(url, headers = {}, redirectsLeft = 5) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers }, (res) => {
      const { statusCode, headers: resHeaders } = res;
      if (statusCode >= 300 && statusCode < 400 && resHeaders.location && redirectsLeft > 0) {
        res.resume();
        const next = new URL(resHeaders.location, url).toString();
        resolve(get(next, headers, redirectsLeft - 1));
        return;
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => resolve({ status: statusCode, url, body }));
    });
    req.setTimeout(10000, () => req.destroy(new Error('timed out')));
    req.on('error', reject);
  });
}

async function fromApi(id, token) {
  const res = await get(`https://api.datawrapper.de/v3/charts/${id}`, {
    Authorization: `Bearer ${token}`,
  });
  if (res.status !== 200) throw new Error(`API returned ${res.status}`);
  const { publicVersion } = JSON.parse(res.body);
  if (!publicVersion) throw new Error('chart is not published');
  return publicVersion;
}

async function fromCdn(id) {
  // The versionless URL answers with a redirect (HTTP or <meta refresh>)
  // pointing at /{id}/{latestVersion}/
  const res = await get(`https://datawrapper.dwcdn.net/${id}/?t=${Date.now()}`);
  const match = `${res.url}\n${res.body}`.match(new RegExp(`/${id}/(\\d+)/`));
  if (!match) throw new Error(`no version found in response (HTTP ${res.status})`);
  return Number(match[1]);
}

const token = await getToken();
const charts = JSON.parse(await readFile(CHARTS_PATH, 'utf8'));
const ids = [
  ...new Set(
    Object.values(charts)
      .flatMap((season) => Object.values(season))
      .map((chart) => chart.chart_id)
      .concat(JSON.parse(await readFile(FORM_PATH, 'utf8')).chart_id)
      .filter(Boolean)
  ),
];

const versions = {};
await Promise.all(
  ids.map(async (id) => {
    try {
      versions[id] = token ? await fromApi(id, token) : await fromCdn(id);
      console.log(`[datawrapper] ${id} -> v${versions[id]}`);
    } catch (err) {
      console.warn(`[datawrapper] ${id}: ${err.message}; using version from charts.json`);
    }
  })
);

// sort keys so the file doesn't reshuffle between runs
const sorted = Object.fromEntries(Object.entries(versions).sort(([a], [b]) => a.localeCompare(b)));
await writeFile(OUT_PATH, JSON.stringify(sorted, null, 2) + '\n');
