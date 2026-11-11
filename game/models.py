from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from game.roles import Role


class Phase:
    REGISTRATION = "registration"
    TEST_SETUP = "test_setup"
    NIGHT = "night"
    DAY = "day"
    VOTE = "vote"
    CONFIRM = "confirm"
    LYNCH_WAIT = "lynch_wait"
    YAKUDZA = "yakudza"
    ENDED = "ended"


@dataclass
class Player:
    user_id: int
    full_name: str
    username: Optional[str] = None
    role: Optional[str] = None
    alive: bool = True
    is_host: bool = False
    join_order: int = 0
    dm_ok: bool = True
    acted_this_cycle: bool = False
    idle_rounds: int = 0
    is_bot: bool = False
    shop_protection: bool = False
    shop_protection_used: bool = False
    shop_documents: bool = False
    shop_documents_used: bool = False
    shop_active_role: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "username": self.username,
            "role": self.role,
            "alive": self.alive,
            "is_host": self.is_host,
            "join_order": self.join_order,
            "dm_ok": self.dm_ok,
            "acted_this_cycle": self.acted_this_cycle,
            "idle_rounds": self.idle_rounds,
            "is_bot": self.is_bot,
            "shop_protection": bool(self.shop_protection),
            "shop_protection_used": bool(self.shop_protection_used),
            "shop_documents": bool(self.shop_documents),
            "shop_documents_used": bool(self.shop_documents_used),
            "shop_active_role": bool(self.shop_active_role),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Player:
        return cls(
            user_id=int(data["user_id"]),
            full_name=data["full_name"],
            username=data.get("username"),
            role=data.get("role"),
            alive=bool(data.get("alive", True)),
            is_host=bool(data.get("is_host", False)),
            join_order=int(data.get("join_order", 0)),
            dm_ok=bool(data.get("dm_ok", True)),
            acted_this_cycle=bool(data.get("acted_this_cycle", False)),
            idle_rounds=int(data.get("idle_rounds", 0)),
            is_bot=bool(data.get("is_bot", False)),
            shop_protection=bool(data.get("shop_protection", False)),
            shop_protection_used=bool(data.get("shop_protection_used", False)),
            shop_documents=bool(data.get("shop_documents", False)),
            shop_documents_used=bool(data.get("shop_documents_used", False)),
            shop_active_role=bool(data.get("shop_active_role", False)),
        )

    @property
    def role_enum(self) -> Optional[Role]:
        return Role(self.role) if self.role else None


@dataclass
class Game:
    chat_id: int
    host_id: int
    phase: str = Phase.REGISTRATION
    night_number: int = 0
    players: dict[int, Player] = field(default_factory=dict)
    night_actions: dict[int, dict[str, Any]] = field(default_factory=dict)
    votes: dict[int, Any] = field(default_factory=dict)
    confirm_votes: dict[int, bool] = field(default_factory=dict)
    nominated_id: Optional[int] = None
    doctor_last_target: Optional[int] = None
    no_vote_user_id: Optional[int] = None
    sheriff_user_id: Optional[int] = None
    status_message_id: Optional[int] = None
    saved_permissions: Optional[dict[str, Any]] = None
    yakudza_pending_id: Optional[int] = None
    yakudza_kill_id: Optional[int] = None
    after_yakudza: Optional[str] = None
    last_report: Optional[str] = None
    winner: Optional[str] = None
    lang: str = "uz"
    deleted: bool = False
    night_flavor_sent: list[str] = field(default_factory=list)
    started_at: Optional[float] = None
    test_mode: bool = False
    test_size: int = 0
    pending_lynch: Optional[dict[str, Any]] = None
    pending_new_don_id: Optional[int] = None
    yakudza_bounty_ids: list[int] = field(default_factory=list)
    boosts_ok: bool = True
    shop_protect_announce: bool = False
    vote_round_id: int = 0
    vote_session_active: bool = False
    skip_used_at_low_players: bool = False
    yakudza_choice_mode: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "host_id": self.host_id,
            "phase": self.phase,
            "night_number": self.night_number,
            "players": {str(k): v.to_dict() for k, v in self.players.items()},
            "night_actions": {str(k): v for k, v in self.night_actions.items()},
            "votes": {str(k): v for k, v in self.votes.items()},
            "confirm_votes": {str(k): v for k, v in self.confirm_votes.items()},
            "nominated_id": self.nominated_id,
            "doctor_last_target": self.doctor_last_target,
            "no_vote_user_id": self.no_vote_user_id,
            "sheriff_user_id": self.sheriff_user_id,
            "status_message_id": self.status_message_id,
            "saved_permissions": self.saved_permissions,
            "yakudza_pending_id": self.yakudza_pending_id,
            "yakudza_kill_id": self.yakudza_kill_id,
            "after_yakudza": self.after_yakudza,
            "last_report": self.last_report,
            "winner": self.winner,
            "lang": self.lang or "uz",
            "deleted": bool(self.deleted),
            "night_flavor_sent": list(self.night_flavor_sent or []),
            "started_at": self.started_at,
            "test_mode": bool(self.test_mode),
            "test_size": int(self.test_size or 0),
            "pending_lynch": self.pending_lynch,
            "pending_new_don_id": self.pending_new_don_id,
            "yakudza_bounty_ids": list(self.yakudza_bounty_ids or []),
            "boosts_ok": bool(self.boosts_ok),
            "shop_protect_announce": bool(self.shop_protect_announce),
            "vote_round_id": int(self.vote_round_id or 0),
            "vote_session_active": bool(self.vote_session_active),
            "skip_used_at_low_players": bool(self.skip_used_at_low_players),
            "yakudza_choice_mode": bool(self.yakudza_choice_mode),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Game:
        players = {
            int(k): Player.from_dict(v) for k, v in data.get("players", {}).items()
        }
        return cls(
            chat_id=int(data["chat_id"]),
            host_id=int(data["host_id"]),
            phase=data.get("phase", Phase.REGISTRATION),
            night_number=int(data.get("night_number", 0)),
            players=players,
            night_actions={int(k): v for k, v in data.get("night_actions", {}).items()},
            votes={int(k): v for k, v in data.get("votes", {}).items()},
            confirm_votes={
                int(k): bool(v) for k, v in data.get("confirm_votes", {}).items()
            },
            nominated_id=_opt_int(data.get("nominated_id")),
            doctor_last_target=_opt_int(data.get("doctor_last_target")),
            no_vote_user_id=_opt_int(data.get("no_vote_user_id")),
            sheriff_user_id=_opt_int(data.get("sheriff_user_id")),
            status_message_id=_opt_int(data.get("status_message_id")),
            saved_permissions=data.get("saved_permissions"),
            yakudza_pending_id=_opt_int(data.get("yakudza_pending_id")),
            yakudza_kill_id=_opt_int(data.get("yakudza_kill_id")),
            after_yakudza=data.get("after_yakudza"),
            last_report=data.get("last_report"),
            winner=data.get("winner"),
            lang=data.get("lang") or "uz",
            deleted=bool(data.get("deleted", False)),
            night_flavor_sent=list(data.get("night_flavor_sent") or []),
            started_at=_opt_float(data.get("started_at")),
            test_mode=bool(data.get("test_mode", False)),
            test_size=int(data.get("test_size") or 0),
            pending_lynch=data.get("pending_lynch"),
            pending_new_don_id=_opt_int(data.get("pending_new_don_id")),
            yakudza_bounty_ids=[
                int(x) for x in (data.get("yakudza_bounty_ids") or [])
            ],
            boosts_ok=bool(data.get("boosts_ok", True)),
            shop_protect_announce=bool(data.get("shop_protect_announce", False)),
            vote_round_id=int(data.get("vote_round_id") or 0),
            vote_session_active=bool(data.get("vote_session_active", False)),
            skip_used_at_low_players=bool(data.get("skip_used_at_low_players", False)),
            yakudza_choice_mode=bool(data.get("yakudza_choice_mode", False)),
        )

    def alive(self) -> list[Player]:
        return sorted(
            (p for p in self.players.values() if p.alive),
            key=lambda p: p.join_order,
        )

    def dead(self) -> list[Player]:
        return [p for p in self.players.values() if not p.alive]

    def joined(self) -> list[Player]:
        return sorted(self.players.values(), key=lambda p: p.join_order)

    def get(self, user_id: int) -> Optional[Player]:
        return self.players.get(user_id)

    def by_role(self, role: Role, alive_only: bool = True) -> Optional[Player]:
        for p in self.players.values():
            if p.role == role.value and (p.alive or not alive_only):
                return p
        return None

    def mafia(self, alive_only: bool = True) -> list[Player]:
        result = []
        for p in self.players.values():
            if p.role in (Role.MAFIYA.value, Role.KROSNIY_OTETS.value):
                if p.alive or not alive_only:
                    result.append(p)
        return sorted(result, key=lambda p: p.join_order)

    def acting_sheriff(self) -> Optional[Player]:
        if self.sheriff_user_id:
            p = self.players.get(self.sheriff_user_id)
            if p and p.alive:
                return p
        return None

    def bots(self, alive_only: bool = True) -> list[Player]:
        result = [
            p
            for p in self.players.values()
            if p.is_bot and (p.alive or not alive_only)
        ]
        return sorted(result, key=lambda p: p.join_order)

    def humans(self, alive_only: bool = True) -> list[Player]:
        result = [
            p
            for p in self.players.values()
            if not p.is_bot and (p.alive or not alive_only)
        ]
        return sorted(result, key=lambda p: p.join_order)


def _opt_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    return int(value)


def _opt_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)
