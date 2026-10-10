"""Master phase: Steam list plus community masters merged into one addr set."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from stats.legacy_master import query as legacy_query
from stats.static_lists import fetch_list
from stats.steam_master import fetch_mod

CORE_GAMEDIRS = ("cstrike", "czero", "valve", "dod", "tfc", "gearbox", "dmc", "ricochet")
EXTRA_WORKERS = 10


def _legacy_job(entry, mod):
    name = entry.get("name") or entry["host"]
    gamedir = mod.get("gamedir", "")
    try:
        addrs = legacy_query(entry["host"], entry.get("port", 27010), gamedir)
        return (name, mod, addrs, None)
    except Exception as e:
        return (name, mod, [], e)


def _static_job(entry, mod, url):
    name = entry.get("name") or entry["url"]
    gamedir = mod.get("gamedir", "")
    try:
        addrs = fetch_list(dict(entry, url=url))
        return (name, mod, addrs, None)
    except Exception as e:
        return (name, mod, [], e)


def collect_all(key, mods, custom_masters, static_lists=None, master_cache=None, save_master=None):
    """Returns (master, per_mod_master, truncated_mods, source_new).

    master maps addr to its entry. source_new counts addrs per source
    (Steam first, so later counts are new beyond earlier sources).
    """
    master = {}  # addr mapped to master entry
    per_mod_master = {}
    truncated_mods = []
    if master_cache:
        with open(os.path.expanduser(master_cache), encoding="utf-8") as f:
            cache = json.load(f)
        for mod in mods:
            servers = cache["by_appid"].get(str(mod["appid"]), [])
            per_mod_master[mod["appid"]] = len(servers)
            for s in servers:
                master[s["addr"]] = s
        truncated_mods = cache.get("truncated", [])
        print(f"master loaded from cache: {len(master)} addrs", flush=True)
    else:
        last_call = [0.0]
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
        if save_master:
            with open(os.path.expanduser(save_master), "w", encoding="utf-8") as f:
                json.dump({"by_appid": {str(m["appid"]): [
                    s for s in master.values()
                    if s.get("appid") == m["appid"]] for m in mods},
                    "truncated": truncated_mods}, f)

    steam_total = sum(per_mod_master.values())
    source_new = {"steam": steam_total}
    jobs = []
    for entry in custom_masters:
        wanted = set(entry.get("gamedirs") or CORE_GAMEDIRS)
        query_mods = [m for m in mods if m.get("gamedir", "") in wanted]
        if entry.get("unfiltered") and query_mods:
            picked = [m for m in query_mods if m.get("gamedir") == "cstrike"]
            query_mods = picked or query_mods[:1]
        for mod in query_mods:
            jobs.append(("legacy", entry, mod))
    for entry in static_lists or []:
        wanted = set(entry.get("gamedirs", []))
        for mod in mods:
            gamedir = mod.get("gamedir", "")
            if not gamedir or (wanted and gamedir not in wanted):
                continue
            jobs.append(("static", entry, mod))
    started = time.monotonic()
    done = 0
    with ThreadPoolExecutor(max_workers=EXTRA_WORKERS) as ex:
        futs = {}
        for kind, entry, mod in jobs:
            if kind == "legacy":
                fut = ex.submit(_legacy_job, entry, mod)
            else:
                url = entry["url"].replace("{gamedir}", mod.get("gamedir", ""))
                fut = ex.submit(_static_job, entry, mod, url)
            futs[fut] = (kind, entry, mod)
        for fut in as_completed(futs):
            kind, entry, mod = futs[fut]
            name, _, addrs, err = fut.result()
            gamedir = mod.get("gamedir", "")
            if err is not None:
                print(f"{kind} source {name} gamedir={gamedir} failed ({err})", flush=True)
                continue
            new_here = 0
            for addr in addrs:
                if addr not in master:
                    master[addr] = {"addr": addr, "gamedir": gamedir, "appid": 0,
                                    "source": name}
                    per_mod_master[mod["appid"]] = per_mod_master.get(mod["appid"], 0) + 1
                    new_here += 1
            source_new[name] = source_new.get(name, 0) + new_here
            done += 1
            print(f"extra source {name} {gamedir}: {new_here} new "
                  f"({done}/{len(futs)} in {time.monotonic() - started:.0f}s)", flush=True)
    return master, per_mod_master, truncated_mods, source_new
