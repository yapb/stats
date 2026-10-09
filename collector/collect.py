"""Addons stats collector: master list (Steam Web API) plus A2S INFO/RULES scan.

Reads config/mods.yml + config/tracked_vars.yml, writes web/data/latest.json
and appends a daily row to web/data/history.json.

    STEAM_WEBAPI_KEY=<key> python collect.py --out ../web/data
"""

from __future__ import annotations

import argparse
import datetime
import ipaddress
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

from a2s_rules import fetch_rules

try:
    import a2s
except ImportError:  # pragma: no cover
    print("missing dependency: pip install -r requirements.txt", file=sys.stderr)
    raise

API_BASE = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
MASTER_LIMIT = 10000  # Steam's per-query cap
MASTER_SPACING = 1.6  # seconds between master calls (200 req / 5 min per key)
SDR_NET = ipaddress.ip_network("169.254.0.0/16")


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def master_call(key, filt, last_call, attempts=7):
    last_exc = None
    for attempt in range(attempts):
        wait = MASTER_SPACING - (time.monotonic() - last_call[0])
        if wait > 0:
            time.sleep(wait)
        params = {"key": key, "filter": filt, "limit": str(MASTER_LIMIT), "format": "json"}
        url = API_BASE + "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                data = json.load(r)
            last_call[0] = time.monotonic()
            return data["response"].get("servers", [])
        except Exception as e:  # Steam API flops sometimes: back off and retry
            last_exc = e
            last_call[0] = time.monotonic()
            print(f"master {filt} attempt {attempt + 1} failed ({e}), backing off", flush=True)
            time.sleep(5 * 2 ** attempt)
    raise last_exc


def fetch_mod(key, mod, last_call):
    """All master entries for one mod; map fan-out when the 10k cap hits."""
    appid = mod["appid"]
    servers = master_call(key, f"\\appid\\{appid}", last_call)
    truncated = len(servers) >= MASTER_LIMIT
    if truncated:
        # Same idea as blaster.net tier-2 fan-out: split the capped answer
        # into per-map queries so dense mods are still (mostly) enumerated.
        # Completeness still isn't provable (maps beyond the cap stay unseen),
        # hence the truncated flag stays set (see quality.truncated_appids).
        maps = sorted({s.get("map", "") for s in servers if s.get("map")})
        extra = {s["addr"]: s for s in servers}
        for i, m in enumerate(maps, 1):
            batch = master_call(key, f"\\appid\\{appid}\\map\\{m}", last_call)
            for s in batch:
                extra.setdefault(s["addr"], s)
            if i % 20 == 0 or i == len(maps):
                print(f"  appid={appid} map fan-out {i}/{len(maps)}"
                      f" ({len(extra)} addrs)", flush=True)
        servers = list(extra.values())
    return servers, truncated


def probe(addr, timeout):
    """A2S INFO + RULES for one addr. Returns a small dict, never raises."""
    host, _, port = addr.rpartition(":")
    out = {"addr": addr}
    try:
        info = a2s.info((host, int(port)), timeout=timeout)
    except Exception as e:  # dead / firewalled / garbage
        out["info_err"] = type(e).__name__
        return out
    out["info"] = {
        "name": info.server_name,
        "map": info.map_name,
        "players": info.player_count,
        "max_players": info.max_players,
        "bots": info.bot_count,
        "os": str(getattr(info, "server_os", "")),
        "gamedir": getattr(info, "folder", ""),
        "vac": bool(info.vac_enabled),
    }
    try:
        goldsrc = isinstance(info, a2s.GoldSrcInfo)
        out["rules"] = fetch_rules(addr, timeout=timeout, goldsrc=goldsrc)
    except Exception as e:
        out["rules_err"] = type(e).__name__
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output dir for latest.json/history.json")
    ap.add_argument("--config-dir", default=os.path.join(os.path.dirname(__file__), "..", "config"))
    ap.add_argument("--workers", type=int, default=100)
    ap.add_argument("--timeout", type=float, default=1.5)
    ap.add_argument("--appid", type=int, action="append", default=None,
                    help="only scan these appids (repeatable; default: all from mods.yml)")
    ap.add_argument("--max-addrs", type=int, default=0,
                    help="cap A2S probes for smoke tests (0 = no cap)")
    ap.add_argument("--save-master", default=None,
                    help="save raw master lists to this JSON file for reuse")
    ap.add_argument("--master-cache", default=None,
                    help="skip the master phase, load lists from a --save-master file")
    args = ap.parse_args()

    key = os.environ.get("STEAM_WEBAPI_KEY", "")
    if not key and not args.master_cache:
        print("STEAM_WEBAPI_KEY is not set", file=sys.stderr)
        return 2

    mods = load_yaml(os.path.join(args.config_dir, "mods.yml"))["mods"]
    tracked = load_yaml(os.path.join(args.config_dir, "tracked_vars.yml"))["vars"]
    if args.appid:
        mods = [m for m in mods if m["appid"] in args.appid]
    tracked_names = [v["name"] for v in tracked]

    last_call = [0.0]

    # --- master phase -----------------------------------------------------
    master = {}  # addr mapped to master entry
    per_mod_master = {}
    truncated_mods = []
    if args.master_cache:
        with open(args.master_cache, encoding="utf-8") as f:
            cache = json.load(f)
        for mod in mods:
            servers = cache["by_appid"].get(str(mod["appid"]), [])
            per_mod_master[mod["appid"]] = len(servers)
            for s in servers:
                master[s["addr"]] = s
        truncated_mods = cache.get("truncated", [])
        print(f"master loaded from cache: {len(master)} addrs", flush=True)
    else:
        for mod in mods:
            servers, truncated = fetch_mod(key, mod, last_call)
            per_mod_master[mod["appid"]] = len(servers)
            if truncated:
                truncated_mods.append(mod["appid"])
            for s in servers:
                master[s["addr"]] = s
            print(f"master appid={mod['appid']}: {len(servers)}"
                  + (" (TRUNCATED)" if truncated else ""), flush=True)
        print(f"master unique addrs: {len(master)}", flush=True)
        if args.save_master:
            with open(args.save_master, "w", encoding="utf-8") as f:
                json.dump({"by_appid": {str(m["appid"]): [
                    s for s in master.values()
                    if s.get("appid") == m["appid"]] for m in mods},
                    "truncated": truncated_mods}, f)

    # --- A2S phase --------------------------------------------------------
    sdr = sum(1 for a in master
              if a.rpartition(":")[0] and _is_sdr(a.rpartition(":")[0]))
    targets = [a for a in master if not _is_sdr(a.rpartition(":")[0])]
    if args.max_addrs:
        targets = targets[:args.max_addrs]
    print(f"A2S targets: {len(targets)} (+{sdr} SDR skipped,"
          f" {args.workers} workers)", flush=True)

    results = []
    done = 0
    started = time.monotonic()
    step = max(1, len(targets) // 40)  # about 40 progress lines per run
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(probe, a, args.timeout) for a in targets]
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % step == 0 or done == len(targets):
                elapsed = time.monotonic() - started
                rate = done / elapsed if elapsed > 0 else 0
                eta = (len(targets) - done) / rate if rate > 0 else 0
                print(f"A2S {done}/{len(targets)} ({100 * done / len(targets):.0f}%)"
                      f" {rate:.0f}/s eta {eta / 60:.0f}m", flush=True)

    # --- aggregate --------------------------------------------------------
    alive = [r for r in results if "info" in r]
    with_rules = [r for r in alive if "rules" in r]

    by_mod = defaultdict(lambda: {"alive": 0, "players": 0, "bots": 0, "with_rules": 0, "max_players": 0})
    for r in alive:
        app = _guess_mod(r, master.get(r["addr"], {}), mods)
        row = by_mod[app]
        row["alive"] += 1
        row["players"] += r["info"]["players"]
        row["bots"] += r["info"]["bots"]
        row["max_players"] += r["info"]["max_players"]

    values = {name: Counter() for name in tracked_names}
    with_addon = {name: 0 for name in tracked_names}
    addon_players = Counter()
    addon_capacity = Counter()
    addon_bots = Counter()
    mod_addon = defaultdict(Counter)  # (appid, var) mapped to value counts
    for r in with_rules:
        app = _guess_mod(r, master.get(r["addr"], {}), mods)
        by_mod[app]["with_rules"] += 1
        for name in tracked_names:
            if name in r["rules"]:
                with_addon[name] += 1
                values[name][r["rules"][name]] += 1
                mod_addon[(app, name)][r["rules"][name]] += 1
                addon_players[name] += r["info"]["players"]
                addon_capacity[name] += r["info"]["max_players"]
                addon_bots[name] += r["info"]["bots"]

    per_ip = Counter(a.rpartition(":")[0] for a in master)
    farms = sum(1 for _, n in per_ip.items() if n > 100)
    empty_mod = {"alive": 0, "players": 0, "bots": 0, "with_rules": 0, "max_players": 0}
    total_players = sum(row["players"] for row in by_mod.values())
    total_capacity = sum(row["max_players"] for row in by_mod.values())

    stamp = datetime.datetime.now(datetime.timezone.utc)
    latest = {
        "generated_at": stamp.isoformat(timespec="seconds"),
        "mods": [{"appid": m["appid"], "name": m["name"], "url": m["url"],
                  "master": per_mod_master.get(m["appid"], 0),
                  **by_mod.get(m["appid"], dict(empty_mod))}
                 for m in mods],
        "totals": {
            "master": len(master),
            "sdr_skipped": sdr,
            "probed": len(results),
            "alive": len(alive),
            "players": total_players,
            "max_players": total_capacity,
            "with_rules": len(with_rules),
            "rules_unknown": len(alive) - len(with_rules),
            "distinct_ips": len(per_ip),
            "ips_over_100_servers": farms,
        },
        "addons": [{"name": v["name"], "title": v["title"], "url": v["url"],
                    "servers": with_addon[v["name"]],
                    "players": addon_players[v["name"]],
                    "max_players": addon_capacity[v["name"]],
                    "bots": addon_bots[v["name"]],
                    "values": dict(values[v["name"]].most_common(50)),
                    "by_mod": {str(m["appid"]): {
                        "servers": sum(mod_addon[(m["appid"], v["name"])].values()),
                        "values": dict(mod_addon[(m["appid"], v["name"])].most_common(20))}
                        for m in mods}}
                   for v in tracked],
        "quality": {
            "truncated_appids": truncated_mods,
            "note": ("Servers that ignore A2S_RULES are counted in rules_unknown, "
                     "not silently dropped."),
        },
    }

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=1)

    row = {"date": stamp.strftime("%Y-%m-%d"),
           "alive": len(alive), "with_rules": len(with_rules),
           "players": total_players, "max_players": total_capacity,
           **{f"addon:{n}": with_addon[n] for n in tracked_names},
           "versions": dict(values[tracked_names[0]].most_common(20)) if tracked_names else {},
           "mods": {str(m["appid"]): {
               "alive": by_mod.get(m["appid"], {}).get("alive", 0),
               "rules": by_mod.get(m["appid"], {}).get("with_rules", 0)} for m in mods},
           "addon_versions": {n: dict(values[n].most_common(10)) for n in tracked_names}}
    hist_path = os.path.join(args.out, "history.json")
    history = []
    if os.path.exists(hist_path):
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    history = [h for h in history if h.get("date") != row["date"]] + [row]
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)

    print(f"alive={len(alive)} with_rules={len(with_rules)} "
          f"yb={with_addon.get('yb_version', 0)}", flush=True)
    return 0


def _is_sdr(host):
    try:
        return ipaddress.ip_address(host) in SDR_NET
    except ValueError:
        return False


def _guess_mod(result, entry, mods):
    appid = entry.get("appid")
    if any(m["appid"] == appid for m in mods):
        return appid
    gamedir = (result.get("info", {}).get("gamedir") or "").lower()
    for m in mods:
        if m.get("gamedir", "").lower() == gamedir:
            return m["appid"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
