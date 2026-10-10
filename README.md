# GoldSrc Addon Stats

Daily census of public Half-Life 1 servers: which addons run where, on which
version, per game mod, per country. A spiritual successor of the
[AMX Mod X addon stats](https://www.amxmodx.org/stats.php), rebuilt from
scratch and open to any addon or mod via pull request.

Live dashboard: https://yapb.github.io/stats/

## What is counted

- **Mods** (`config/mods.yml`): game mods keyed by gamedir, from Counter-Strike
  to exotic ones like Bumper Cars. Add missing ones via PR.
- **Addons** (`config/tracked_vars.yml`): server rules counted AMX stats style,
  from `yb_version` and `amxmodx_version` down to single-server plugins.
  Flags: `novalue` counts presence only (settings, not versions), `any_of`
  matches any of several keys (engine fingerprints like Xash3D).
- **Countries**: offline GeoIP, per mod and per addon breakdowns.
- **Top maps** per mod, **mystery bots** (bots with no recognized bot addon),
  **fresh versions** (first seen this run).

Servers that ignore A2S rules land in the `unknown` bucket: reported openly,
not silently dropped. Redirect farms (hosts with over 100 master entries) and
impossible headcounts are cut before scanning.

## Data sources (all merged, all PR-editable)

- Steam Web API master list per appid, with per-map fan-out past the 10k cap.
- Community UDP masters (`config/custom_masters.yml`): Varq, ds-servers,
  CSDownload and dozens more, queried in parallel.
- Static HTTP lists (`config/static_lists.yml`): Elinsrc and FWGS curated lists.

## Dashboard (`web/`, Vue 3 + ECharts, static build)

Overview with filters by addon and version, per-addon pages (`/addon/<name>`,
Addon x Mod table, tracked values, version history), per-mod pages
(`/mod/<gamedir>`, addons, top maps, history), per-country pages
(`/country/<cc>`), sortable tables, daily history with server/player modes.
Deployed to GitHub Pages on every run.

## Collector (`collector/`, Python)

Stages: `config`, `steam_master`, `legacy_master`, `static_lists`, `masters`
(merge), `farm` (filter), `probe` (A2S INFO/RULES with progress),
`a2s_rules` (GoldSrc/Source split packets), `geo` (offline mmdb),
`aggregate` (`latest.json` + `history.json`).

```sh
pip install -r collector/requirements.txt
STEAM_WEBAPI_KEY=<key> python collector/collect.py --out web/data
python collector/tests/test_smoke.py
```

A free key at https://steamcommunity.com/dev/apikey (any domain works) lives
in the repository secret, never in commits. Useful flags: `--appid` (subset),
`--max-addrs` (cap probes), `--master-cache`/`--save-master` (offline master
reuse), `--max-servers-per-host` (farm threshold, 0 disables), `--skip-a2s`,
`--geoip-mmdb` (country stats).

Runs daily at 03:17 UTC via GitHub Actions (cron plus manual dispatch), with
a fail-fast self test before the scan.
