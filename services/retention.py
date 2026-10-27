from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from services.game_store import GameStore

STREAK_REWARDS = {
    1: {"money": 20, "vcoin": 0, "protection": 0},
    2: {"money": 35, "vcoin": 0, "protection": 0},
    3: {"money": 50, "vcoin": 1, "protection": 0},
    4: {"money": 75, "vcoin": 0, "protection": 0},
    5: {"money": 100, "vcoin": 2, "protection": 0},
    6: {"money": 140, "vcoin": 3, "protection": 0},
    7: {"money": 200, "vcoin": 5, "protection": 1},
}

LUCKY_PRIZES = [
    {"type": "money", "min": 80, "max": 150, "weight": 35, "label": "Kichik pul mukofoti"},
    {"type": "money", "min": 150, "max": 300, "weight": 25, "label": "O'rtacha pul mukofoti"},
    {"type": "vcoin", "min": 8, "max": 15, "weight": 15, "label": "Vcoin paketi"},
    {"type": "protection", "count": 1, "weight": 12, "label": "Ximoya (🛡️)"},
    {"type": "documents", "count": 1, "weight": 8, "label": "Hujjatlar (📁)"},
    {"type": "active_role", "count": 1, "weight": 3, "label": "Faol rol (🎎)"},
    {"type": "jackpot_vcoin", "count": 50, "weight": 2, "label": "🌟 JEKPOT: 50 Vcoin!"},
]


class RetentionService:
    @staticmethod
    def is_user_vip(stats: dict) -> bool:
        until = int(stats.get("vip_until") or 0)
        return until > int(time.time())

    @staticmethod
    async def claim_daily_bonus(store: GameStore, user_id: int) -> tuple[bool, str, dict]:
        now = int(time.time())
        day_seconds = 86400
        stats = await store.get_stats(user_id)
        last_claim = int(stats.get("last_daily_ts") or 0)
        streak = int(stats.get("daily_streak") or 0)

        elapsed = now - last_claim
        if elapsed < day_seconds and last_claim > 0:
            remaining = day_seconds - elapsed
            hours = remaining // 3600
            mins = (remaining % 3600) // 60
            return False, f"wait_{hours}_{mins}", {}

        if elapsed > (day_seconds * 2):
            streak = 1
        else:
            streak = (streak % 7) + 1

        reward = dict(STREAK_REWARDS.get(streak, STREAK_REWARDS[1]))
        vip = RetentionService.is_user_vip(stats)
        if vip:
            reward["money"] = reward["money"] * 2
            if reward["vcoin"] > 0:
                reward["vcoin"] = reward["vcoin"] * 2

        stats["daily_streak"] = streak
        stats["last_daily_ts"] = now
        stats["money"] = int(stats.get("money") or 0) + reward["money"]
        if reward["vcoin"] > 0:
            stats["vcoin"] = int(stats.get("vcoin") or 0) + reward["vcoin"]
        if reward.get("protection", 0) > 0:
            stats["protection"] = int(stats.get("protection") or 0) + reward["protection"]

        await store.save_stats(user_id, stats)
        await store.add_econ_log(
            user_id,
            kind="daily_bonus",
            money=reward["money"],
            vcoin=reward["vcoin"] or None,
            detail=f"streak_{streak}_vip_{vip}",
        )
        return True, "ok", {"reward": reward, "streak": streak, "vip": vip}

    @staticmethod
    async def bind_referral(store: GameStore, user_id: int, referrer_id: int) -> bool:
        if user_id == referrer_id:
            return False
        stats = await store.get_stats(user_id)
        if stats.get("ref_by") or stats.get("games", 0) > 0:
            return False
        stats["ref_by"] = referrer_id
        # Yangi kelgan do'stga xush kelibsiz bonusi
        stats["money"] = int(stats.get("money") or 0) + 25
        await store.save_stats(user_id, stats)
        await store.add_econ_log(user_id, kind="ref_welcome", money=25, detail=f"by_{referrer_id}")

        ref_stats = await store.get_stats(referrer_id)
        ref_stats["ref_count"] = int(ref_stats.get("ref_count") or 0) + 1
        await store.save_stats(referrer_id, ref_stats)
        return True

    @staticmethod
    async def reward_referrer_if_eligible(store: GameStore, user_id: int) -> tuple[int | None, dict]:
        stats = await store.get_stats(user_id)
        ref_by = int(stats.get("ref_by") or 0)
        if not ref_by:
            return None, {}
        # Faqat 1-o'yin uchun mukofot
        if stats.get("ref_rewarded"):
            return None, {}
        stats["ref_rewarded"] = True
        await store.save_stats(user_id, stats)

        ref_stats = await store.get_stats(ref_by)
        ref_stats["money"] = int(ref_stats.get("money") or 0) + 40
        ref_stats["vcoin"] = int(ref_stats.get("vcoin") or 0) + 2
        ref_stats["ref_earnings"] = int(ref_stats.get("ref_earnings") or 0) + 40
        await store.save_stats(ref_by, ref_stats)
        await store.add_econ_log(
            ref_by,
            kind="ref_played",
            money=40,
            vcoin=2,
            detail=f"player_{user_id}",
        )
        return ref_by, {"money": 40, "vcoin": 2}

    @staticmethod
    async def open_lucky_box(store: GameStore, user_id: int) -> tuple[bool, str, dict]:
        cost = 10
        stats = await store.get_stats(user_id)
        vcoin = int(stats.get("vcoin") or 0)
        if vcoin < cost:
            return False, "broke", {}

        stats["vcoin"] = vcoin - cost
        stats["boxes_opened"] = int(stats.get("boxes_opened") or 0) + 1

        # Tanlov
        weights = [p["weight"] for p in LUCKY_PRIZES]
        chosen = random.choices(LUCKY_PRIZES, weights=weights, k=1)[0]
        ptype = chosen["type"]
        won_data: dict[str, Any] = {"type": ptype, "label": chosen["label"]}

        if ptype == "money":
            amount = random.randint(chosen["min"], chosen["max"])
            stats["money"] = int(stats.get("money") or 0) + amount
            won_data["amount"] = amount
            won_data["text"] = f"{amount} $"
        elif ptype == "vcoin":
            amount = random.randint(chosen["min"], chosen["max"])
            stats["vcoin"] = int(stats.get("vcoin") or 0) + amount
            won_data["amount"] = amount
            won_data["text"] = f"{amount} Vcoin"
        elif ptype in ("protection", "documents", "active_role"):
            count = chosen["count"]
            stats[ptype] = int(stats.get(ptype) or 0) + count
            won_data["count"] = count
            won_data["text"] = f"{count} ta {chosen['label']}"
        elif ptype == "jackpot_vcoin":
            count = chosen["count"]
            stats["vcoin"] = int(stats.get("vcoin") or 0) + count
            won_data["amount"] = count
            won_data["text"] = f"{count} Vcoin (JEKPOT!)"

        await store.save_stats(user_id, stats)
        await store.add_econ_log(
            user_id,
            kind="lucky_box",
            vcoin=-cost,
            detail=f"won_{ptype}",
        )
        return True, "ok", won_data
