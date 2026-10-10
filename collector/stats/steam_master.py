"""Steam Web API master list with per-map fan-out past the 10k cap."""

import json
import time
import urllib.parse
import urllib.request

API_BASE = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
MASTER_LIMIT = 10000  # Steam's per-query cap
MASTER_SPACING = 1.6  # seconds between calls (200 req / 5 min per key)


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
        # Split the capped answer into per-map queries so dense mods are
        # still (mostly) enumerated. Completeness still isn't provable
        # (maps beyond the cap stay unseen), hence the truncated flag stays
        # set (see quality.truncated_appids).
        maps = sorted({s.get("map", "") for s in servers if s.get("map")})
        maps = [m for m in maps if m.strip()]
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
