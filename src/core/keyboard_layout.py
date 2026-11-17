"""Turkish Q keyboard layout definition with 10-finger mapping.

Defines the physical key rows, the character each key produces, and which
finger is responsible for pressing it in touch typing.
"""
from __future__ import annotations

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

HOME_FINGER_KEYS = dict(zip(("LP", "LR", "LM", "LI", "RI", "RM", "RR", "RP"), "asdfjklş", strict=True))

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
        self.shift = dict(zip('1234567890*-,.<', "!'^+%&/()=?_;:>", strict=True))
        self.shift['"'] = "é"
        self.shift["3"] = "^"
        self.altgr = {"q": "@", "e": "€", "2": "£", "3": "#", "4": "$",
                      "5": "½", "7": "{", "8": "[", "9": "]", "0": "}",
                      "*": "\\", "-": "|", "a": "æ", "s": "ß"}
        self.char_to_finger = self._build_char_finger_map()

    def _build_rows(self) -> list:
        LP, LR, LM, LI = FINGER_LEFT_PINKY, FINGER_LEFT_RING, FINGER_LEFT_MIDDLE, FINGER_LEFT_INDEX
        RI, RM, RR, RP = FINGER_RIGHT_INDEX, FINGER_RIGHT_MIDDLE, FINGER_RIGHT_RING, FINGER_RIGHT_PINKY

        row1 = [
            Key('"', '"', LP), Key("1", "1", LP), Key("2", "2", LR), Key("3", "3", LM),
            Key("4", "4", LI), Key("5", "5", LI), Key("6", "6", RI), Key("7", "7", RI),
            Key("8", "8", RM), Key("9", "9", RR), Key("0", "0", RP), Key("*", "*", RP),
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
            Key("l", "L", RR), Key("ş", "Ş", RP), Key("i", "İ", RP), Key(",", ",", RP),
        ]
        row4 = [
            Key("<", "<", LP),
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
        for source, output in {**self.shift}.items():
            mapping[output] = mapping[source]
        for source, output in self.altgr.items():
            mapping[output] = mapping[source]
        return mapping

    def finger_for_char(self, char: str) -> str:
        return self.char_to_finger.get(char, "")

    def find_key(self, char: str) -> Key | None:
        base, _ = self.stroke_for_char(char)
        return next((key for row in self.rows for key in row if key.char == base), None)

    def stroke_for_char(self, char: str) -> tuple[str, str]:
        if char == " ":
            return " ", ""
        for row in self.rows:
            for key in row:
                if key.char == char:
                    return char, ""
                if key.char.isalpha() and _tr_upper(key.char) == char:
                    return key.char, "Shift"
        for modifier, mapping in (("Shift", self.shift), ("AltGr", self.altgr)):
            for base, output in mapping.items():
                if output == char:
                    return base, modifier
        return "", ""

    def output_for_key(self, base: str, modifier: str = "") -> str:
        if modifier == "Shift":
            return self.shift.get(base, _tr_upper(base))
        if modifier == "AltGr":
            return self.altgr.get(base, "")
        return base

    def row_for_char(self, char: str) -> int | None:
        key = self.find_key(char)
        return next((index for index, row in enumerate(self.rows) if key in row), None)
