from __future__ import annotations

import html
from collections import Counter

from game.models import Game, Player
from game.roles import Role
from game.rewards import payout_for, player_won_alive
from i18n import t

_ROLE_ORDER = (
    Role.KROSNIY_OTETS,
    Role.MAFIYA,
    Role.SHERIF,
    Role.SERJANT,
    Role.DOKTOR,
    Role.KRASOTKA,
    Role.POTRASHITEL,
    Role.MANYAK,
    Role.JURNALIST,
    Role.YAKUDZA,
    Role.AHOLI,
)


def mention(player: Player) -> str:
    name = html.escape(player.full_name)
    if player.is_bot:
        return f"<b>{name}</b>"
    return f'<a href="tg://user?id={player.user_id}"><b>{name}</b></a>'


def player_line(player: Player, index: int | None = None) -> str:
    prefix = f"{index}. " if index is not None else ""
    uname = f" @{html.escape(player.username)}" if player.username else ""
    host = " 👑" if player.is_host else ""
    return f"{prefix}{mention(player)}{uname}{host}"


def living_list(game: Game) -> str:
    lines = [f"{p.join_order}. {mention(p)}" for p in game.alive()]
    return "\n".join(lines) if lines else "—"


def _lang(game: Game | None = None, lang: str | None = None) -> str:
    if lang:
        return lang
    if game and getattr(game, "lang", None):
        return game.lang
    return "uz"


def joined_list(game: Game) -> str:
    lines = [player_line(p, i) for i, p in enumerate(game.joined(), start=1)]
    return "\n".join(lines) if lines else t("reg_empty", _lang(game))


def role_name(role: Role | str, lang: str = "uz") -> str:
    return t(f"role_{Role(role).value}", lang)


def role_card(role: Role, lang: str = "uz") -> str:
    return t(f"card_{role.value}", lang)


def registration_text(game: Game, seconds: int, min_players: int, max_players: int) -> str:
    lang = _lang(game)
    if game.test_mode:
        humans = [p for p in game.joined() if not p.is_bot]
        n = len(humans)
        size = game.test_size or max_players
        bots = max(0, size - n)
        return t(
            "test_reg_text",
            lang,
            n=n,
            max=size,
            bots=bots,
            players=joined_list(game),
        )
    n = len(game.players)
    return t(
        "reg_text",
        lang,
        n=n,
        max=max_players,
        min=min_players,
        players=joined_list(game),
    )


def game_started_text(lang: str = "uz") -> str:
    return t("game_started", lang)


def remaining_roles_block(game: Game) -> str:
    lang = _lang(game)
    counts: Counter[str] = Counter()
    active_n = 0
    for p in game.alive():
        if not p.role:
            continue
        if p.shop_active_role:
            active_n += 1
            continue
        counts[p.role] += 1
    parts: list[str] = []
    for role in _ROLE_ORDER:
        n = counts.get(role.value, 0)
        if not n:
            continue
        name = role_name(role, lang)
        parts.append(f"{name} - {n}" if n > 1 else name)
    if active_n:
        label = t("role_active_public", lang)
        parts.append(f"{label} - {active_n}" if active_n > 1 else label)
    return ", ".join(parts) if parts else "—"


def mafia_mates_text(members: list[Player], you: Player, lang: str = "uz") -> str | None:
    others = [p for p in members if p.user_id != you.user_id]
    if not others:
        return None
    lines = [t("mafia_mates_title", lang)]
    for p in others:
        role = (
            t("mafia_label_don", lang)
            if p.role == Role.KROSNIY_OTETS.value
            else t("mafia_label_mafiya", lang)
        )
        lines.append(t("mafia_mate_line", lang, name=mention(p), role=role))
    return "\n".join(lines)


def mafia_vote_line_text(game: Game, voter_id: int) -> str | None:
    voter = game.players.get(voter_id)
    if not voter:
        return None
    lang = _lang(game)
    role = (
        t("mafia_label_don", lang)
        if voter.role == Role.KROSNIY_OTETS.value
        else t("mafia_label_mafiya", lang)
    )
    act = game.night_actions.get(voter_id) or {}
    if act.get("skip") or not act.get("target"):
        return None
    chosen = game.players.get(int(act["target"]))
    if not chosen:
        return None
    return t(
        "mafia_vote_arrow",
        lang,
        role=role,
        voter=mention(voter),
        target=mention(chosen),
    )


def night_intro(lang: str = "uz") -> str:
    return t("night_intro", lang)


def night_living(game: Game, seconds: int) -> str:
    return t(
        "night_living",
        _lang(game),
        living=living_list(game),
        seconds=seconds,
    )


def night_public(game: Game) -> str:
    lang = _lang(game)
    return t(
        "night_living",
        lang,
        living=living_list(game),
        seconds=0,
    )


def day_intro(game: Game) -> str:
    return t("day_intro", _lang(game), n=game.night_number)


def day_living(game: Game) -> str:
    lang = _lang(game)
    alive_n = len(game.alive())
    return t(
        "day_living",
        lang,
        living=living_list(game),
        roles=remaining_roles_block(game),
        n=alive_n,
    )


def vote_public(game: Game, seconds: int) -> str:
    return t("vote_group", _lang(game), seconds=seconds)


def death_line(player: Player, lang: str = "uz") -> str:
    return t("death_line", lang, name=mention(player), role=role_name(player.role, lang))


def confirm_public(game: Game, target: Player, seconds: int = 0) -> str:
    return t("confirm_public", _lang(game), name=mention(target))


def confirm_closed(game: Game, target: Player) -> str:
    return t("confirm_closed", _lang(game), name=mention(target))


def lynch_hang_result(target: Player, yes: int, no: int, lang: str = "uz") -> str:
    return t(
        "lynch_hang_result",
        lang,
        yes=yes,
        no=no,
        name=mention(target),
    )


def lynch_role_reveal(target: Player, lang: str = "uz") -> str:
    return t(
        "lynch_was_role",
        lang,
        name=mention(target),
        role=role_name(target.role, lang) if target.role else "?",
    )


def lynch_no_agree(yes: int, no: int, lang: str = "uz") -> str:
    return t("lynch_no_agree", lang, yes=yes, no=no)


_CAUSE_ROLE = {
    "mafia": Role.KROSNIY_OTETS,
    "sheriff": Role.SHERIF,
    "manyak": Role.MANYAK,
    "potrashitel": Role.POTRASHITEL,
    "yakudza": Role.YAKUDZA,
}
_CAUSE_ORDER = ("sheriff", "potrashitel", "manyak", "mafia", "yakudza")


def night_kill_text(player: Player, causes: list[str], lang: str = "uz") -> str:
    names = [
        role_name(_CAUSE_ROLE[cause], lang)
        for cause in _CAUSE_ORDER
        if cause in causes
    ]
    body = t(
        "night_kill",
        lang,
        role=role_name(player.role, lang) if player.role else "?",
        name=mention(player),
    )
    if not names:
        return body
    if len(names) == 1:
        return body + "\n" + t("night_kill_cause", lang, killer=names[0])
    if len(names) == 2:
        joined = t("killers_two", lang, a=names[0], b=names[1])
        return body + "\n" + t("night_kill_cause", lang, killer=joined)
    extra = "\n".join(t("night_kill_cause", lang, killer=name) for name in names)
    return body + "\n" + extra


def night_report(deaths: list[Player], lang: str = "uz") -> str:
    if not deaths:
        return t("night_none", lang)
    lines = "\n".join(death_line(p, lang) for p in deaths)
    return t("night_some", lang, lines=lines)


def lynch_report(player: Player, lang: str = "uz") -> str:
    return t("lynch", lang, name=mention(player), role=role_name(player.role, lang))


def no_lynch(lang: str = "uz") -> str:
    return t("no_lynch", lang)


def vote_tally(game: Game) -> str:
    lang = _lang(game)
    parts = []
    for voter_id, target in game.votes.items():
        voter = game.players.get(int(voter_id))
        if not voter:
            continue
        if target == "skip":
            parts.append(t("vote_line_skip", lang, voter=mention(voter)))
            continue
        chosen = game.players.get(int(target))
        if chosen:
            parts.append(
                t("vote_line", lang, voter=mention(voter), target=mention(chosen))
            )
    body = "\n".join(parts) if parts else t("no_votes", lang)
    return t("votes_title", lang) + "\n" + body


def vote_board(game: Game, seconds: int) -> str:
    lang = _lang(game)
    text = vote_public(game, seconds)
    if not game.votes:
        return text

    eligible = [p.user_id for p in game.alive() if p.user_id != game.no_vote_user_id]
    total_eligible = len(eligible)
    total_voted = len(game.votes)

    counts: dict[object, list[Player]] = {}
    for uid, target in game.votes.items():
        voter = game.players.get(int(uid))
        if not voter:
            continue
        counts.setdefault(target, []).append(voter)

    lines = [f"\n📊 <b>Jarayon:</b> {total_voted}/{total_eligible} o‘yinchi ovoz berdi"]
    sorted_targets = sorted(counts.items(), key=lambda x: len(x[1]), reverse=True)
    for target, voters in sorted_targets:
        n = len(voters)
        bar = "🟩" * min(n, 6) + "⬜" * max(0, 6 - n)
        if target == "skip":
            label = "⏭ <i>Ovoz bermaslik (Skip)</i>"
        else:
            p = game.players.get(int(target))
            label = mention(p) if p else str(target)
        lines.append(f"• {label}: <b>{n}</b> ta {bar}")

    return text + "\n" + "\n".join(lines)


def vote_cast_text(game: Game, voter: Player, target) -> str:
    if target == "skip":
        return f"{mention(voter)} - Skip"
    chosen = game.players.get(int(target))
    if not chosen:
        return f"{mention(voter)} - Skip"
    return f"{mention(voter)} - {mention(chosen)}"


def lynch_score_text(
    target: Player,
    yes: int,
    no: int,
    hanged: bool,
    lang: str = "uz",
) -> str:
    if hanged:
        return t(
            "lynch_score_yes",
            lang,
            yes=yes,
            no=no,
            name=mention(target),
            role=role_name(target.role, lang) if target.role else "?",
        )
    if yes == no:
        return t("lynch_score_tie", lang, yes=yes, no=no)
    return t("lynch_score_no", lang, yes=yes, no=no)


def win_text(winner: str, lang: str = "uz") -> str:
    if winner == "town":
        return t("win_town", lang)
    if winner == "mafia":
        return t("win_mafia", lang)
    if winner == "manyak":
        return t("win_manyak", lang)
    return t("game_over", lang)


def _player_won(player: Player, winner: str) -> bool:
    return player_won_alive(player, winner)


def _duration_text(seconds: float, lang: str) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return t("duration_hms", lang, h=hours, m=minutes, s=secs)
    return t("duration_ms", lang, m=minutes, s=secs)


def end_game_text(game: Game, winner: str | None, lang: str | None = None) -> str:
    lang = _lang(game, lang)
    side = t(f"win_side_{winner}", lang) if winner else t("game_over", lang)
    winners: list[str] = []
    others: list[str] = []
    for p in game.joined():
        role = role_name(p.role, lang) if p.role else "?"
        money = 0 if game.test_mode else payout_for(game, p, winner)
        extra = f" — {money}$" if money else ""
        line = f"    {html.escape(p.full_name)} - {role}{extra}"
        if winner and _player_won(p, winner):
            winners.append(line)
        else:
            others.append(line)
    elapsed = 0.0
    if game.started_at:
        import time

        elapsed = time.time() - float(game.started_at)
    parts = [
        t("end_title", lang),
        t("end_winner_side", lang, side=side),
        "",
        t("end_winners_title", lang),
        "\n".join(winners) if winners else "    —",
        "",
        t("end_others_title", lang),
        "\n".join(others) if others else "    —",
        "",
        t("end_duration", lang, duration=_duration_text(elapsed, lang)),
    ]
    return "\n".join(parts)


def profile_username(player_name: str, username: str | None) -> str:
    raw = (username or player_name or "").strip()
    if raw.startswith("@"):
        raw = raw[1:]
    return html.escape(raw or "—")


def profile_card(
    lang: str,
    *,
    username: str,
    stats: dict,
    role: str | None = None,
    amount: int = 0,
    won: bool = False,
) -> str:
    body = t(
        "profile_body",
        lang,
        username=username,
        money=int(stats.get("money") or 0),
        vcoin=int(stats.get("vcoin") or stats.get("gems") or 0),
        gems=int(stats.get("vcoin") or stats.get("gems") or 0),
        protection=int(stats.get("protection") or 0),
        documents=int(stats.get("documents") or 0),
        active_role=int(stats.get("active_role") or 0),
        chosen_role=int(stats.get("chosen_role") or 0),
    )
    if amount and role:
        key = "profile_win_header" if won else "profile_reward_header"
        header = t(key, lang, role=role, amount=amount)
        return f"{header}\n\n{body}"
    return body


def reveal_all(game: Game) -> str:
    lang = _lang(game)
    lines = [t("reveal_title", lang)]
    for p in game.joined():
        mark = "✅" if p.alive else "💀"
        role = role_name(p.role, lang) if p.role else "?"
        lines.append(f"{mark} {mention(p)} — {role}")
    return "\n".join(lines)


def _rank_mention(user_id: int, name: str) -> str:
    label = html.escape(name or str(user_id))
    return f'<a href="tg://user?id={user_id}"><b>{label}</b></a>'


def global_stats_text(lang: str, games: int, players: int, money: int) -> str:
    return t(
        "stats_global",
        lang,
        games=games,
        players=players,
        money=money,
    )


def group_stats_text(
    lang: str, games: int, town: int, mafia: int, manyak: int, money: int
) -> str:
    return t(
        "stats_group",
        lang,
        games=games,
        town=town,
        mafia=mafia,
        manyak=manyak,
        money=money,
    )


def rating_text(
    lang: str,
    rows: list[tuple[int, str, int]],
    *,
    group: bool,
    you_rank: int | None,
    you_money: int,
) -> str:
    title = t("rating_title_group" if group else "rating_title_global", lang)
    if not rows:
        return f"{title}\n\n{t('rating_empty', lang)}"
    lines = [title, ""]
    for i, (uid, name, money) in enumerate(rows, start=1):
        lines.append(
            t(
                "rating_line",
                lang,
                n=i,
                name=_rank_mention(uid, name),
                money=money,
            )
        )
    lines.append("")
    if you_rank:
        lines.append(
            t("rating_you", lang, rank=you_rank, money=you_money)
        )
    else:
        lines.append(t("rating_unranked", lang))
    return "\n".join(lines)
