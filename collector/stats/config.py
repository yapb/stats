"""Load YAML configs (mods, tracked vars, community masters)."""

import os

import yaml


def _load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_mods(config_dir):
    return _load(os.path.join(config_dir, "mods.yml"))["mods"]


def load_tracked_vars(config_dir):
    return _load(os.path.join(config_dir, "tracked_vars.yml"))["vars"]


def load_custom_masters(config_dir):
    return _load(os.path.join(config_dir, "custom_masters.yml")).get("masters", [])
