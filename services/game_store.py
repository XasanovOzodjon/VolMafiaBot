from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from redis.asyncio import Redis

from game.models import Game, Phase
from services.admin_data import AdminData

GAME_TTL = 60 * 60 * 24


class GameStore(AdminData):
    def __init__(self, redis: Redis):
        self.redis = redis

    def _game_key(self, chat_id: int) -> str:
        return f"mafia:game:{chat_id}"

    def _user_key(self, user_id: int) -> str:
        return f"mafia:user:{user_id}"

    def _lock_key(self, chat_id: int) -> str:
        return f"mafia:lock:{chat_id}"

    async def get(self, chat_id: int) -> Optional[Game]:
        raw = await self.redis.get(self._game_key(chat_id))
        if not raw:
            return None
        return Game.from_dict(json.loads(raw))

    async def save(self, game: Game) -> None:
        await self.redis.set(
            self._game_key(game.chat_id),
            json.dumps(game.to_dict(), ensure_ascii=False),
            ex=GAME_TTL,
        )
        if game.deleted or game.phase == Phase.ENDED:
            await self.unmark_live(game.chat_id)
        else:
            await self.mark_live(game.chat_id)

    async def delete(self, chat_id: int) -> None:
        game = await self.get(chat_id)
        if game:
            for uid in list(game.players):
                await self.unbind_user(uid, chat_id)
        await self.redis.delete(self._game_key(chat_id))
        await self.unmark_live(chat_id)

    async def bind_user(self, user_id: int, chat_id: int) -> None:
        await self.redis.set(self._user_key(user_id), str(chat_id), ex=GAME_TTL)

    async def unbind_user(self, user_id: int, chat_id: Optional[int] = None) -> None:
        if chat_id is not None:
            current = await self.chat_of_user(user_id)
            if current != chat_id:
                return
        await self.redis.delete(self._user_key(user_id))

    async def chat_of_user(self, user_id: int) -> Optional[int]:
        raw = await self.redis.get(self._user_key(user_id))
        return int(raw) if raw else None

    def _user_lang_key(self, user_id: int) -> str:
        return f"mafia:lang:user:{user_id}"

    def _known_lang(self, lang: str | None) -> str:
        from i18n.langs import is_known

        code = (lang or "").lower()
        return code if is_known(code) else "uz"

    async def get_user_lang(self, user_id: int) -> str:
        raw = await self.redis.get(self._user_lang_key(user_id))
        return self._known_lang(raw)

    async def user_has_lang(self, user_id: int) -> bool:
        from i18n.langs import is_known

        raw = await self.redis.get(self._user_lang_key(user_id))
        return bool(raw) and is_known(raw)

    async def set_user_lang(self, user_id: int, lang: str) -> None:
        lang = self._known_lang(lang)
        await self.redis.set(self._user_lang_key(user_id), lang)

    async def assign_user_lang_once(self, user_id: int, lang: str) -> bool:
        lang = self._known_lang(lang)
        return bool(await self.redis.set(self._user_lang_key(user_id), lang, nx=True))

    async def ensure_user_lang_from_chat(self, user_id: int, chat_id: int) -> str:
        if not await self.user_has_lang(user_id):
            from i18n.langs import public_codes

            chat_lang = await self.get_chat_lang(chat_id)
            if chat_lang in public_codes():
                await self.assign_user_lang_once(user_id, chat_lang)
        return await self.get_user_lang(user_id)

    async def get_chat_lang(self, chat_id: int) -> str:
        settings = await self.get_chat_settings(chat_id)
        return settings["lang"]

    async def set_chat_lang(self, chat_id: int, lang: str) -> None:
        await self.update_chat_settings(chat_id, lang=lang)

    def _settings_key(self, chat_id: int) -> str:
        return f"mafia:settings:chat:{chat_id}"

    async def get_chat_settings(self, chat_id: int) -> dict:
        raw = await self.redis.get(self._settings_key(chat_id))
        data: dict = {}
        if raw:
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                data = {}
        lang = data.get("lang")
        if not lang:
            lang = await self.redis.get(f"mafia:lang:chat:{chat_id}")
        lang = self._known_lang(lang)
        auto_start = data.get("auto_start")
        if auto_start is None:
            auto_start = True
        return {
            "lang": lang,
            "auto_start": bool(auto_start),
        }

    async def update_chat_settings(self, chat_id: int, **fields) -> dict:
        settings = await self.get_chat_settings(chat_id)
        if "lang" in fields:
            settings["lang"] = self._known_lang(fields["lang"])
        if "auto_start" in fields:
            settings["auto_start"] = bool(fields["auto_start"])
        await self.redis.set(
            self._settings_key(chat_id),
            json.dumps(settings, ensure_ascii=False),
        )
        await self.redis.set(f"mafia:lang:chat:{chat_id}", settings["lang"])
        game = await self.get(chat_id)
        if game:
            game.lang = settings["lang"]
            await self.save(game)
        return settings

    async def add_stats(
        self,
        user_id: int,
        won: bool,
        money: int = 0,
        name: str = "",
        chat_id: int | None = None,
        role: str | None = None,
    ) -> dict:
        stats = await self.get_stats(user_id)
        stats["games"] += 1
        if won:
            stats["wins"] += 1
        money = int(money or 0)
        stats["money"] += money
        if name:
            stats["name"] = name
        stats = await self.save_stats(user_id, stats)
        await self.redis.sadd("mafia:players", str(user_id))
        if chat_id is not None:
            await self.redis.zincrby(
                f"mafia:rank:chat:{chat_id}", money, str(user_id)
            )
        if money:
            await self.add_econ_log(
                user_id,
                kind="game_money",
                money=money,
                chat_id=chat_id,
                won=won,
            )
        await self._bump_play(user_id, won=won, chat_id=chat_id, role=role)
        await self.evaluate_auto_shart(user_id)
        return stats

    async def record_finished_game(self, game, winner: str | None) -> list[tuple]:
        from game.rewards import human_results

        results: list[tuple] = []
        total_money = 0
        for player, money, won in human_results(game, winner):
            stats = await self.add_stats(
                player.user_id,
                won,
                money=money,
                name=player.full_name,
                chat_id=game.chat_id,
                role=player.role,
            )
            results.append((player, money, won, stats))
            total_money += money
        group = await self.get_group_stats(game.chat_id)
        group["games"] += 1
        if winner in ("town", "mafia", "manyak"):
            group[winner] += 1
        group["money"] += total_money
        await self.redis.set(
            f"mafia:stats:chat:{game.chat_id}",
            json.dumps(group, ensure_ascii=False),
        )
        glob = await self.get_global_stats()
        glob["games"] += 1
        glob["money"] += total_money
        await self.redis.set(
            "mafia:stats:global",
            json.dumps({"games": glob["games"], "money": glob["money"]}),
        )
        await self.bump_metric("games", 1)
        if total_money:
            await self.bump_metric("money", total_money)
        await self.redis.hset(
            f"mafia:group:{game.chat_id}",
            mapping={"last_game": str(int(__import__("time").time()))},
        )
        return results

    async def get_global_stats(self) -> dict:
        raw = await self.redis.get("mafia:stats:global")
        data = json.loads(raw) if raw else {}
        players = await self.redis.scard("mafia:players")
        return {
            "games": int(data.get("games", 0)),
            "money": int(data.get("money", 0)),
            "players": int(players or 0),
        }

    async def get_group_stats(self, chat_id: int) -> dict:
        raw = await self.redis.get(f"mafia:stats:chat:{chat_id}")
        data = json.loads(raw) if raw else {}
        return {
            "games": int(data.get("games", 0)),
            "town": int(data.get("town", 0)),
            "mafia": int(data.get("mafia", 0)),
            "manyak": int(data.get("manyak", 0)),
            "money": int(data.get("money", 0)),
        }

    async def get_rank(self, user_id: int, chat_id: int | None = None) -> int | None:
        key = f"mafia:rank:chat:{chat_id}" if chat_id else "mafia:rank:global"
        rank = await self.redis.zrevrank(key, str(user_id))
        if rank is None:
            return None
        return int(rank) + 1

    async def get_score(self, user_id: int, chat_id: int | None = None) -> int:
        key = f"mafia:rank:chat:{chat_id}" if chat_id else "mafia:rank:global"
        score = await self.redis.zscore(key, str(user_id))
        if score is None:
            return 0
        return int(score)

    async def get_leaderboard(
        self, *, chat_id: int | None = None, limit: int = 10
    ) -> list[tuple[int, str, int]]:
        key = f"mafia:rank:chat:{chat_id}" if chat_id else "mafia:rank:global"
        rows = await self.redis.zrevrange(key, 0, limit - 1, withscores=True)
        if not rows:
            return []
        ids = [int(uid) for uid, _score in rows]
        names = await self.redis.mget([f"mafia:uname:{uid}" for uid in ids])
        result: list[tuple[int, str, int]] = []
        for i, uid in enumerate(ids):
            name = names[i] if names else None
            if not name:
                stats = await self.get_stats(uid)
                name = stats.get("name") or str(uid)
            score = int(rows[i][1])
            result.append((uid, str(name), score))
        return result

    def _gif_key(self, kind: str) -> str:
        return f"mafia:gif:{kind}"

    async def get_gif(self, kind: str) -> Optional[str]:
        raw = await self.redis.get(self._gif_key(kind))
        return raw or None

    async def set_gif(self, kind: str, file_id: str) -> None:
        await self.redis.set(self._gif_key(kind), file_id)

    async def set_await_gif(self, user_id: int, kind: str) -> None:
        await self.redis.set(f"mafia:await_gif:{user_id}", kind, ex=300)

    async def get_await_gif(self, user_id: int) -> Optional[str]:
        raw = await self.redis.get(f"mafia:await_gif:{user_id}")
        return raw or None

    async def clear_await_gif(self, user_id: int) -> None:
        await self.redis.delete(f"mafia:await_gif:{user_id}")

    @asynccontextmanager
    async def lock_only(self, chat_id: int) -> AsyncIterator[None]:
        lock = self.redis.lock(self._lock_key(chat_id), timeout=20, blocking_timeout=8)
        await lock.acquire()
        try:
            yield
        finally:
            try:
                await lock.release()
            except Exception:
                pass

    @asynccontextmanager
    async def locked(self, chat_id: int) -> AsyncIterator[Optional[Game]]:
        async with self.lock_only(chat_id):
            game = await self.get(chat_id)
            try:
                yield game
            finally:
                if game is not None:
                    if game.deleted:
                        await self.delete(chat_id)
                    else:
                        await self.save(game)
