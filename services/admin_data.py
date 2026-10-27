from __future__ import annotations

import json
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Optional

DEFAULT_SHOP: list[dict[str, Any]] = [
    {
        "id": "protection",
        "emoji": "🛡️",
        "title_uz": "Ximoya",
        "title_ru": "Защита",
        "desc_uz": "1 marta tunda mafia, komissar o‘ldirishi, manyak va padrajiteldan saqlaydi. Yakudza va osishdan saqlamaydi.",
        "desc_ru": "1 раз ночью спасает от мафии, выстрела комиссара, маньяка и падражителя. Не от якудзы и повешения.",
        "field": "protection",
        "amount": 1,
        "money": 80,
        "vcoin": 0,
        "enabled": True,
    },
    {
        "id": "documents",
        "emoji": "📁",
        "title_uz": "Hujjatlar",
        "title_ru": "Документы",
        "desc_uz": "Komissar, jurnalist va serjant tekshiruvida tinch aholi bo‘lib ko‘rinasiz.",
        "desc_ru": "Проверки комиссара, журналиста и сержанта видят вас мирным.",
        "field": "documents",
        "amount": 1,
        "money": 60,
        "vcoin": 0,
        "enabled": True,
    },
    {
        "id": "active_role",
        "emoji": "🎎",
        "title_uz": "Faol rol",
        "title_ru": "Активная роль",
        "desc_uz": "99% faol rol: shu o‘yinda tinch aholi yoki yakudza tushmaydi. Guruhda «Faol rol» deb chiqadi.",
        "desc_ru": "99% активная роль: в этой игре не будете мирным или якудзой. В чате — «Активная роль».",
        "field": "active_role",
        "amount": 1,
        "money": 0,
        "vcoin": 12,
        "enabled": True,
    },
    {
        "id": "chosen_role",
        "emoji": "🎭",
        "title_uz": "Tanlangan rol",
        "title_ru": "Выбранная роль",
        "desc_uz": "O‘yin boshida o‘zingiz tanlagan rolni olasiz (tarkibdagi o‘rin).",
        "desc_ru": "В начале игры получите выбранную роль (слот состава).",
        "field": "chosen_role",
        "amount": 1,
        "money": 0,
        "vcoin": 20,
        "enabled": True,
    },
]

SHOP_FIELDS = ("protection", "documents", "active_role", "chosen_role")
SHART_KINDS = ("play", "win", "lose", "buy", "toldirish", "groups")
ARM_FLAGS = {
    "protection": "armed_protection",
    "documents": "armed_documents",
    "active_role": "armed_active",
    "chosen_role": "armed_chosen",
}
DEFAULT_VCOIN_PACKS: list[dict[str, Any]] = [
    {"id": "p50", "kind": "vcoin", "vcoin": 50, "money": 0, "stars": 50, "enabled": True},
    {"id": "p150", "kind": "vcoin", "vcoin": 150, "money": 0, "stars": 140, "enabled": True},
    {"id": "p400", "kind": "vcoin", "vcoin": 400, "money": 0, "stars": 350, "enabled": True},
    {"id": "m50", "kind": "money", "vcoin": 0, "money": 50, "stars": 50, "enabled": True},
    {"id": "m150", "kind": "money", "vcoin": 0, "money": 150, "stars": 140, "enabled": True},
    {"id": "m400", "kind": "money", "vcoin": 0, "money": 400, "stars": 350, "enabled": True},
]
DEFAULT_MONEY_PACKS: list[dict[str, Any]] = [
    {"id": "m50", "kind": "money", "vcoin": 0, "money": 50, "stars": 50, "enabled": True},
    {"id": "m150", "kind": "money", "vcoin": 0, "money": 150, "stars": 140, "enabled": True},
    {"id": "m400", "kind": "money", "vcoin": 0, "money": 400, "stars": 350, "enabled": True},
]
DEFAULT_SWAPS: list[dict[str, Any]] = [
    {"id": "s50", "vcoin": 50, "money": 50, "enabled": True},
    {"id": "s150", "vcoin": 150, "money": 150, "enabled": True},
    {"id": "s400", "vcoin": 400, "money": 400, "enabled": True},
]


def swap_is_listed(item: dict | None) -> bool:
    if not isinstance(item, dict) or not item.get("id"):
        return False
    if not item.get("enabled", True):
        return False
    return int(item.get("vcoin") or 0) > 0 and int(item.get("money") or 0) > 0
DEFAULT_GIFTS: list[dict[str, Any]] = [
    {
        "id": "phone",
        "emoji": "📱",
        "title_uz": "Telefon",
        "title_ru": "Телефон",
        "title_en": "Phone",
        "desc_uz": "Real sovg‘a. Admin qo‘lda yuboradi (aloqa LSda).",
        "desc_ru": "Реальный подарок. Админ выдаёт вручную.",
        "desc_en": "Real gift. Admin fulfills by hand.",
        "vcoin": 8000,
        "enabled": True,
    },
    {
        "id": "card",
        "emoji": "💳",
        "title_uz": "Karta 50 000 so‘m",
        "title_ru": "Карта 50 000 сум",
        "title_en": "Card 50 000 UZS",
        "desc_uz": "Real pul/karta. Admin qo‘lda yuboradi.",
        "desc_ru": "Реальные деньги. Админ выдаёт вручную.",
        "desc_en": "Cash/card. Admin fulfills by hand.",
        "vcoin": 3000,
        "enabled": True,
    },
    {
        "id": "premium",
        "emoji": "⭐",
        "title_uz": "Telegram Premium (1 oy)",
        "title_ru": "Telegram Premium (1 мес.)",
        "title_en": "Telegram Premium (1 month)",
        "desc_uz": "Admin Premium ni qo‘lda beradi.",
        "desc_ru": "Админ выдаёт Premium вручную.",
        "desc_en": "Admin grants Premium by hand.",
        "vcoin": 1200,
        "enabled": True,
    },
    {
        "id": "buds",
        "emoji": "🎧",
        "title_uz": "Quloqchin",
        "title_ru": "Наушники",
        "title_en": "Earbuds",
        "desc_uz": "Real sovg‘a. Admin qo‘lda yuboradi.",
        "desc_ru": "Реальный подарок. Админ выдаёт вручную.",
        "desc_en": "Real gift. Admin fulfills by hand.",
        "vcoin": 4500,
        "enabled": True,
    },
]

ROLES = ("super", "moderator", "ads")
_IMG_ID_RE = re.compile(r"^[a-z0-9_]{2,20}$")


def resolve_catalog_id(raw: str, existing, prefix: str = "x") -> str:
    raw = (raw or "").strip().lower()
    if _IMG_ID_RE.match(raw):
        return raw
    return new_catalog_id(existing, prefix)


def new_catalog_id(existing, prefix: str = "x") -> str:
    taken = set()
    for row in existing or []:
        if isinstance(row, dict):
            taken.add(str(row.get("id") or ""))
        else:
            taken.add(str(row))
    prefix = re.sub(r"[^a-z0-9]", "", (prefix or "x").lower())[:4] or "x"
    for _ in range(48):
        nid = prefix + secrets.token_hex(4)
        if _IMG_ID_RE.match(nid) and nid not in taken:
            return nid
    raise RuntimeError("catalog id")


def catalog_image(item: dict | None = None, *, pack: bool = False) -> str:
    item = item or {}
    img = str(item.get("image") or "").strip()
    path = img.split("?", 1)[0]
    if (
        path.startswith("/")
        and ".." not in path
        and " " not in path
        and (
            path.startswith("/static/shop/")
            or path.startswith("/media/shop/")
            or path.startswith("/media/gifts/")
            or path.startswith("/media/swaps/")
            or path.startswith("/media/badges/")
        )
    ):
        return path[:160]
    if pack:
        if str(item.get("kind") or "") in ("money", "swap"):
            return "/static/shop/card.jpg"
        return "/static/shop/vcoin.jpg"
    if "ranks" in item:
        return ""
    iid = str(item.get("id") or "").strip()
    if iid and _IMG_ID_RE.match(iid):
        return f"/static/shop/{iid}.jpg"
    return "/static/shop/vcoin.jpg"


def normalize_stats(data: dict | None) -> dict:
    data = dict(data or {})
    if data.get("vcoin") is None:
        vcoin = int(data.get("gems") or 0)
    else:
        vcoin = int(data.get("vcoin") or 0)
    chosen_inv = data.get("chosen_role")
    if isinstance(chosen_inv, str):
        chosen_inv = data.get("chosen_role_count") or 0
    return {
        "games": int(data.get("games") or 0),
        "wins": int(data.get("wins") or 0),
        "money": int(data.get("money") or 0),
        "vcoin": vcoin,
        "gems": vcoin,
        "protection": int(data.get("protection") or 0),
        "documents": int(data.get("documents") or 0),
        "active_role": int(data.get("active_role") or 0),
        "chosen_role": int(chosen_inv or 0),
        "chosen_pick": str(data.get("chosen_pick") or ""),
        "armed_protection": bool(data.get("armed_protection")),
        "armed_documents": bool(data.get("armed_documents")),
        "armed_active": bool(data.get("armed_active")),
        "armed_chosen": bool(data.get("armed_chosen")),
        "name": str(data.get("name") or ""),
        "daily_streak": int(data.get("daily_streak") or 0),
        "last_daily_ts": int(data.get("last_daily_ts") or 0),
        "ref_by": int(data.get("ref_by") or 0) if data.get("ref_by") else None,
        "ref_count": int(data.get("ref_count") or 0),
        "ref_earnings": int(data.get("ref_earnings") or 0),
        "ref_rewarded": bool(data.get("ref_rewarded")),
        "boxes_opened": int(data.get("boxes_opened") or 0),
        "is_vip": bool(data.get("is_vip")),
        "vip_until": int(data.get("vip_until") or 0),
    }


def _migrate_shop_item(item: dict) -> dict:
    out = dict(item)
    if "vcoin" not in out:
        out["vcoin"] = int(out.get("gems") or 0)
    out.pop("gems", None)
    field = str(out.get("field") or "")
    if field in ("protection", "documents"):
        out["vcoin"] = 0
        out["money"] = int(out.get("money") or 0)
    elif field in ("active_role", "chosen_role"):
        out["money"] = 0
        out["vcoin"] = int(out.get("vcoin") or 0)
    else:
        out["money"] = int(out.get("money") or 0)
        out["vcoin"] = int(out.get("vcoin") or 0)
    out["enabled"] = bool(out.get("enabled", True))
    out["amount"] = max(1, int(out.get("amount") or 1))
    out["image"] = str(out.get("image") or "").strip()
    return out


def _now() -> int:
    return int(time.time())


def _badge_ranks(raw) -> list[dict]:
    rows: list[dict] = []
    if not isinstance(raw, list):
        return rows
    for i, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        rank = int(item.get("rank") or i)
        cost = max(0, int(item.get("vcoin_cost") or 0))
        shart = str(item.get("shart_uz") or item.get("shart") or "").strip()
        if rank < 1 or not shart:
            continue
        kind = str(item.get("kind") or "").strip().lower()
        if kind not in SHART_KINDS:
            kind = ""
        currency = str(item.get("currency") or "").strip().lower()
        if currency not in ("money", "vcoin"):
            currency = "vcoin"
        field = str(item.get("item") or "").strip()
        if field not in SHOP_FIELDS:
            field = ""
        rows.append(
            {
                "rank": rank,
                "shart_uz": str(item.get("shart_uz") or shart)[:200],
                "shart_ru": str(item.get("shart_ru") or "")[:200],
                "shart_en": str(item.get("shart_en") or "")[:200],
                "vcoin_cost": cost,
                "kind": kind,
                "n": max(0, int(item.get("n") or 0)),
                "role": str(item.get("role") or "").strip()[:40],
                "item": field,
                "currency": currency,
                "groups": max(0, int(item.get("groups") or 0)),
            }
        )
    rows.sort(key=lambda x: x["rank"])
    return rows


def _loc(item: dict, stem: str, lang: str) -> str:
    lang = lang if lang in ("uz", "ru", "en") else "uz"
    direct = str(item.get(f"{stem}_{lang}") or "").strip()
    if direct:
        return direct
    return str(
        item.get(f"{stem}_uz") or item.get(f"{stem}_ru") or item.get(stem) or ""
    ).strip()


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AdminData:
    """Guruhlar, userlar, do'kon, reklama, staff — Redis."""

    redis = None  # GameStore o'rnatadi

    async def touch_user(self, user) -> None:
        if not user or getattr(user, "is_bot", False):
            return
        uid = int(user.id)
        is_new = not await self.redis.sismember("mafia:players", str(uid))
        await self.redis.sadd("mafia:players", str(uid))
        name = (getattr(user, "full_name", None) or user.first_name or str(uid))[:80]
        username = getattr(user, "username", None) or ""
        await self.redis.set(f"mafia:uname:{uid}", name)
        await self.redis.hset(
            f"mafia:profile:{uid}",
            mapping={
                "name": name,
                "username": username,
                "last_seen": str(_now()),
            },
        )
        stats = await self.get_stats(uid)
        if name and not stats.get("name"):
            stats["name"] = name
            await self.save_stats(uid, stats)
        if is_new:
            await self.bump_metric("new_users", 1)
            await self.redis.zadd("mafia:rank:global", {str(uid): stats["money"]})

    async def touch_group(self, chat, *, member_count: int | None = None) -> None:
        if not chat or chat.type not in ("group", "supergroup"):
            return
        cid = int(chat.id)
        await self.redis.sadd("mafia:groups", str(cid))
        data = {
            "id": str(cid),
            "title": chat.title or str(cid),
            "username": chat.username or "",
            "type": chat.type,
            "last_seen": str(_now()),
            "left": "0",
        }
        if member_count is not None:
            data["members"] = str(member_count)
        await self.redis.hset(f"mafia:group:{cid}", mapping=data)

    async def mark_group_left(self, chat_id: int, left: bool = True) -> None:
        await self.redis.hset(
            f"mafia:group:{chat_id}",
            mapping={"left": "1" if left else "0", "last_seen": str(_now())},
        )
        if left:
            await self.unmark_live(chat_id)

    async def note_group_player(self, chat_id: int, user_id: int) -> None:
        await self.redis.zadd(
            f"mafia:group:{chat_id}:active", {str(user_id): float(_now())}
        )
        await self.redis.sadd(f"mafia:group:{chat_id}:known", str(user_id))

    async def mark_live(self, chat_id: int) -> None:
        await self.redis.sadd("mafia:live", str(chat_id))

    async def unmark_live(self, chat_id: int) -> None:
        await self.redis.srem("mafia:live", str(chat_id))

    async def live_chat_ids(self) -> list[int]:
        raw = await self.redis.smembers("mafia:live")
        return [int(x) for x in raw]

    async def live_games(self) -> list[dict]:
        from game.models import Phase

        out = []
        for cid in await self.live_chat_ids():
            game = await self.get(cid)
            if not game or game.deleted or game.phase == Phase.ENDED:
                await self.unmark_live(cid)
                continue
            info = await self.get_group_info(cid)
            alive = sum(1 for p in game.players.values() if p.alive)
            out.append(
                {
                    "chat_id": cid,
                    "title": info.get("title") or str(cid),
                    "phase": game.phase,
                    "night": game.night_number,
                    "players": len(game.players),
                    "alive": alive,
                    "test": bool(getattr(game, "test_mode", False)),
                }
            )
        return out

    async def top_groups(self, limit: int = 8) -> list[dict]:
        groups = await self.list_groups()
        groups.sort(key=lambda g: int((g.get("stats") or {}).get("games") or 0), reverse=True)
        return groups[:limit]

    async def seed_env_admins(self) -> None:
        from data import config

        for raw in config.ADMINS:
            try:
                uid = int(str(raw).strip())
            except ValueError:
                continue
            await self.set_staff(uid, "super")

    async def staff_list(self) -> list[dict]:
        from data import config

        env_ids = {str(a).strip() for a in config.ADMINS if str(a).strip()}
        mapping = await self.staff_map()
        out = []
        for uid, role in mapping.items():
            stats = await self.get_stats(int(uid))
            out.append(
                {
                    "id": int(uid),
                    "role": role,
                    "name": stats.get("name") or str(uid),
                    "env": str(uid) in env_ids,
                    "panel_user": (await self.staff_creds(int(uid))).get("user") or "",
                }
            )
        out.sort(key=lambda x: (0 if x["role"] == "super" else 1, x["name"]))
        return out

    async def pending_ads(self) -> list[dict]:
        now = _now()
        out = []
        for ad in await self.list_ads(100):
            status = ad.get("status")
            send_at = int(ad.get("send_at") or 0)
            if status == "sending":
                out.append(ad)
            elif status == "scheduled" and send_at > now:
                out.append(ad)
        return out

    async def bump_metric(self, field: str, amount: int = 1, day: str | None = None) -> None:
        day = day or _day()
        await self.redis.hincrby(f"mafia:metric:{day}", field, amount)
        await self.redis.sadd("mafia:metric:days", day)

    async def metrics_series(self, days: int = 14) -> list[dict]:
        names = sorted(await self.redis.smembers("mafia:metric:days"))[-days:]
        out = []
        for day in names:
            row = await self.redis.hgetall(f"mafia:metric:{day}")
            out.append(
                {
                    "day": day,
                    "games": int(row.get("games") or 0),
                    "new_users": int(row.get("new_users") or 0),
                    "money": int(row.get("money") or 0),
                    "ads": int(row.get("ads") or 0),
                }
            )
        return out

    async def list_groups(self) -> list[dict]:
        ids = await self.redis.smembers("mafia:groups")
        groups = []
        for raw in ids:
            cid = int(raw)
            info = await self.get_group_info(cid)
            if info:
                groups.append(info)
        groups.sort(key=lambda g: int(g.get("last_seen") or 0), reverse=True)
        return groups

    async def get_group_info(self, chat_id: int) -> dict:
        raw = await self.redis.hgetall(f"mafia:group:{chat_id}")
        settings = await self.get_chat_settings(chat_id)
        stats = await self.get_group_stats(chat_id)
        known = await self.redis.scard(f"mafia:group:{chat_id}:known")
        if not raw and not stats["games"]:
            return {
                "id": chat_id,
                "title": str(chat_id),
                "username": "",
                "members": 0,
                "known": int(known or 0),
                "left": False,
                "last_seen": 0,
                "last_game": 0,
                "settings": settings,
                "stats": stats,
            }
        return {
            "id": chat_id,
            "title": raw.get("title") or str(chat_id),
            "username": raw.get("username") or "",
            "members": int(raw.get("members") or 0),
            "known": int(known or 0),
            "left": raw.get("left") == "1",
            "last_seen": int(raw.get("last_seen") or 0),
            "last_game": int(raw.get("last_game") or 0),
            "settings": settings,
            "stats": stats,
        }

    async def group_active_users(self, chat_id: int, limit: int = 30) -> list[dict]:
        rows = await self.redis.zrevrange(
            f"mafia:group:{chat_id}:active", 0, limit - 1, withscores=True
        )
        out = []
        for uid, score in rows:
            stats = await self.get_stats(int(uid))
            out.append(
                {
                    "id": int(uid),
                    "name": stats.get("name") or str(uid),
                    "at": int(score),
                }
            )
        return out

    async def list_users(self, limit: int = 80, q: str = "") -> list[dict]:
        q = (q or "").strip().lower()
        ids: list[int] = []
        if q.lstrip("-").isdigit():
            ids = [int(q)]
        else:
            rows = await self.redis.zrevrange("mafia:rank:global", 0, 400, withscores=True)
            for uid, _ in rows:
                ids.append(int(uid))
            extra = await self.redis.smembers("mafia:players")
            for uid in extra:
                n = int(uid)
                if n not in ids:
                    ids.append(n)
        out = []
        for uid in ids:
            stats = await self.get_stats(uid)
            name = stats.get("name") or str(uid)
            prof = await self.redis.hgetall(f"mafia:profile:{uid}")
            username = (prof.get("username") or "") if prof else ""
            hay = f"{name} {username} {uid}".lower()
            if q and not q.lstrip("-").isdigit() and q not in hay:
                continue
            out.append(
                {
                    "id": uid,
                    "name": name,
                    "username": username,
                    "stats": stats,
                    "banned": await self.is_user_banned(uid),
                    "last_seen": int((prof or {}).get("last_seen") or 0),
                }
            )
            if len(out) >= limit:
                break
        return out

    async def is_user_banned(self, user_id: int) -> bool:
        return bool(await self.redis.sismember("mafia:ban:users", str(user_id)))

    async def is_group_banned(self, chat_id: int) -> bool:
        return bool(await self.redis.sismember("mafia:ban:groups", str(chat_id)))

    async def set_user_banned(self, user_id: int, banned: bool) -> None:
        if banned:
            await self.redis.sadd("mafia:ban:users", str(user_id))
        else:
            await self.redis.srem("mafia:ban:users", str(user_id))

    async def set_group_banned(self, chat_id: int, banned: bool) -> None:
        if banned:
            await self.redis.sadd("mafia:ban:groups", str(chat_id))
        else:
            await self.redis.srem("mafia:ban:groups", str(chat_id))

    async def get_stats(self, user_id: int) -> dict:
        raw = await self.redis.get(f"mafia:stats:{user_id}")
        if not raw:
            return normalize_stats(None)
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        stats = normalize_stats(data)
        if "vcoin" not in data and data.get("gems") is not None:
            await self.save_stats(user_id, stats)
        return stats

    async def save_stats(self, user_id: int, stats: dict) -> dict:
        stats = normalize_stats(stats)
        await self.redis.set(
            f"mafia:stats:{user_id}", json.dumps(stats, ensure_ascii=False)
        )
        await self.redis.zadd("mafia:rank:global", {str(user_id): stats["money"]})
        if stats.get("name"):
            await self.redis.set(f"mafia:uname:{user_id}", stats["name"])
        return stats

    async def add_econ_log(self, user_id: int, *, kind: str, **extra) -> None:
        entry = {
            "ts": _now(),
            "user_id": int(user_id),
            "kind": str(kind),
            **{k: v for k, v in extra.items() if v not in (None, "")},
        }
        raw = json.dumps(entry, ensure_ascii=False)
        await self.redis.lpush("mafia:econ:log", raw)
        await self.redis.ltrim("mafia:econ:log", 0, 1999)
        await self.redis.lpush(f"mafia:econ:user:{user_id}", raw)
        await self.redis.ltrim(f"mafia:econ:user:{user_id}", 0, 199)

    async def list_econ_logs(
        self, limit: int = 120, user_id: int | None = None
    ) -> list[dict]:
        key = f"mafia:econ:user:{user_id}" if user_id else "mafia:econ:log"
        rows = await self.redis.lrange(key, 0, limit - 1)
        out = []
        for raw in rows:
            try:
                item = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if isinstance(item, dict):
                out.append(item)
        return out

    async def adjust_balance(
        self,
        user_id: int,
        *,
        money: int = 0,
        vcoin: int = 0,
        gems: int = 0,
        reason: str = "admin",
    ) -> dict:
        if gems and not vcoin:
            vcoin = gems
        money = int(money or 0)
        vcoin = int(vcoin or 0)
        stats = await self.get_stats(user_id)
        applied_money = 0
        applied_vcoin = 0
        if money:
            applied_money = money if money > 0 else max(money, -int(stats["money"]))
            stats["money"] = int(stats["money"]) + applied_money
        if vcoin:
            applied_vcoin = vcoin if vcoin > 0 else max(vcoin, -int(stats["vcoin"]))
            stats["vcoin"] = int(stats["vcoin"]) + applied_vcoin
        stats = await self.save_stats(user_id, stats)
        if applied_money or applied_vcoin:
            await self.add_econ_log(
                user_id,
                kind="admin_grant",
                money=applied_money or None,
                vcoin=applied_vcoin or None,
                detail=reason,
            )
        return stats

    async def credit_vcoin(
        self, user_id: int, amount: int, *, kind: str, detail: str = ""
    ) -> dict:
        amount = int(amount or 0)
        stats = await self.get_stats(user_id)
        stats["vcoin"] = max(0, stats["vcoin"] + amount)
        stats = await self.save_stats(user_id, stats)
        await self.add_econ_log(
            user_id, kind=kind, vcoin=amount, detail=detail
        )
        if str(kind) == "stars" and amount > 0:
            await self._bump_stars(user_id, vcoin=amount)
            await self.evaluate_auto_shart(user_id)
        return stats

    async def credit_money(
        self, user_id: int, amount: int, *, kind: str, detail: str = ""
    ) -> dict:
        amount = int(amount or 0)
        stats = await self.get_stats(user_id)
        stats["money"] = max(0, stats["money"] + amount)
        stats = await self.save_stats(user_id, stats)
        await self.add_econ_log(
            user_id, kind=kind, money=amount, detail=detail
        )
        if str(kind) == "stars" and amount > 0:
            await self._bump_stars(user_id, money=amount)
            await self.evaluate_auto_shart(user_id)
        return stats

    async def maintenance(self) -> bool:
        raw = await self.redis.get("mafia:maintenance")
        return raw == "1"

    async def set_maintenance(self, on: bool) -> None:
        await self.redis.set("mafia:maintenance", "1" if on else "0")

    async def ensure_shop(self) -> list[dict]:
        raw = await self.redis.get("mafia:shop")
        items: list[dict] = []
        if raw:
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, list):
                    items = [
                        _migrate_shop_item(x)
                        for x in loaded
                        if isinstance(x, dict) and x.get("id")
                    ]
            except (TypeError, ValueError):
                items = []
        have = {str(x.get("id")) for x in items}
        changed = not items or ("gems" in (raw or ""))
        for default in DEFAULT_SHOP:
            if default["id"] not in have:
                items.append(dict(default))
                changed = True
                have.add(default["id"])
        if changed:
            await self.save_shop(items)
        return items

    async def save_shop(self, items: list[dict]) -> None:
        await self.redis.set("mafia:shop", json.dumps(items, ensure_ascii=False))

    async def shop_item(self, item_id: str) -> Optional[dict]:
        for item in await self.ensure_shop():
            if item.get("id") == item_id:
                return item
        return None

    async def upsert_shop_item(self, item: dict) -> list[dict]:
        items = await self.ensure_shop()
        for i, old in enumerate(items):
            if old.get("id") == item["id"]:
                merged = dict(old)
                merged.update(item)
                if not str(merged.get("image") or "").strip():
                    merged["image"] = old.get("image") or ""
                items[i] = _migrate_shop_item(merged)
                await self.save_shop(items)
                return items
        items.append(_migrate_shop_item(dict(item)))
        await self.save_shop(items)
        return items

    async def delete_shop_item(self, item_id: str) -> list[dict]:
        items = [x for x in await self.ensure_shop() if x.get("id") != item_id]
        await self.save_shop(items)
        return items

    async def buy_item(self, user_id: int, item_id: str, pay: str) -> tuple[bool, str, dict]:
        lock = self.redis.lock(f"mafia:lock:user:{user_id}", timeout=10, blocking_timeout=5)
        await lock.acquire()
        try:
            item = await self.shop_item(item_id)
            if not item or not item.get("enabled", True):
                return False, "missing", await self.get_stats(user_id)
            stats = await self.get_stats(user_id)
            pay = "vcoin" if pay in ("vcoin", "gems") else "money"
            price = int(item.get("vcoin") or 0) if pay == "vcoin" else int(item.get("money") or 0)
            wallet = "vcoin" if pay == "vcoin" else "money"
            if price <= 0:
                return False, "no_price", stats
            if int(stats.get(wallet) or 0) < price:
                return False, "broke", stats
            stats[wallet] = int(stats[wallet]) - price
            field = str(item.get("field") or "")
            if field in SHOP_FIELDS:
                stats[field] = int(stats.get(field) or 0) + int(item.get("amount") or 1)
            stats = await self.save_stats(user_id, stats)
            await self.add_econ_log(
                user_id,
                kind="shop_buy",
                money=(-price if wallet == "money" else None),
                vcoin=(-price if wallet == "vcoin" else None),
                item=item_id,
                pay=wallet,
            )
            if field in SHOP_FIELDS:
                await self._bump_buy(user_id, field)
                await self.evaluate_auto_shart(user_id)
            return True, "ok", stats
        finally:
            try:
                await lock.release()
            except Exception:
                pass

    async def arm_shop_item(
        self, user_id: int, field: str
    ) -> tuple[bool, str, dict]:
        stats = await self.get_stats(user_id)
        if field not in ARM_FLAGS:
            return False, "missing", stats
        if int(stats.get(field) or 0) <= 0:
            return False, "need_item", stats
        if field == "chosen_role" and not str(stats.get("chosen_pick") or ""):
            return False, "need_pick", stats
        flag = ARM_FLAGS[field]
        if stats.get(flag):
            return True, "already", stats
        stats[flag] = True
        stats = await self.save_stats(user_id, stats)
        await self.add_econ_log(user_id, kind="shop_arm", item=field)
        return True, "ok", stats

    async def set_chosen_pick(
        self, user_id: int, role: str
    ) -> tuple[bool, str, dict]:
        from game.roles import Role

        stats = await self.get_stats(user_id)
        try:
            Role(role)
        except ValueError:
            return False, "missing", stats
        if int(stats.get("chosen_role") or 0) <= 0:
            return False, "need_item", stats
        stats["chosen_pick"] = role
        stats = await self.save_stats(user_id, stats)
        await self.add_econ_log(user_id, kind="role_pick", item=role)
        return True, "ok", stats

    async def consume_shop_item(
        self, user_id: int, field: str, reason: str = ""
    ) -> dict:
        stats = await self.get_stats(user_id)
        if field not in ARM_FLAGS:
            return stats
        n = int(stats.get(field) or 0)
        if n > 0:
            stats[field] = n - 1
        stats[ARM_FLAGS[field]] = False
        stats = await self.save_stats(user_id, stats)
        await self.add_econ_log(
            user_id, kind="shop_consume", item=field, detail=reason
        )
        return stats

    async def staff_map(self) -> dict[str, str]:
        raw = await self.redis.hgetall("mafia:staff")
        return {str(k): str(v) for k, v in (raw or {}).items()}

    async def staff_role(self, user_id: int) -> Optional[str]:
        raw = await self.redis.hget("mafia:staff", str(user_id))
        return raw if raw in ROLES else None

    async def set_staff(self, user_id: int, role: str, name: str = "") -> None:
        if role not in ROLES:
            raise ValueError("role")
        await self.redis.hset("mafia:staff", str(user_id), role)
        if name:
            await self.redis.set(f"mafia:uname:{user_id}", name)

    async def remove_staff(self, user_id: int) -> None:
        cred = await self.staff_creds(user_id)
        login = str(cred.get("user") or "").strip().lower()
        if login:
            await self.redis.delete(f"mafia:staff:login:{login}")
        await self.redis.delete(f"mafia:staff:cred:{user_id}")
        await self.redis.hdel("mafia:staff", str(user_id))

    async def staff_creds(self, user_id: int) -> dict:
        raw = await self.redis.get(f"mafia:staff:cred:{user_id}")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    async def set_staff_panel_login(
        self, user_id: int, username: str, password: str
    ) -> str:
        from data import config
        from admin.auth import hash_password

        username = (username or "").strip().lower()
        password = (password or "").strip()
        if username and not re.fullmatch(r"[a-z0-9_.]{3,32}", username):
            return "bad_user"
        old = await self.staff_creds(user_id)
        old_user = str(old.get("user") or "").strip().lower()
        if username and username == (config.PANEL_LOGIN or "").strip().lower():
            return "taken"
        if username:
            taken = await self.redis.get(f"mafia:staff:login:{username}")
            if taken and str(taken) != str(user_id):
                return "taken"
        if old_user and old_user != username:
            await self.redis.delete(f"mafia:staff:login:{old_user}")
        cred = dict(old)
        if username:
            cred["user"] = username
        elif not cred.get("user"):
            return "ok"
        if password:
            cred["hash"] = hash_password(password)
        if not cred.get("user"):
            await self.redis.delete(f"mafia:staff:cred:{user_id}")
            return "ok"
        await self.redis.set(
            f"mafia:staff:cred:{user_id}", json.dumps(cred, ensure_ascii=False)
        )
        await self.redis.set(f"mafia:staff:login:{cred['user']}", str(user_id))
        return "ok"

    async def find_staff_by_login(self, username: str) -> dict | None:
        key = (username or "").strip().lower()
        if not key:
            return None
        raw_id = await self.redis.get(f"mafia:staff:login:{key}")
        if not raw_id:
            return None
        try:
            uid = int(raw_id)
        except (TypeError, ValueError):
            return None
        role = await self.staff_role(uid)
        cred = await self.staff_creds(uid)
        if not role or not cred.get("hash"):
            return None
        stats = await self.get_stats(uid)
        return {
            "id": uid,
            "role": role,
            "name": stats.get("name") or cred.get("user") or str(uid),
            "hash": cred["hash"],
        }

    async def login_blocked(self, ip: str) -> bool:
        n = int(await self.redis.get(f"mafia:panel:fail:{ip}") or 0)
        return n >= 8

    async def note_login_fail(self, ip: str) -> None:
        key = f"mafia:panel:fail:{ip}"
        n = await self.redis.incr(key)
        if n == 1:
            await self.redis.expire(key, 15 * 60)

    async def clear_login_fail(self, ip: str) -> None:
        await self.redis.delete(f"mafia:panel:fail:{ip}")

    async def add_audit(self, entry: dict) -> None:
        await self.redis.lpush(
            "mafia:panel:audit", json.dumps(entry, ensure_ascii=False)
        )
        await self.redis.ltrim("mafia:panel:audit", 0, 399)

    async def list_audit(self, limit: int = 80) -> list[dict]:
        rows = await self.redis.lrange("mafia:panel:audit", 0, limit - 1)
        out = []
        for raw in rows:
            try:
                item = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if isinstance(item, dict):
                out.append(item)
        return out

    async def ensure_vcoin_packs(self) -> list[dict]:
        raw = await self.redis.get("mafia:vcoin:packs")
        items: list[dict] = []
        if raw:
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, list) and loaded:
                    items = [dict(x) for x in loaded if isinstance(x, dict)]
            except (TypeError, ValueError):
                items = []
        if not items:
            items = [dict(x) for x in DEFAULT_VCOIN_PACKS]
            await self.save_vcoin_packs(items)
            return items
        changed = False
        ids = {str(x.get("id") or "") for x in items}
        for row in items:
            kind = str(row.get("kind") or "")
            if kind not in ("vcoin", "money"):
                row["kind"] = (
                    "money"
                    if int(row.get("money") or 0) > 0 and int(row.get("vcoin") or 0) <= 0
                    else "vcoin"
                )
                changed = True
        if not any(str(x.get("kind") or "") == "money" for x in items):
            for pack in DEFAULT_MONEY_PACKS:
                if pack["id"] not in ids:
                    items.append(dict(pack))
                    changed = True
        if changed:
            await self.save_vcoin_packs(items)
        return items

    async def save_vcoin_packs(self, items: list[dict]) -> None:
        await self.redis.set(
            "mafia:vcoin:packs", json.dumps(items, ensure_ascii=False)
        )

    async def vcoin_pack(self, pack_id: str) -> Optional[dict]:
        for item in await self.ensure_vcoin_packs():
            if item.get("id") == pack_id and item.get("enabled", True):
                return item
        return None

    async def upsert_vcoin_pack(self, pack: dict) -> list[dict]:
        items = await self.ensure_vcoin_packs()
        found = False
        for i, old in enumerate(items):
            if old.get("id") == pack["id"]:
                items[i] = pack
                found = True
                break
        if not found:
            items.append(pack)
        await self.save_vcoin_packs(items)
        return items

    async def delete_vcoin_pack(self, pack_id: str) -> list[dict]:
        items = [x for x in await self.ensure_vcoin_packs() if x.get("id") != pack_id]
        await self.save_vcoin_packs(items)
        return items

    async def ensure_swaps(self) -> list[dict]:
        raw = await self.redis.get("mafia:vcoin:swap")
        if raw:
            try:
                items = json.loads(raw)
                if isinstance(items, list) and items:
                    return [dict(x) for x in items if isinstance(x, dict)]
            except (TypeError, ValueError):
                pass
        items = [dict(x) for x in DEFAULT_SWAPS]
        await self.redis.set("mafia:vcoin:swap", json.dumps(items, ensure_ascii=False))
        return items

    async def save_swaps(self, items: list[dict]) -> None:
        await self.redis.set("mafia:vcoin:swap", json.dumps(items, ensure_ascii=False))

    async def swap_offer(self, offer_id: str) -> Optional[dict]:
        for item in await self.ensure_swaps():
            if item.get("id") == offer_id and swap_is_listed(item):
                return item
        return None

    async def listed_swaps(self) -> list[dict]:
        return [x for x in await self.ensure_swaps() if swap_is_listed(x)]

    async def upsert_swap(self, offer: dict) -> list[dict]:
        items = await self.ensure_swaps()
        found = False
        for i, old in enumerate(items):
            if old.get("id") == offer["id"]:
                items[i] = offer
                found = True
                break
        if not found:
            items.append(offer)
        await self.save_swaps(items)
        return items

    async def delete_swap(self, offer_id: str) -> list[dict]:
        items = [x for x in await self.ensure_swaps() if x.get("id") != offer_id]
        await self.save_swaps(items)
        return items

    async def swap_vcoin(self, user_id: int, offer_id: str) -> tuple[bool, str, dict]:
        lock = self.redis.lock(f"mafia:lock:user:{user_id}", timeout=10, blocking_timeout=5)
        await lock.acquire()
        try:
            offer = await self.swap_offer(offer_id)
            stats = await self.get_stats(user_id)
            if not offer:
                return False, "missing", stats
            cost = int(offer.get("vcoin") or 0)
            gain = int(offer.get("money") or 0)
            if cost <= 0 or gain <= 0:
                return False, "missing", stats
            if int(stats.get("vcoin") or 0) < cost:
                return False, "broke", stats
            stats["vcoin"] = int(stats["vcoin"]) - cost
            stats["money"] = int(stats.get("money") or 0) + gain
            stats = await self.save_stats(user_id, stats)
            await self.add_econ_log(
                user_id,
                kind="swap",
                vcoin=-cost,
                money=gain,
                item=offer_id,
            )
            return True, "ok", stats
        finally:
            try:
                await lock.release()
            except Exception:
                pass

    async def stars_paid(self, charge_id: str) -> bool:
        if not charge_id:
            return True
        ok = await self.redis.set(
            f"mafia:pay:stars:{charge_id}", "1", nx=True, ex=60 * 60 * 24 * 40
        )
        return not bool(ok)

    async def ensure_gifts(self) -> list[dict]:
        raw = await self.redis.get("mafia:gifts")
        items: list[dict] = []
        if raw:
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, list):
                    items = [
                        x for x in loaded if isinstance(x, dict) and x.get("id")
                    ]
            except (TypeError, ValueError):
                items = []
        have = {str(x.get("id")) for x in items}
        changed = not items
        for default in DEFAULT_GIFTS:
            if default["id"] not in have:
                items.append(dict(default))
                changed = True
        if changed:
            await self.save_gifts(items)
        return items

    async def save_gifts(self, items: list[dict]) -> None:
        await self.redis.set("mafia:gifts", json.dumps(items, ensure_ascii=False))

    async def gift_item(self, gift_id: str) -> Optional[dict]:
        for item in await self.ensure_gifts():
            if item.get("id") == gift_id:
                return item
        return None

    async def upsert_gift(self, item: dict) -> list[dict]:
        items = await self.ensure_gifts()
        for i, old in enumerate(items):
            if old.get("id") == item["id"]:
                merged = dict(old)
                merged.update(item)
                if not str(merged.get("image") or "").strip():
                    merged["image"] = old.get("image") or ""
                items[i] = merged
                await self.save_gifts(items)
                return items
        items.append(dict(item))
        await self.save_gifts(items)
        return items

    async def delete_gift(self, gift_id: str) -> list[dict]:
        items = [x for x in await self.ensure_gifts() if x.get("id") != gift_id]
        await self.save_gifts(items)
        return items

    async def place_gift_order(self, user_id: int, gift_id: str) -> tuple[bool, str, dict]:
        gift = await self.gift_item(gift_id)
        stats = await self.get_stats(user_id)
        if not gift or not gift.get("enabled", True):
            return False, "missing", stats
        price = int(gift.get("vcoin") or 0)
        if price <= 0:
            return False, "no_price", stats
        pending = int(await self.redis.llen(f"mafia:gifts:pending:{user_id}") or 0)
        if pending >= 5:
            return False, "busy", stats
        if int(stats.get("vcoin") or 0) < price:
            return False, "broke", stats
        stats["vcoin"] = int(stats["vcoin"]) - price
        stats = await self.save_stats(user_id, stats)
        prof = await self.redis.hgetall(f"mafia:profile:{user_id}")
        order = {
            "id": secrets.token_hex(8),
            "user_id": int(user_id),
            "gift_id": gift_id,
            "title": gift.get("title_uz") or gift_id,
            "emoji": gift.get("emoji") or "🎁",
            "vcoin": price,
            "status": "new",
            "ts": _now(),
            "note": "",
            "name": stats.get("name") or str(user_id),
            "username": (prof or {}).get("username") or "",
        }
        raw = json.dumps(order, ensure_ascii=False)
        await self.redis.lpush("mafia:gifts:orders", raw)
        await self.redis.ltrim("mafia:gifts:orders", 0, 499)
        await self.redis.lpush(f"mafia:gifts:pending:{user_id}", order["id"])
        await self.redis.set(f"mafia:gifts:order:{order['id']}", raw)
        await self.add_econ_log(
            user_id,
            kind="gift_order",
            vcoin=-price,
            item=gift_id,
            order_id=order["id"],
        )
        return True, "ok", {**stats, "order": order}

    async def get_gift_order(self, order_id: str) -> Optional[dict]:
        raw = await self.redis.get(f"mafia:gifts:order:{order_id}")
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    async def list_gift_orders(self, limit: int = 80) -> list[dict]:
        rows = await self.redis.lrange("mafia:gifts:orders", 0, limit - 1)
        out = []
        for raw in rows:
            try:
                item = json.loads(raw)
            except (TypeError, ValueError):
                continue
            if not isinstance(item, dict):
                continue
            live = await self.get_gift_order(str(item.get("id") or ""))
            out.append(live or item)
        return out

    async def _rewrite_order_list(self, order: dict) -> None:
        rows = await self.redis.lrange("mafia:gifts:orders", 0, 499)
        new_rows = []
        for raw in rows:
            try:
                item = json.loads(raw)
            except (TypeError, ValueError):
                new_rows.append(raw)
                continue
            if isinstance(item, dict) and item.get("id") == order.get("id"):
                new_rows.append(json.dumps(order, ensure_ascii=False))
            else:
                new_rows.append(raw)
        pipe = self.redis.pipeline()
        pipe.delete("mafia:gifts:orders")
        if new_rows:
            pipe.rpush("mafia:gifts:orders", *new_rows)
        await pipe.execute()

    async def set_gift_order_status(
        self, order_id: str, status: str, note: str = ""
    ) -> Optional[dict]:
        order = await self.get_gift_order(order_id)
        if not order:
            return None
        prev = str(order.get("status") or "new")
        order["status"] = status
        if note:
            order["note"] = note[:200]
        raw = json.dumps(order, ensure_ascii=False)
        await self.redis.set(f"mafia:gifts:order:{order_id}", raw)
        await self._rewrite_order_list(order)
        uid = int(order.get("user_id") or 0)
        if uid and prev == "new" and status != "new":
            await self.redis.lrem(f"mafia:gifts:pending:{uid}", 1, order_id)
        if uid and prev == "new" and status == "cancel":
            price = int(order.get("vcoin") or 0)
            if price:
                stats = await self.get_stats(uid)
                stats["vcoin"] = int(stats.get("vcoin") or 0) + price
                await self.save_stats(uid, stats)
                await self.add_econ_log(
                    uid,
                    kind="gift_refund",
                    vcoin=price,
                    item=str(order.get("gift_id") or ""),
                    order_id=order_id,
                )
        if uid and status == "done":
            await self.add_econ_log(
                uid,
                kind="gift_done",
                item=str(order.get("gift_id") or ""),
                order_id=order_id,
            )
        return order

    async def create_session(self, payload: dict, ttl: int = 60 * 60 * 24 * 7) -> str:
        token = secrets.token_urlsafe(32)
        payload = dict(payload)
        payload["exp"] = _now() + ttl
        await self.redis.set(
            f"mafia:panel:sess:{token}",
            json.dumps(payload, ensure_ascii=False),
            ex=ttl,
        )
        return token

    async def get_session(self, token: str | None) -> Optional[dict]:
        if not token:
            return None
        raw = await self.redis.get(f"mafia:panel:sess:{token}")
        if not raw:
            return None
        data = json.loads(raw)
        if int(data.get("exp") or 0) < _now():
            await self.redis.delete(f"mafia:panel:sess:{token}")
            return None
        return data

    async def drop_session(self, token: str | None) -> None:
        if token:
            await self.redis.delete(f"mafia:panel:sess:{token}")

    async def save_ad(self, ad: dict) -> dict:
        if not ad.get("id"):
            ad["id"] = secrets.token_hex(6)
        ad.setdefault("created_at", _now())
        await self.redis.set(
            f"mafia:ad:{ad['id']}", json.dumps(ad, ensure_ascii=False), ex=60 * 60 * 24 * 30
        )
        await self.redis.zadd("mafia:ads", {ad["id"]: float(ad["created_at"])})
        return ad

    async def get_ad(self, ad_id: str) -> Optional[dict]:
        raw = await self.redis.get(f"mafia:ad:{ad_id}")
        return json.loads(raw) if raw else None

    async def list_ads(self, limit: int = 40) -> list[dict]:
        ids = await self.redis.zrevrange("mafia:ads", 0, limit - 1)
        out = []
        for ad_id in ids:
            ad = await self.get_ad(ad_id)
            if ad:
                out.append(ad)
        return out

    async def delete_ad(self, ad_id: str) -> None:
        await self.redis.delete(f"mafia:ad:{ad_id}")
        await self.redis.zrem("mafia:ads", ad_id)

    async def resolved_role(self, user_id: int) -> Optional[str]:
        from data import config

        allowed = {str(a).strip() for a in config.ADMINS if str(a).strip()}
        if str(user_id) in allowed:
            return "super"
        return await self.staff_role(user_id)

    async def set_staff_wait(self, admin_id: int, payload: dict, ttl: int = 300) -> None:
        await self.redis.set(
            f"mafia:staff:wait:{admin_id}",
            json.dumps(payload, ensure_ascii=False),
            ex=ttl,
        )

    async def get_staff_wait(self, admin_id: int) -> Optional[dict]:
        raw = await self.redis.get(f"mafia:staff:wait:{admin_id}")
        return json.loads(raw) if raw else None

    async def clear_staff_wait(self, admin_id: int) -> None:
        await self.redis.delete(f"mafia:staff:wait:{admin_id}")

    async def ensure_badges(self) -> list[dict]:
        raw = await self.redis.get("mafia:badges")
        if raw:
            try:
                items = json.loads(raw)
                if isinstance(items, list):
                    return [x for x in items if isinstance(x, dict) and x.get("id")]
            except (TypeError, ValueError):
                pass
        return []

    async def save_badges(self, items: list[dict]) -> None:
        await self.redis.set("mafia:badges", json.dumps(items, ensure_ascii=False))

    async def upsert_badge(self, badge: dict) -> list[dict]:
        row = {
            "id": str(badge.get("id") or "").strip().lower(),
            "emoji": str(badge.get("emoji") or "🏅")[:4],
            "title_uz": str(badge.get("title_uz") or "")[:40],
            "title_ru": str(badge.get("title_ru") or "")[:40],
            "title_en": str(badge.get("title_en") or "")[:40],
            "enabled": bool(badge.get("enabled", True)),
            "image": str(badge.get("image") or "")[:160],
            "ranks": _badge_ranks(badge.get("ranks")),
        }
        items = await self.ensure_badges()
        found = False
        for i, old in enumerate(items):
            if old.get("id") == row["id"]:
                items[i] = row
                found = True
                break
        if not found:
            items.append(row)
        await self.save_badges(items)
        return items

    async def delete_badge(self, badge_id: str) -> list[dict]:
        items = [x for x in await self.ensure_badges() if x.get("id") != badge_id]
        await self.save_badges(items)
        return items

    async def badge_by_id(self, badge_id: str) -> Optional[dict]:
        for item in await self.ensure_badges():
            if item.get("id") == badge_id and item.get("enabled", True):
                return item
        return None

    async def _badge_map(self, user_id: int) -> dict:
        raw = await self.redis.get(f"mafia:user:badges:{user_id}")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    async def _save_badge_map(self, user_id: int, data: dict) -> None:
        await self.redis.set(
            f"mafia:user:badges:{user_id}", json.dumps(data, ensure_ascii=False)
        )

    async def _shart_progress(self, user_id: int) -> dict:
        raw = await self.redis.get(f"mafia:shart:{user_id}")
        data: dict = {}
        if raw:
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    data = loaded
            except (TypeError, ValueError):
                data = {}
        data.setdefault("stars_money", 0)
        data.setdefault("stars_vcoin", 0)
        data.setdefault("buy", {})
        data.setdefault("roles", {})
        data.setdefault("chats", {})
        if not isinstance(data["buy"], dict):
            data["buy"] = {}
        if not isinstance(data["roles"], dict):
            data["roles"] = {}
        if not isinstance(data["chats"], dict):
            data["chats"] = {}
        return data

    async def _save_shart_progress(self, user_id: int, data: dict) -> None:
        await self.redis.set(
            f"mafia:shart:{user_id}", json.dumps(data, ensure_ascii=False)
        )

    async def _bump_stars(self, user_id: int, *, money: int = 0, vcoin: int = 0) -> None:
        data = await self._shart_progress(user_id)
        data["stars_money"] = int(data.get("stars_money") or 0) + max(0, int(money))
        data["stars_vcoin"] = int(data.get("stars_vcoin") or 0) + max(0, int(vcoin))
        await self._save_shart_progress(user_id, data)

    async def _bump_buy(self, user_id: int, field: str) -> None:
        if field not in SHOP_FIELDS:
            return
        data = await self._shart_progress(user_id)
        buy = dict(data.get("buy") or {})
        buy[field] = int(buy.get(field) or 0) + 1
        data["buy"] = buy
        await self._save_shart_progress(user_id, data)

    async def _bump_play(
        self,
        user_id: int,
        *,
        won: bool,
        chat_id: int | None = None,
        role: str | None = None,
    ) -> None:
        data = await self._shart_progress(user_id)
        code = str(role or "").strip()
        if code:
            roles = dict(data.get("roles") or {})
            row = dict(roles.get(code) or {})
            row["games"] = int(row.get("games") or 0) + 1
            if won:
                row["wins"] = int(row.get("wins") or 0) + 1
            else:
                row.setdefault("wins", int(row.get("wins") or 0))
            roles[code] = row
            data["roles"] = roles
        if chat_id is not None:
            chats = dict(data.get("chats") or {})
            key = str(int(chat_id))
            chats[key] = int(chats.get(key) or 0) + 1
            data["chats"] = chats
        await self._save_shart_progress(user_id, data)

    def _shart_met(self, stats: dict, progress: dict, row: dict) -> bool:
        kind = str(row.get("kind") or "")
        n = int(row.get("n") or 0)
        if kind not in SHART_KINDS:
            return False
        if kind == "groups":
            if n < 1 or int(row.get("groups") or 0) < 1:
                return False
        elif n < 1:
            return False
        role = str(row.get("role") or "").strip()
        if kind == "play":
            if role:
                return int((progress.get("roles") or {}).get(role, {}).get("games") or 0) >= n
            return int(stats.get("games") or 0) >= n
        if kind == "win":
            if role:
                return int((progress.get("roles") or {}).get(role, {}).get("wins") or 0) >= n
            return int(stats.get("wins") or 0) >= n
        if kind == "lose":
            if role:
                r = (progress.get("roles") or {}).get(role) or {}
                return int(r.get("games") or 0) - int(r.get("wins") or 0) >= n
            return int(stats.get("games") or 0) - int(stats.get("wins") or 0) >= n
        if kind == "buy":
            item = str(row.get("item") or "")
            if item not in SHOP_FIELDS:
                return False
            return int((progress.get("buy") or {}).get(item) or 0) >= n
        if kind == "toldirish":
            key = "stars_money" if str(row.get("currency") or "") == "money" else "stars_vcoin"
            return int(progress.get(key) or 0) >= n
        if kind == "groups":
            need = int(row.get("groups") or 0)
            chats = progress.get("chats") or {}
            hit = sum(1 for v in chats.values() if int(v or 0) >= n)
            return hit >= need
        return False

    async def evaluate_auto_shart(self, user_id: int) -> None:
        stats = await self.get_stats(user_id)
        progress = await self._shart_progress(user_id)
        for cat in await self.ensure_badges():
            if not cat.get("enabled", True):
                continue
            bid = str(cat.get("id") or "")
            if not bid:
                continue
            owned = await self.user_badge(user_id, bid)
            have = int(owned["rank"]) if owned else 0
            rows = sorted(
                [r for r in (cat.get("ranks") or []) if isinstance(r, dict)],
                key=lambda r: int(r.get("rank") or 0),
            )
            while True:
                nxt = next(
                    (r for r in rows if int(r.get("rank") or 0) == have + 1),
                    None,
                )
                if not nxt or not str(nxt.get("kind") or ""):
                    break
                if not self._shart_met(stats, progress, nxt):
                    break
                await self._set_badge_rank(user_id, bid, have + 1)
                have += 1

    async def user_badge(self, user_id: int, badge_id: str) -> Optional[dict]:
        row = self._badge_map_row(await self._badge_map(user_id), badge_id)
        return row

    def _badge_map_row(self, data: dict, badge_id: str) -> Optional[dict]:
        row = data.get(badge_id)
        if not isinstance(row, dict):
            return None
        if int(row.get("rank") or 0) < 1:
            return None
        return row

    async def _set_badge_rank(self, user_id: int, badge_id: str, rank: int) -> dict:
        data = await self._badge_map(user_id)
        row = dict(data.get(badge_id) or {})
        got = dict(row.get("got") or {})
        have = int(row.get("rank") or 0)
        target = max(have, int(rank))
        now = _now()
        for step in range(1, target + 1):
            key = str(step)
            if key not in got:
                got[key] = now
        row["rank"] = target
        row["got"] = got
        data[badge_id] = row
        await self._save_badge_map(user_id, data)
        return row

    async def next_shop_badge(self, user_id: int, badge_id: str) -> Optional[dict]:
        cat = await self.badge_by_id(badge_id)
        if not cat:
            return None
        owned = await self.user_badge(user_id, badge_id)
        have = int(owned["rank"]) if owned else 0
        want = have + 1
        for row in cat.get("ranks") or []:
            if int(row.get("rank") or 0) != want:
                continue
            if int(row.get("vcoin_cost") or 0) <= 0:
                return None
            return row
        return None

    async def listed_shop_badges(self, user_id: int, lang: str = "uz") -> list[dict]:
        out: list[dict] = []
        for cat in await self.ensure_badges():
            if not cat.get("enabled", True):
                continue
            bid = str(cat.get("id") or "")
            nxt = await self.next_shop_badge(user_id, bid)
            if not nxt:
                continue
            out.append(
                {
                    "id": bid,
                    "emoji": cat.get("emoji") or "🏅",
                    "title": _loc(cat, "title", lang) or bid,
                    "desc": _loc(nxt, "shart", lang),
                    "vcoin": int(nxt.get("vcoin_cost") or 0),
                    "rank": int(nxt.get("rank") or 0),
                    "image": catalog_image(cat),
                }
            )
        return out

    async def buy_badge(self, user_id: int, badge_id: str) -> tuple[bool, str, dict]:
        nxt = await self.next_shop_badge(user_id, badge_id)
        stats = await self.get_stats(user_id)
        if not nxt:
            return False, "missing", stats
        cost = int(nxt.get("vcoin_cost") or 0)
        if int(stats.get("vcoin") or 0) < cost:
            return False, "broke", stats
        stats["vcoin"] = int(stats["vcoin"]) - cost
        stats = await self.save_stats(user_id, stats)
        await self._set_badge_rank(user_id, badge_id, int(nxt["rank"]))
        await self.add_econ_log(
            user_id, kind="badge", vcoin=-cost, item=f"{badge_id}:{nxt['rank']}"
        )
        return True, "ok", stats

    async def grant_badge(
        self, user_id: int, badge_id: str, rank: int
    ) -> tuple[bool, str, dict]:
        cat = await self.badge_by_id(badge_id)
        stats = await self.get_stats(user_id)
        rank = int(rank)
        if not cat or rank < 1:
            return False, "missing", stats
        ranks = [int(r.get("rank") or 0) for r in cat.get("ranks") or []]
        if ranks and rank not in ranks:
            return False, "missing", stats
        await self._set_badge_rank(user_id, badge_id, rank)
        return True, "ok", await self.get_stats(user_id)

    async def owned_badges(self, user_id: int, lang: str = "uz") -> list[dict]:
        catalog = {
            str(x.get("id")): x
            for x in await self.ensure_badges()
            if x.get("enabled", True)
        }
        data = await self._badge_map(user_id)
        out: list[dict] = []
        for bid, row in data.items():
            cat = catalog.get(str(bid))
            owned = self._badge_map_row({bid: row}, bid)
            if not cat or not owned:
                continue
            rank = int(owned["rank"])
            shart = ""
            for r in cat.get("ranks") or []:
                if int(r.get("rank") or 0) == rank:
                    shart = _loc(r, "shart", lang)
                    break
            got = dict(owned.get("got") or {})
            title = _loc(cat, "title", lang) or bid
            out.append(
                {
                    "id": bid,
                    "rank": rank,
                    "emoji": cat.get("emoji") or "🏅",
                    "title": title,
                    "title_uz": cat.get("title_uz") or bid,
                    "title_ru": cat.get("title_ru") or "",
                    "title_en": cat.get("title_en") or "",
                    "image": catalog_image(cat),
                    "shart": shart,
                    "at": int(got.get(str(rank)) or 0),
                }
            )
        return out

    def _gmod_key(self, chat_id: int) -> str:
        return f"mafia:gmod:{chat_id}"

    async def group_penalty(self, chat_id: int, user_id: int) -> dict:
        raw = await self.redis.hget(self._gmod_key(chat_id), str(user_id))
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    async def _save_group_penalty(self, chat_id: int, user_id: int, data: dict) -> None:
        key = self._gmod_key(chat_id)
        if not data.get("mute") and not data.get("ban"):
            await self.redis.hdel(key, str(user_id))
            return
        await self.redis.hset(key, mapping={str(user_id): json.dumps(data)})

    async def set_admin_mute(self, chat_id: int, user_id: int, until_ts: int) -> None:
        row = await self.group_penalty(chat_id, user_id)
        row["mute"] = int(until_ts)
        await self._save_group_penalty(chat_id, user_id, row)

    async def clear_admin_mute(self, chat_id: int, user_id: int) -> None:
        row = await self.group_penalty(chat_id, user_id)
        row.pop("mute", None)
        await self._save_group_penalty(chat_id, user_id, row)

    async def set_admin_ban(self, chat_id: int, user_id: int, until_ts: int) -> None:
        row = await self.group_penalty(chat_id, user_id)
        row["ban"] = int(until_ts)
        await self._save_group_penalty(chat_id, user_id, row)

    async def clear_admin_ban(self, chat_id: int, user_id: int) -> None:
        row = await self.group_penalty(chat_id, user_id)
        row.pop("ban", None)
        await self._save_group_penalty(chat_id, user_id, row)

    async def admin_muted_ids(self, chat_id: int) -> set[int]:
        now = _now()
        raw = await self.redis.hgetall(self._gmod_key(chat_id))
        out: set[int] = set()
        for uid, blob in (raw or {}).items():
            try:
                data = json.loads(blob)
            except (TypeError, ValueError):
                continue
            if int(data.get("mute") or 0) > now:
                out.add(int(uid))
        return out

    async def is_admin_muted(self, chat_id: int, user_id: int) -> bool:
        row = await self.group_penalty(chat_id, user_id)
        return int(row.get("mute") or 0) > _now()

    async def is_game_banned(self, chat_id: int, user_id: int) -> bool:
        row = await self.group_penalty(chat_id, user_id)
        return int(row.get("ban") or 0) > _now()
