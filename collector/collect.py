"""Addons stats collector: master lists plus A2S INFO/RULES scan.

Reads config/mods.yml, config/tracked_vars.yml and config/custom_masters.yml,
writes web/data/latest.json and appends a daily row to web/data/history.json.

    STEAM_WEBAPI_KEY=<key> python collect.py --out ../web/data
"""

import argparse
import os
import sys

from stats import aggregate, config, farm, masters, probe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output dir for latest.json/history.json")
    ap.add_argument("--config-dir", default=os.path.join(os.path.dirname(__file__), "..", "config"))
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--timeout", type=float, default=3.0)
    ap.add_argument("--appid", type=int, action="append", default=None,
                    help="only scan these appids (repeatable; default: all from mods.yml)")
    ap.add_argument("--max-addrs", type=int, default=0,
                    help="cap A2S probes for smoke tests (0 = no cap)")
    ap.add_argument("--save-master", default=None,
                    help="save raw master lists to this JSON file for reuse")
    ap.add_argument("--master-cache", default=None,
                    help="skip the master phase, load lists from a --save-master file")
    ap.add_argument("--skip-a2s", action="store_true",
                    help="only fetch the master lists (used with --save-master)")
    ap.add_argument("--max-servers-per-host", type=int, default=100,
                    help="hosts with more master entries are redirect farms, drop them (0 disables)")
    args = ap.parse_args()

    key = os.environ.get("STEAM_WEBAPI_KEY", "")
    if not key and not args.master_cache:
        print("STEAM_WEBAPI_KEY is not set", file=sys.stderr)
        return 2

    mods = config.load_mods(args.config_dir)
    tracked = config.load_tracked_vars(args.config_dir)
    customs = config.load_custom_masters(args.config_dir)
    if args.appid:
        mods = [m for m in mods if m["appid"] in args.appid]

    master, per_mod_master, truncated_mods, source_new = masters.collect_all(
        key, mods, customs, args.master_cache, args.save_master)
    master, farm_info = farm.filter_farms(master, args.max_servers_per_host)
    targets, sdr = probe.select_targets(master, args.max_addrs, args.skip_a2s)
    print(f"A2S targets: {len(targets)} (+{sdr} SDR skipped,"
          f" {args.workers} workers)", flush=True)
    results = probe.run_a2s(targets, args.timeout, args.workers)
    latest, row = aggregate.build(
        results, master, mods, tracked, per_mod_master, truncated_mods,
        source_new, farm_info, sdr)
    aggregate.write_output(args.out, latest, row)

    yb = next((a["servers"] for a in latest["addons"] if a["name"] == "yb_version"), 0)
    print(f"alive={latest['totals']['alive']} with_rules={latest['totals']['with_rules']} "
          f"yb={yb}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
