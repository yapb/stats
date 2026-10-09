# Addons Stats

Daily census of public Half-Life 1 servers: which server addons run where,
on which version, per game mod. Think AMX Mod X addon stats, but rebuilt from
scratch and open to any addon via pull request. Out of the box it tracks
[YaPB](https://github.com/yapb/yapb), [AMX Mod X](https://www.amxmodx.org/)
and [Metamod](http://www.metamod.org/). Addons expose themselves through
server rules, so nothing needs to be installed on servers to count them.

- **Collector** (`collector/`): Python. Steam Web API master list plus A2S
  `INFO`/`RULES` scan.
- **Config** (`config/`): tracked mods and addon cvars. Add yours via PR.
- **Dashboard** (`web/`): static site, rebuilt daily by GitHub Actions.
- **Data** (`web/data/`): machine-readable snapshots (`latest.json`,
  `history.json`).

Live dashboard: https://yapb.github.io/stats/ (after the first scheduled run).

## Add a mod or an addon (via PR)

- `config/mods.yml`: one entry per game (`appid`, `gamedir`, `name`, `url`).
  `appid` is used for the master server filter.
- `config/tracked_vars.yml`: one entry per counted server rule (`name` is the
  exact rule key, plus `title` and `url` for display).

## Run the collector locally

```sh
pip install -r collector/requirements.txt
STEAM_WEBAPI_KEY=<key> python collector/collect.py --out web/data
```

Get a key (free) at https://steamcommunity.com/dev/apikey, any domain works.
The key only travels via environment or repository secret, never in commits.

## How it works

1. `IGameServersService/GetServerList` per tracked `appid` (`limit=10000`).
   Capped answers get split further per map (same trick as the blaster.net
   fan-out).
2. Every address gets A2S `INFO` plus `RULES` (concurrent, short timeouts).
   SDR (`169.254.x.x`) entries are unreachable over UDP, counted separately.
3. Aggregates go to `web/data/latest.json`, a daily row is appended to
   `web/data/history.json`. No per-server data lands in git.
4. Servers that ignore A2S rules (firewalled majority) land in the `unknown`
   bucket: reported openly, not silently dropped.
