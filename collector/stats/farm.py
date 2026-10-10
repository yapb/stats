"""Redirect farm filter, applied before spending A2S probes.

Farms stuff the master list with thousands of fake ports on a few IPs.
Drop whole hosts over the per-IP cap, plus lone servers with impossible
master-reported player counts. A lone faker never condemns its host: only
the port count marks spam.
"""

from collections import Counter

MAX_REALISTIC_PLAYERS = 130


def filter_farms(master, max_per_host):
    """Returns (kept, info) with info holding counts for the report."""
    per_ip = Counter(a.rpartition(":")[0] for a in master)
    mod_master = Counter((e.get("gamedir") or "").lower() for e in master.values())
    master_raw = len(master)
    spam_hosts = {ip for ip, n in per_ip.items() if max_per_host > 0 and n > max_per_host}
    farm_dropped = 0
    fake_dropped = 0
    kept = master
    if max_per_host > 0:
        kept = {}
        for addr, entry in master.items():
            host = addr.rpartition(":")[0]
            if host in spam_hosts:
                farm_dropped += 1
                continue
            if (entry.get("players", 0) or 0) > MAX_REALISTIC_PLAYERS:
                fake_dropped += 1
                continue
            kept[addr] = entry
        print(f"farm filter: {len(spam_hosts)} hosts, {farm_dropped} farm addrs, "
              f"{fake_dropped} fake-count addrs dropped", flush=True)
    info = {
        "per_ip": per_ip,
        "mod_master": mod_master,
        "spam_hosts": spam_hosts,
        "master_raw": master_raw,
        "farm_dropped": farm_dropped,
        "fake_dropped": fake_dropped,
    }
    return kept, info
