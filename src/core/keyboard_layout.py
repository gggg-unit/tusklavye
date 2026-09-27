"""Turkish Q keyboard layout definition with 10-finger mapping.

Defines the physical key rows, the character each key produces, and which
finger is responsible for pressing it in touch typing.
"""
from __future__ import annotations

from typing import Optional

FINGER_LEFT_PINKY = "LP"
FINGER_LEFT_RING = "LR"
FINGER_LEFT_MIDDLE = "LM"
FINGER_LEFT_INDEX = "LI"
FINGER_RIGHT_INDEX = "RI"
FINGER_RIGHT_MIDDLE = "RM"
FINGER_RIGHT_RING = "RR"
FINGER_RIGHT_PINKY = "RP"
FINGER_LEFT_THUMB = "LT"
FINGER_RIGHT_THUMB = "RT"

HOME_ROW_KEYS = ["a", "s", "d", "f", "j", "k", "l", "ş"]

_TR_UPPER = {"i": "İ", "ı": "I", "ş": "Ş", "ğ": "Ğ", "ü": "Ü", "ö": "Ö", "ç": "Ç"}
_TR_LOWER = {"İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ", "Ü": "ü", "Ö": "ö", "Ç": "ç"}


def _tr_upper(ch: str) -> str:
    return _TR_UPPER.get(ch, ch.upper())


def _tr_lower(ch: str) -> str:
    return _TR_LOWER.get(ch, ch.lower())


class Key:
    """A single physical key: its character, display label, finger, and width."""
    __slots__ = ("char", "display", "finger", "width", "special")

    def __init__(self, char: str, display: str, finger: str, width: float = 1.0, special: bool = False):
        self.char = char
        self.display = display
        self.finger = finger
        self.width = width
        self.special = special


class KeyboardLayout:
    """Turkish Q (Q klavye) layout."""

    def __init__(self):
        self.rows = self._build_rows()
        self.char_to_finger = self._build_char_finger_map()

    def _build_rows(self) -> list:
        LP, LR, LM, LI = FINGER_LEFT_PINKY, FINGER_LEFT_RING, FINGER_LEFT_MIDDLE, FINGER_LEFT_INDEX
        RI, RM, RR, RP = FINGER_RIGHT_INDEX, FINGER_RIGHT_MIDDLE, FINGER_RIGHT_RING, FINGER_RIGHT_PINKY

        row1 = [
            Key('"', '"', LP), Key("1", "1", LP), Key("2", "2", LR), Key("3", "3", LM),
            Key("4", "4", LI), Key("5", "5", LI), Key("6", "6", RI), Key("7", "7", RI),
            Key("8", "8", RM), Key("9", "9", RR), Key("0", "0", RR), Key("*", "*", RP),
            Key("-", "-", RP),
        ]
        row2 = [
            Key("q", "Q", LP), Key("w", "W", LR), Key("e", "E", LM), Key("r", "R", LI),
            Key("t", "T", LI), Key("y", "Y", RI), Key("u", "U", RI), Key("ı", "I", RM),
            Key("o", "O", RR), Key("p", "P", RP), Key("ğ", "Ğ", RP), Key("ü", "Ü", RP),
        ]
        row3 = [
            Key("a", "A", LP), Key("s", "S", LR), Key("d", "D", LM), Key("f", "F", LI),
            Key("g", "G", LI), Key("h", "H", RI), Key("j", "J", RI), Key("k", "K", RM),
            Key("l", "L", RR), Key("ş", "Ş", RR), Key("i", "İ", RP), Key(",", ",", RP),
        ]
        row4 = [
            Key("z", "Z", LP), Key("x", "X", LR), Key("c", "C", LM), Key("v", "V", LI),
            Key("b", "B", LI), Key("n", "N", RI), Key("m", "M", RI), Key("ö", "Ö", RM),
            Key("ç", "Ç", RR), Key(".", ".", RP),
        ]
        return [row1, row2, row3, row4]

    def _build_char_finger_map(self) -> dict:
        mapping = {}
        for row in self.rows:
            for key in row:
                mapping[key.char] = key.finger
                mapping[_tr_upper(key.char)] = key.finger
        mapping[" "] = FINGER_RIGHT_THUMB
        mapping["\n"] = FINGER_RIGHT_PINKY
        return mapping

    def finger_for_char(self, char: str) -> str:
        return self.char_to_finger.get(char, FINGER_RIGHT_PINKY)

    def find_key(self, char: str) -> Optional[Key]:
        for row in self.rows:
            for key in row:
                if key.char == char:
                    return key
        lower = _tr_lower(char)
        if lower != char:
            for row in self.rows:
                for key in row:
                    if key.char == lower:
                        return key
        return None