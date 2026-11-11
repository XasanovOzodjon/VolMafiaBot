from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from game.models import Game, Player
from game.roles import vote_ally_prefix
from i18n import t


def registration_kb(
    lang: str = "uz",
    bot_username: str | None = None,
    chat_id: int | None = None,
) -> InlineKeyboardMarkup:
    if bot_username and chat_id is not None:
        join_btn = InlineKeyboardButton(
            t("btn_join", lang),
            url=f"https://t.me/{bot_username}?start=j{chat_id}",
        )
    else:
        join_btn = InlineKeyboardButton(t("btn_join", lang), callback_data="g:join")
    return InlineKeyboardMarkup([[join_btn]])


def view_role_kb(
    lang: str = "uz",
    bot_username: str | None = None,
    chat_id: int | None = None,
) -> InlineKeyboardMarkup:
    if bot_username:
        btn = InlineKeyboardButton(
            t("btn_view_role", lang),
            url=f"https://t.me/{bot_username}",
        )
    else:
        btn = InlineKeyboardButton(t("btn_view_role", lang), url="https://t.me")
    return InlineKeyboardMarkup([[btn]])


def open_bot_kb(
    lang: str = "uz",
    bot_username: str | None = None,
) -> InlineKeyboardMarkup:
    url = f"https://t.me/{bot_username}" if bot_username else "https://t.me"
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("btn_open_bot", lang), url=url)]]
    )


def vote_open_kb(
    lang: str = "uz",
    bot_username: str | None = None,
    chat_id: int | None = None,
) -> InlineKeyboardMarkup:
    if bot_username and chat_id is not None:
        btn = InlineKeyboardButton(
            t("btn_vote", lang),
            url=f"https://t.me/{bot_username}",
        )
    else:
        btn = InlineKeyboardButton(t("btn_vote", lang), callback_data="g:vote")
    return InlineKeyboardMarkup([[btn]])


def _player_rows(
    players: list[Player],
    prefix: str,
    exclude_ids: set[int] | None = None,
    skip: bool = True,
    skip_data: str | None = None,
    lang: str = "uz",
) -> InlineKeyboardMarkup:
    exclude_ids = exclude_ids or set()
    rows: list[list[InlineKeyboardButton]] = []
    for p in players:
        if not p.alive or p.user_id in exclude_ids:
            continue
        label = p.full_name[:40] or str(p.user_id)
        rows.append(
            [InlineKeyboardButton(label, callback_data=f"{prefix}:{p.user_id}")]
        )
    if skip:
        rows.append(
            [
                InlineKeyboardButton(
                    t("btn_skip", lang),
                    callback_data=skip_data or f"{prefix}:skip",
                )
            ]
        )
    return InlineKeyboardMarkup(rows)


def night_targets(
    game: Game,
    prefix: str,
    actor_id: int,
    *,
    include_self: bool = False,
    extra_exclude: set[int] | None = None,
    skip: bool = True,
) -> InlineKeyboardMarkup:
    exclude = set(extra_exclude or [])
    if not include_self:
        exclude.add(actor_id)
    lang = getattr(game, "lang", "uz")
    return _player_rows(game.alive(), prefix, exclude, skip=skip, lang=lang)


def sheriff_menu(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t("btn_check", lang), callback_data="n:sm:check"),
                InlineKeyboardButton(t("btn_kill", lang), callback_data="n:sm:kill"),
            ],
            [InlineKeyboardButton(t("btn_skip", lang), callback_data="n:sm:skip")],
        ]
    )


def vote_kb(game: Game, voter_id: int | None = None) -> InlineKeyboardMarkup:
    voter = game.players.get(voter_id) if voter_id else None
    rows: list[list[InlineKeyboardButton]] = []
    round_id = game.vote_round_id
    for p in game.alive():
        if voter_id and p.user_id == voter_id:
            continue
        prefix = ""
        if voter:
            prefix = vote_ally_prefix(
                voter.role,
                p.role,
                target_is_sheriff=p.user_id == game.sheriff_user_id,
            )
        name = p.full_name[:36] or str(p.user_id)
        label = f"{prefix} {name}".strip() if prefix else name
        rows.append([InlineKeyboardButton(label, callback_data=f"v:{round_id}:{p.user_id}")])
    lang = getattr(game, "lang", "uz")
    if not game.skip_used_at_low_players:
        rows.append([InlineKeyboardButton(t("btn_skip", lang), callback_data=f"v:{round_id}:skip")])
    return InlineKeyboardMarkup(rows)


def confirm_kb(lang: str = "uz", yes: int = 0, no: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"{yes} 👍", callback_data="c:1"),
                InlineKeyboardButton(f"{no} 👎", callback_data="c:0"),
            ]
        ]
    )


def mafia_change_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t("btn_change_vote", lang),
                    callback_data="n:mf:change",
                )
            ]
        ]
    )


def test_role_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    from game.texts import _ROLE_ORDER

    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for role in _ROLE_ORDER:
        row.append(
            InlineKeyboardButton(
                t(f"role_{role.value}", lang),
                callback_data=f"gt:role:{role.value}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)
