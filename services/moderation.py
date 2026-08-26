"""Parse group Admin mute/ban text. No Telegram types."""

from __future__ import annotations

import re
from typing import Optional

MUTE_MAX_SECONDS = 14 * 24 * 60 * 60

_CMD = re.compile(
    r"^/?(?P<cmd>"
    r"unmute|unmut|mute|mut|"
    r"unban|ban|"
    r"размут|анмут|мьют|мут|"
    r"разбан|бан"
    r")(?:@\w+)?"
    r"(?:\s+(?P<n>\d+)\s*(?P<u>[mhdмчд]))?"
    r"(?:\s+@(?P<who>[A-Za-z0-9_]{4,32}))?"
    r"\s*$",
    re.IGNORECASE | re.UNICODE,
)

_MUTE = frozenset({"mute", "mut", "мут", "мьют"})
_UNMUTE = frozenset({"unmute", "unmut", "размут", "анмут"})
_BAN = frozenset({"ban", "бан"})
_UNBAN = frozenset({"unban", "разбан"})

_UNITS = {
    "m": 60,
    "h": 3600,
    "d": 86400,
    "м": 60,
    "ч": 3600,
    "д": 86400,
}


def parse_moderation(text: str) -> Optional[dict]:
    raw = (text or "").strip()
    if not raw:
        return None
    m = _CMD.match(raw)
    if not m:
        return None
    cmd = m.group("cmd").lower()
    action = None
    if cmd in _UNMUTE:
        action = "unmute"
    elif cmd in _MUTE:
        action = "mute"
    elif cmd in _UNBAN:
        action = "unban"
    elif cmd in _BAN:
        action = "ban"
    if not action:
        return None
    n = m.group("n")
    unit = m.group("u")
    seconds = 0
    if action in ("mute", "ban"):
        if not n or not unit:
            return None
        seconds = int(n) * _UNITS[unit.lower()]
        if seconds <= 0:
            return None
        seconds = min(seconds, MUTE_MAX_SECONDS)
    who = (m.group("who") or "").strip() or None
    return {"action": action, "seconds": seconds, "username": who}
