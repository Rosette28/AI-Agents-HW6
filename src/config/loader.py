"""Loads config/config.yaml into a plain dict. Single entry point for all
config access — no module outside this package should parse YAML itself.
"""

from pathlib import Path

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.yaml"


def load_config(path: Path | str | None = None) -> dict:
    """Load and return the config file as a dict.

    Args: path -- override path to a config YAML file; defaults to the
    repo's config/config.yaml.
    Returns: parsed config dict.
    """
    config_path = Path(path) if path is not None else _DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
