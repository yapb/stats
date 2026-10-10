"""A2S phase: INFO plus RULES for every target, concurrent with progress."""

import ipaddress
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import a2s

from stats.a2s_rules import fetch_rules

SDR_NET = ipaddress.ip_network("169.254.0.0/16")


def _is_sdr(host):
    try:
        return ipaddress.ip_address(host) in SDR_NET
    except ValueError:
        return False


def select_targets(master, max_addrs=0, skip_a2s=False):
    """Split addrs into (targets, sdr_skipped)."""
    sdr = sum(1 for a in master
              if a.rpartition(":")[0] and _is_sdr(a.rpartition(":")[0]))
    targets = [a for a in master if not _is_sdr(a.rpartition(":")[0])]
    if max_addrs:
        targets = targets[:max_addrs]
    if skip_a2s:
        targets = []
    return targets, sdr


def probe(addr, timeout):
    """A2S INFO plus RULES for one addr. Returns a small dict, never raises."""
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


def run_a2s(targets, timeout, workers):
    """Probe everything, printing progress about 40 times per run."""
    results = []
    done = 0
    started = time.monotonic()
    step = max(1, len(targets) // 40)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(probe, a, timeout) for a in targets]
        for f in as_completed(futs):
            results.append(f.result())
            done += 1
            if done % step == 0 or done == len(targets):
                elapsed = time.monotonic() - started
                rate = done / elapsed if elapsed > 0 else 0
                eta = (len(targets) - done) / rate if rate > 0 else 0
                print(f"A2S {done}/{len(targets)} ({100 * done / len(targets):.0f}%)"
                      f" {rate:.0f}/s eta {eta / 60:.0f}m", flush=True)
    return results
