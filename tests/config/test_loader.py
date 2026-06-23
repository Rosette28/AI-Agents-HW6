"""Tests for the config loader against the real config/config.yaml."""

from src.config.loader import load_config


def test_load_config_returns_expected_keys():
    config = load_config()
    assert config["board"]["grid_size"] == [5, 5]
    assert config["game"]["max_moves"] == 25
    assert config["game"]["num_games"] == 6
    assert config["game"]["max_barriers"] == 5
    assert config["scoring"]["cop_win"] == 20
