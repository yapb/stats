"""Aggregation: probe results folded into latest.json plus a history row."""

import datetime
import json
import os
from collections import Counter, defaultdict

from stats import geo as geo_mod


def _guess_mod(result, entry, mods):
    gamedir = (result.get("info", {}).get("gamedir") or entry.get("gamedir") or "").lower()
    if gamedir:
        return gamedir
    if entry.get("appid"):
        return f"appid:{entry['appid']}"
    return "unknown"


def _is_fake_count(info):
    """Impossible headcounts no real HL1 server reports. Tolerances stay
    wide on purpose: a couple of extra bodies can be HLTV or quirks, while
    hundreds cannot."""
    players = info["players"]
    capacity = info["max_players"]
    return players - capacity > 2 or capacity > 64 or players > 130


def build(results, master, mods, tracked, truncated_mods,
          source_new, farm_info, sdr, geo_reader=None):
    """Fold results into (latest, history_row) dicts."""
    tracked_names = [v["name"] for v in tracked]
    answered = [r for r in results if "info" in r]
    fakes = [r for r in answered if _is_fake_count(r["info"])]
    alive = [r for r in answered if not _is_fake_count(r["info"])]
    with_rules = [r for r in alive if "rules" in r]

    empty_mod = {"alive": 0, "players": 0, "bots": 0, "with_rules": 0, "max_players": 0}
    by_mod = defaultdict(lambda: dict(empty_mod))
    mod_maps = defaultdict(Counter)  # gamedir mapped to map counts
    tracked_dirs = {(m.get("gamedir") or "").lower() for m in mods}
    unlisted = Counter()
    for r in alive:
        app = _guess_mod(r, master.get(r["addr"], {}), mods)
        row = by_mod[app]
        row["alive"] += 1
        row["players"] += r["info"]["players"]
        row["bots"] += r["info"]["bots"]
        row["max_players"] += r["info"]["max_players"]
        if r["info"]["map"]:
            mod_maps[app][r["info"]["map"]] += 1
        if app not in tracked_dirs:
            unlisted[app] += 1

    values = {name: Counter() for name in tracked_names}
    with_addon = {name: 0 for name in tracked_names}
    addon_players = Counter()
    addon_capacity = Counter()
    addon_bots = Counter()
    mod_addon = defaultdict(Counter)  # (gamedir, var) mapped to value counts
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

    info_errs = Counter(r["info_err"] for r in results if "info_err" in r)
    rules_errs = Counter(r["rules_err"] for r in alive if "rules_err" in r)
    BOT_VARS = {"yb_version", "pb_version", "bot_quota"}
    mystery_servers = 0
    mystery_bots = 0
    for r in with_rules:
        if r["info"]["bots"] > 0 and not any(v in r["rules"] for v in BOT_VARS):
            mystery_servers += 1
            mystery_bots += r["info"]["bots"]
    countries = []
    if geo_reader is not None:
        per_ip_count = Counter(r["addr"].rpartition(":")[0] for r in alive)
        found = geo_mod.lookup_all(geo_reader, per_ip_count.keys())
        by_cc = Counter()
        names = {}
        for ip, n in per_ip_count.items():
            if ip in found:
                cc, name = found[ip]
                by_cc[cc] += n
                names[cc] = name
        countries = [{"cc": cc, "name": names[cc], "servers": n}
                     for cc, n in by_cc.most_common()]
    total_players = sum(row["players"] for row in by_mod.values())
    total_capacity = sum(row["max_players"] for row in by_mod.values())

    stamp = datetime.datetime.now(datetime.timezone.utc)
    mod_master = farm_info.get("mod_master", {})
    latest = {
        "generated_at": stamp.isoformat(timespec="seconds"),
        "mods": [{"appid": m["appid"], "gamedir": m.get("gamedir", ""), "name": m["name"],
                  **({"url": m["url"]} if m.get("url") else {}),
                  "master": mod_master.get((m.get("gamedir") or "").lower(), 0),
                  **by_mod.get((m.get("gamedir") or "").lower(), dict(empty_mod)),
                  "maps": dict(mod_maps[(m.get("gamedir") or "").lower()].most_common(15))}
                 for m in mods],
        "totals": {
            "master": farm_info["master_raw"],
            "sources": source_new,
            "sdr_skipped": sdr,
            "farm_dropped": farm_info["farm_dropped"],
            "fake_dropped": farm_info["fake_dropped"],
            "probed": len(results),
            "alive": len(alive),
            "fake_a2s_dropped": len(fakes),
            "players": total_players,
            "max_players": total_capacity,
            "with_rules": len(with_rules),
            "rules_unknown": len(alive) - len(with_rules),
            "distinct_ips": len(farm_info["per_ip"]),
            "ips_over_100_servers": len(farm_info["spam_hosts"]),
            "mystery_servers": mystery_servers,
            "mystery_bots": mystery_bots,
        },
        "countries": countries,
        "unlisted_mods": [{"gamedir": g, "servers": n} for g, n in unlisted.most_common(20)],
        "addons": [{"name": v["name"], "title": v["title"], "url": v["url"],
                    "servers": with_addon[v["name"]],
                    "players": addon_players[v["name"]],
                    "max_players": addon_capacity[v["name"]],
                    "bots": addon_bots[v["name"]],
                    "values": dict(values[v["name"]].most_common(50)),
                    "by_mod": {m.get("gamedir", ""): {
                        "servers": sum(mod_addon[(m.get("gamedir", ""), v["name"])].values()),
                        "values": dict(mod_addon[(m.get("gamedir", ""), v["name"])].most_common(20))}
                        for m in mods}}
                   for v in tracked],
        "quality": {
            "truncated_appids": truncated_mods,
            "info_errors": dict(info_errs.most_common(10)),
            "rules_errors": dict(rules_errs.most_common(10)),
            "note": ("Servers that ignore A2S_RULES are counted in rules_unknown, "
                     "not silently dropped."),
        },
    }
    row = {"ts": stamp.strftime("%Y-%m-%d %H:%M"),
           "date": stamp.strftime("%Y-%m-%d"),
           "alive": len(alive), "with_rules": len(with_rules),
           "players": total_players, "max_players": total_capacity,
           **{f"addon:{n}": with_addon[n] for n in tracked_names},
           "versions": dict(values[tracked_names[0]].most_common(20)) if tracked_names else {},
           "mods": {m.get("gamedir", ""): {
               "alive": by_mod.get(m.get("gamedir", ""), {}).get("alive", 0),
               "rules": by_mod.get(m.get("gamedir", ""), {}).get("with_rules", 0)} for m in mods},
           "addon_versions": {n: dict(values[n].most_common(10)) for n in tracked_names}}
    return latest, row


def write_output(out_dir, latest, row):
    """Write latest.json, appending the row to history.json by timestamp.

    Returns {addon: [values]} first seen in this run (dashboard NEW badges
    and release notifications). Needs at least one prior row carrying
    addon_versions, otherwise everything looks new.
    """
    os.makedirs(out_dir, exist_ok=True)
    hist_path = os.path.join(out_dir, "history.json")
    history = []
    if os.path.exists(hist_path):
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    known = set()
    baseline = 0
    for h in history:
        av = h.get("addon_versions")
        if av:
            baseline += 1
            for name, vals in av.items():
                for v in vals:
                    known.add((name, v))
    fresh = {}
    if baseline >= 1:
        for name, vals in row.get("addon_versions", {}).items():
            new = [v for v in vals if (name, v) not in known]
            if new:
                fresh[name] = new
    latest["fresh"] = fresh
    with open(os.path.join(out_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=1)
    history = [h for h in history if h.get("ts") != row["ts"]] + [row]
    history = history[-120:]
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1)
    return fresh
