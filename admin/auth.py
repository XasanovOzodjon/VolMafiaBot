from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from data import config


class AuthRedirect(Exception):
    def __init__(self, url: str = "/login"):
        self.url = url


def _same_text(a: str, b: str) -> bool:
    ha = hashlib.sha256(a.encode()).digest()
    hb = hashlib.sha256(b.encode()).digest()
    return hmac.compare_digest(ha, hb)


def check_password(login: str, password: str) -> bool:
    return _same_text(login.strip(), config.PANEL_LOGIN) and _same_text(
        password.strip(), config.PANEL_PASSWORD
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), 120_000
    )
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, hx = stored.split("$", 1)
    try:
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), 120_000
        )
    except ValueError:
        return False
    return hmac.compare_digest(dk.hex(), hx)


def check_telegram_login(data: dict) -> bool:
    check_hash = str(data.get("hash") or "")
    if not check_hash:
        return False
    parts = []
    for key in sorted(k for k in data.keys() if k != "hash"):
        val = data.get(key)
        if val is None or val == "":
            continue
        parts.append(f"{key}={val}")
    secret = hashlib.sha256(config.BOT_TOKEN.encode()).digest()
    digest = hmac.new(secret, "\n".join(parts).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, check_hash):
        return False
    try:
        auth_date = int(data.get("auth_date") or 0)
    except (TypeError, ValueError):
        return False
    return abs(time.time() - auth_date) < 86400


def check_webapp_init_data(init_data: str, max_age: int = 86400) -> dict | None:
    from urllib.parse import parse_qsl
    import json

    if not init_data:
        return None
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    got = str(pairs.pop("hash", "") or "")
    if not got:
        return None
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, got):
        return None
    try:
        auth_date = int(pairs.get("auth_date") or 0)
    except (TypeError, ValueError):
        return None
    if abs(time.time() - auth_date) > max_age:
        return None
    try:
        user = json.loads(pairs.get("user") or "")
    except (TypeError, ValueError):
        return None
    if not isinstance(user, dict):
        return None
    try:
        uid = int(user.get("id") or 0)
    except (TypeError, ValueError):
        return None
    if uid <= 0:
        return None
    lang = str(user.get("language_code") or "uz").lower()[:8]
    if lang.startswith("ru"):
        lang = "ru"
    elif lang.startswith("en"):
        lang = "en"
    else:
        lang = "uz"
    return {"id": uid, "user": user, "lang": lang}
