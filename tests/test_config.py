"""Test centralized configuration."""

import os

import pytest


def test_config_loads_founder_id():
    """Founder ID must be set and positive."""
    from src.config import settings
    assert settings.founder_telegram_id > 0


def test_config_app_defaults():
    """Default app settings."""
    from src.config import settings
    assert settings.app_name == "IDOL"
    assert settings.enable_ai is False
