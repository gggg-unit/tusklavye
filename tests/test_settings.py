"""Tests for SettingsRepository typed accessors."""
from src.database.models import SettingsRepository


def test_set_and_get(settings_repo):
    settings_repo.set("theme", "dark")
    assert settings_repo.get("theme") == "dark"


def test_get_bool(settings_repo):
    settings_repo.set("sound_enabled", "True")
    assert settings_repo.get_bool("sound_enabled") is True
    settings_repo.set("sound_enabled", "False")
    assert settings_repo.get_bool("sound_enabled") is False
    assert settings_repo.get_bool("nonexistent", True) is True


def test_get_int(settings_repo):
    settings_repo.set("font_size", "26")
    assert settings_repo.get_int("font_size") == 26
    assert settings_repo.get_int("nonexistent", 20) == 20
    settings_repo.set("bad", "not_a_number")
    assert settings_repo.get_int("bad", 0) == 0


def test_get_float(settings_repo):
    settings_repo.set("volume", "0.5")
    assert settings_repo.get_float("volume") == 0.5
    assert settings_repo.get_float("nonexistent", 0.5) == 0.5


def test_get_all(settings_repo):
    settings_repo.set("a", "1")
    settings_repo.set("b", "2")
    all_settings = settings_repo.get_all()
    assert all_settings["a"] == "1"
    assert all_settings["b"] == "2"


def test_overwrite(settings_repo):
    settings_repo.set("key", "first")
    settings_repo.set("key", "second")
    assert settings_repo.get("key") == "second"