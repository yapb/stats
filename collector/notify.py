"""Open one issue per freshly seen addon version (deduped via notified.json).

Reads web/data/latest.json (fresh field) and web/data/notified.json, opens
GitHub issues for anything not announced yet, updates notified.json.
Talks to the GitHub REST API directly, no gh binary needed.
Needs GH_TOKEN and GITHUB_REPOSITORY set, and issues:write permission.
Without a token it quietly does nothing (exit 0, CI stays green).
"""

import json
import os
import sys
import urllib.request

DATA = os.path.join(os.path.dirname(__file__), "..", "web", "data")


def load(name, default):
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def create_issue(repo, token, title, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues",
        data=json.dumps({"title": title, "body": body}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "yapb-stats-notify"},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("html_url", "")


def main():
    latest = load("latest.json", {})
    fresh = latest.get("fresh", {})
    if not fresh:
        print("nothing fresh")
        return 0
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("no GH_TOKEN, skipping notifications")
        return 0
    repo = os.environ.get("GITHUB_REPOSITORY", "yapb/stats")
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
            try:
                url = create_issue(repo, token, title, body)
            except Exception as e:
                print(f"issue failed for {name}={value}: {e}")
                continue
            print(f"opened: {url}")
            notified.setdefault(name, []).append(value)
            opened += 1
    with open(os.path.join(DATA, "notified.json"), "w", encoding="utf-8") as f:
        json.dump(notified, f, ensure_ascii=False, indent=1)
    print(f"notified {opened} new versions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
