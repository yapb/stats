"""Fail-fast self test: synthetic census through aggregate plus imports.

Catches KeyError-class bugs before a full run burns an hour.
Run: python collector/tests/test_smoke.py (exit nonzero on failure).
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from stats import aggregate, config, farm, masters, probe  # noqa: F401, E402
from stats import a2s_rules, geo, legacy_master, static_lists, steam_master  # noqa: F401, E402


def synthetic():
    results = [
        {"addr": "1.1.1.1:27015",
         "info": {"name": "cs pub", "map": "de_dust2", "players": 5,
                  "max_players": 32, "bots": 0, "os": "l",
                  "gamedir": "cstrike", "vac": True},
         "rules": {"yb_version": "4.8.1", "bot_quota": "0"}},
        {"addr": "2.2.2.2:27015",
         "info": {"name": "hl pub", "map": "crossfire", "players": 3,
                  "max_players": 20, "bots": 1, "os": "w",
                  "gamedir": "valve", "vac": False},
         "rules": {"amxmodx_version": "1.9.0", "pushablemode": "1"}},
        {"addr": "3.3.3.3:27015",
         "info": {"name": "fake", "map": "de_dust2", "players": 255,
                  "max_players": 255, "bots": 0, "os": "l",
                  "gamedir": "cstrike", "vac": False}},
        {"addr": "4.4.4.4:27015", "info_err": "TimeoutError"},
    ]
    master = {
        "1.1.1.1:27015": {"addr": "1.1.1.1:27015", "appid": 10, "gamedir": "cstrike"},
        "2.2.2.2:27015": {"addr": "2.2.2.2:27015", "appid": 70, "gamedir": "valve"},
        "3.3.3.3:27015": {"addr": "3.3.3.3:27015", "appid": 10, "gamedir": "cstrike"},
        "4.4.4.4:27015": {"addr": "4.4.4.4:27015", "appid": 10, "gamedir": "cstrike"},
    }
    mods = [
        {"appid": 10, "gamedir": "cstrike", "name": "CS",
         "url": "https://example.com/cs"},
        {"appid": 70, "gamedir": "valve", "name": "HL"},
    ]
    tracked = [
        {"name": "yb_version", "title": "YaPB", "url": "https://example.com/yb"},
        {"name": "bot_quota", "title": "CZ Bot", "novalue": True},
        {"name": "amxmodx_version", "title": "AMX Mod X"},
        {"name": "xash", "title": "Xash3D", "novalue": True,
         "any_of": ["pushablemode", "mp_bhopcap"]},
    ]
    return results, master, mods, tracked


class SmokeTest(unittest.TestCase):
    def test_build_schema(self):
        results, master, mods, tracked = synthetic()
        kept, farm_info = farm.filter_farms(dict(master), 100)
        self.assertEqual(len(kept), 4)
        latest, row = aggregate.build(
            results, kept, mods, tracked, [], {"steam": 4},
            farm_info, 0, None)
        self.assertEqual(latest["totals"]["alive"], 2)
        self.assertEqual(latest["totals"]["fake_a2s_dropped"], 1)
        self.assertEqual(len(latest["mods"]), 2)
        self.assertIn("maps", latest["mods"][0])
        self.assertIn("countries", latest["mods"][0])
        self.assertEqual(len(latest["addons"]), 4)
        by_name = {a["name"]: a for a in latest["addons"]}
        self.assertTrue(by_name["yb_version"]["values"])
        self.assertTrue(by_name["bot_quota"]["novalue"])
        self.assertEqual(by_name["xash"]["servers"], 1)
        self.assertFalse(by_name["xash"]["values"])
        self.assertNotIn("url", by_name["amxmodx_version"])
        self.assertEqual(by_name["amxmodx_version"]["servers"], 1)
        self.assertIn("unlisted_mods", latest)
        self.assertIn("unlisted_vars", latest)
        self.assertEqual(row["alive"], 2)
        self.assertIn("addon:yb_version", row)
        with tempfile.TemporaryDirectory() as out:
            with open(os.path.join(out, "history.json"), "w", encoding="utf-8") as f:
                json.dump([{"ts": "2026-10-09 00:00", "date": "2026-10-09",
                            "addon_versions": {"yb_version": ["4.8.0"]}}], f)
            fresh = aggregate.write_output(out, latest, row, tracked)
            self.assertIn("fresh", latest)
            self.assertIn("yb_version", fresh)
            self.assertNotIn("bot_quota", fresh)
            self.assertTrue(os.path.exists(os.path.join(out, "latest.json")))
            self.assertTrue(os.path.exists(os.path.join(out, "history.json")))
            self.assertIsInstance(fresh, dict)

    def test_farm_filter(self):
        master = {f"9.9.9.9:{p}": {"addr": f"9.9.9.9:{p}", "players": 0}
                  for p in range(27015, 27117)}
        master["1.2.3.4:27015"] = {"addr": "1.2.3.4:27015", "players": 500}
        kept, info = farm.filter_farms(master, 100)
        self.assertEqual(len(kept), 0)
        self.assertEqual(info["farm_dropped"], 102)
        self.assertEqual(info["fake_dropped"], 1)
        kept, _ = farm.filter_farms(dict(master), 0)
        self.assertEqual(len(kept), 103)


if __name__ == "__main__":
    unittest.main(verbosity=1)
