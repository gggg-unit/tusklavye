"""Tests for the Turkish Q keyboard layout."""
from src.core.keyboard_layout import KeyboardLayout, _tr_upper, _tr_lower


def test_finger_mapping(layout):
    assert layout.finger_for_char("a") == "LP"
    assert layout.finger_for_char("j") == "RI"
    assert layout.finger_for_char("ş") == "RR"
    assert layout.finger_for_char(" ") == "RT"
    assert len(layout.rows) == 4


def test_find_key_returns_optional(layout):
    assert layout.find_key("a") is not None
    assert layout.find_key("a").char == "a"
    assert layout.find_key("zzz") is None


def test_turkish_uppercase():
    assert _tr_upper("i") == "İ"
    assert _tr_upper("ı") == "I"
    assert _tr_upper("ş") == "Ş"
    assert _tr_upper("ğ") == "Ğ"
    assert _tr_upper("ü") == "Ü"
    assert _tr_upper("ö") == "Ö"
    assert _tr_upper("ç") == "Ç"


def test_turkish_lowercase():
    assert _tr_lower("İ") == "i"
    assert _tr_lower("I") == "ı"
    assert _tr_lower("Ş") == "ş"
    assert _tr_lower("Ğ") == "ğ"


def test_upper_lower_finger_consistency(layout):
    assert layout.finger_for_char("İ") == layout.finger_for_char("i")
    assert layout.finger_for_char("I") == layout.finger_for_char("ı")
    assert layout.finger_for_char("A") == layout.finger_for_char("a")
    k = layout.find_key("Ş")
    assert k is not None and k.char == "ş"