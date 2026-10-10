"""Open one issue per freshly seen addon version (deduped via notified.json).

Reads web/data/latest.json (fresh field) and web/data/notified.json, opens
GitHub issues for anything not announced yet, updates notified.json.
Needs gh on PATH with GH_TOKEN set, and issues:write permission.
"""

import json
import os
import subprocess
import sys

DATA = os.path.join(os.path.dirname(__file__), "..", "web", "data")


def load(name, default):
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main():
    latest = load("latest.json", {})
    fresh = latest.get("fresh", {})
    if not fresh:
        print("nothing fresh")
        return 0
    titles = {a["name"]: a["title"] for a in latest.get("addons", [])}
    notified = load("notified.json", {})
    opened = 0
    for name, values in fresh.items():
        known = set(notified.get(name, []))
        for value in values:
            if value in known:
                continue
            title = f"New {titles.get(name, name)} version seen: {value}"
            body = (
                f"First seen in the census run {latest.get('generated_at', '?')}.\n\n"
                f"Rule `{name}` with value `{value}` never appeared before.\n\n"
                f"Dashboard: https://yapb.github.io/stats/#/addon/{name}"
            )
            r = subprocess.run(
                ["gh", "issue", "create", "--title", title, "--body", body],
                capture_output=True, text=True)
            if r.returncode != 0:
                print(f"issue failed for {name}={value}: {r.stderr.strip()}")
                continue
            print(f"opened: {r.stdout.strip()}")
            notified.setdefault(name, []).append(value)
            opened += 1
    with open(os.path.join(DATA, "notified.json"), "w", encoding="utf-8") as f:
        json.dump(notified, f, ensure_ascii=False, indent=1)
    print(f"notified {opened} new versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
