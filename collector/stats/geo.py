"""Country resolution via an offline mmdb (iplocate, no keys or API calls)."""

import maxminddb


def open_db(path):
    return maxminddb.open_database(path)


def lookup_all(reader, ips):
    """Map every ip to [cc, name], skipping misses."""
    out = {}
    for ip in sorted(set(ips)):
        try:
            rec = reader.get(ip)
        except Exception:
            rec = None
        if isinstance(rec, dict) and rec.get("country_code"):
            out[ip] = [rec.get("country_code", ""), rec.get("country_name", "")]
    return out
