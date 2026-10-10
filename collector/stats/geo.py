"""Country resolution with a persistent on-disk cache.

Uses the ip-api.com batch endpoint (100 addrs per call, throttled) and keeps
everything already seen in web/data/geocache.json, so daily runs only look
up new IPs. Unknown/unresolved addrs map to None and land in no bucket.
"""

import json
import os
import time
import urllib.request

BATCH_URL = "http://ip-api.com/batch"
BATCH_SIZE = 100
BATCH_SPACING = 1.5


def load_cache(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(path, cache):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=0)


def _batch_lookup(ips):
    payload = json.dumps([
        {"query": ip, "fields": "status,country,countryCode,query"} for ip in ips
    ]).encode("ascii")
    req = urllib.request.Request(
        BATCH_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def resolve(ips, cache):
    """Fill cache for unknown ips. Returns the cache."""
    todo = [ip for ip in sorted(set(ips)) if ip not in cache]
    for i in range(0, len(todo), BATCH_SIZE):
        if i > 0:
            time.sleep(BATCH_SPACING)
        batch = todo[i:i + BATCH_SIZE]
        try:
            answers = _batch_lookup(batch)
        except Exception as e:
            print(f"geo batch failed ({e}), {len(batch)} ips skipped", flush=True)
            continue
        for entry, ip in zip(answers, batch):
            if isinstance(entry, dict) and entry.get("status") == "success":
                cache[ip] = [entry.get("countryCode", ""), entry.get("country", "")]
        print(f"geo {min(i + BATCH_SIZE, len(todo))}/{len(todo)}", flush=True)
    return cache


def country_of(cache, ip):
    hit = cache.get(ip)
    if not hit:
        return None
    return {"cc": hit[0], "name": hit[1]}
