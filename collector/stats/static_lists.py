"""Static HTTP server lists merged into the addr set.

Two shapes: plain "gs ip:port" line files and TOML files with [[server]]
address fields. Anything unparsable is skipped; A2S probing later drops
whatever is dead, so stale entries here cost nothing but a probe.
"""

import tomllib
import urllib.error
import urllib.request


def fetch_lines(url, prefix):
    with urllib.request.urlopen(url, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    addrs = []
    for line in text.splitlines():
        line = line.strip()
        if prefix and line.startswith(prefix):
            line = line[len(prefix):].strip()
        if _looks_like_addr(line):
            addrs.append(line)
    return addrs


def fetch_toml(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        data = tomllib.load(r)
    addrs = []
    servers = data.get("server", [])
    if isinstance(servers, dict):
        servers = [servers]
    for entry in servers:
        addr = (entry.get("address") or "").strip()
        if _looks_like_addr(addr):
            addrs.append(addr)
    return addrs


def _looks_like_addr(addr):
    host, sep, port = addr.rpartition(":")
    if not sep or not host:
        return False
    try:
        return 0 < int(port) < 65536
    except ValueError:
        return False


def fetch_list(entry):
    if entry.get("kind") == "toml":
        return fetch_toml(entry["url"])
    return fetch_lines(entry["url"], entry.get("prefix", ""))
