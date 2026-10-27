from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from data import config
from game.roles import Role
from i18n import t
from i18n.langs import lang_label, public_codes

ROLE_BUTTON_ORDER = [
    Role.AHOLI,
    Role.KROSNIY_OTETS,
    Role.MAFIYA,
    Role.SHERIF,
    Role.SERJANT,
    Role.DOKTOR,
    Role.MANYAK,
    Role.KRASOTKA,
    Role.POTRASHITEL,
    Role.JURNALIST,
    Role.YAKUDZA,
]


def start_kb(
    lang: str,
    bot_username: str | None,
    *,
    staff: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if bot_username:
        rows.append(
            [
                InlineKeyboardButton(
                    t("btn_add_group", lang),
                    url=f"https://t.me/{bot_username}?startgroup=true",
                )
            ]
        )
    group_url = getattr(config, "PLAY_GROUP_URL", "") or ""
    if group_url:
        rows.append(
            [InlineKeyboardButton(t("btn_join_group", lang), url=group_url)]
        )
    else:
        rows.append(
            [InlineKeyboardButton(t("btn_join_group", lang), callback_data="ui:nogroup")]
        )
    rows.append(
        [InlineKeyboardButton(t("btn_language", lang), callback_data="ui:lang")]
    )
    rows.append(
        [
            InlineKeyboardButton("🎁 Kunlik bonus", callback_data="ret:bonus"),
            InlineKeyboardButton("📦 Omad sandig‘i", callback_data="ret:box"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("👥 Do‘stlarni taklif qilish", callback_data="ret:ref"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(t("btn_profile", lang), callback_data="ui:profile"),
            InlineKeyboardButton(t("btn_roles", lang), callback_data="ui:roles"),
        ]
    )
    return InlineKeyboardMarkup(rows)


def _webapp_or_alert(text: str, url: str) -> InlineKeyboardButton:
    if url:
        return InlineKeyboardButton(text, web_app=WebAppInfo(url=url))
    return InlineKeyboardButton(text, callback_data="ui:nomarket")


def profile_kb(
    lang: str,
    *,
    profile_url: str = "",
    market_url: str = "",
    topup_url: str = "",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                _webapp_or_alert(t("btn_profile_app", lang), profile_url),
                _webapp_or_alert(t("btn_shop", lang), market_url),
            ],
            [_webapp_or_alert(t("btn_topup", lang), topup_url)],
            [InlineKeyboardButton(t("btn_back", lang), callback_data="ui:home")],
        ]
    )


def language_kb(lang: str, back: str | None = "ui:home") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(lang_label(code, lang), callback_data=f"ui:setlang:{code}")]
        for code in public_codes()
    ]
    if not rows:
        rows = [[InlineKeyboardButton(lang_label("uz", lang), callback_data="ui:setlang:uz")]]
    if back:
        rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data=back)])
    return InlineKeyboardMarkup(rows)


def group_settings_kb(
    lang: str,
    auto_start: bool,
    *,
    staff: bool = False,
    command_id: int | None = None,
) -> InlineKeyboardMarkup:
    auto_label = (
        t("btn_auto_on", lang) if auto_start else t("btn_auto_off", lang)
    )
    rows = [
        [InlineKeyboardButton(t("btn_group_lang", lang), callback_data="gs:lang")],
        [InlineKeyboardButton(auto_label, callback_data="gs:auto")],
    ]
    if staff:
        rows.append([InlineKeyboardButton(t("btn_stats", lang), callback_data="gs:stats")])
        rows.append([InlineKeyboardButton(t("btn_rating", lang), callback_data="gs:rank")])
    close_data = f"gs:close:{command_id}" if command_id else "gs:close"
    rows.append([InlineKeyboardButton(t("btn_close", lang), callback_data=close_data)])
    return InlineKeyboardMarkup(rows)


def group_language_kb(lang: str, back: str = "gs:home") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(lang_label(code, lang), callback_data=f"gs:setlang:{code}")]
        for code in public_codes()
    ]
    if not rows:
        rows = [[InlineKeyboardButton(lang_label("uz", lang), callback_data="gs:setlang:uz")]]
    rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data=back)])
    return InlineKeyboardMarkup(rows)


def stats_nav_kb(lang: str, *, group: bool, back: str | None = None) -> InlineKeyboardMarkup:
    stats_data = "gs:stats" if group else "ui:stats"
    rank_data = "gs:rank" if group else "ui:rank"
    rows = [
        [
            InlineKeyboardButton(t("btn_stats", lang), callback_data=stats_data),
            InlineKeyboardButton(t("btn_rating", lang), callback_data=rank_data),
        ]
    ]
    if back:
        rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data=back)])
    return InlineKeyboardMarkup(rows)


def roles_kb(lang: str, back: str | None = "ui:home") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    pair: list[InlineKeyboardButton] = []
    for role in ROLE_BUTTON_ORDER:
        pair.append(
            InlineKeyboardButton(
                t(f"role_{role.value}", lang),
                callback_data=f"ui:role:{role.value}",
            )
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    if back:
        rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data=back)])
    return InlineKeyboardMarkup(rows)


def shop_kb(
    lang: str,
    items: list | None = None,
    stats: dict | None = None,
    packs: list | None = None,
    *,
    back: bool = False,
    market_url: str = "",
    pick: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if pick:
        pair: list[InlineKeyboardButton] = []
        for role in ROLE_BUTTON_ORDER:
            pair.append(
                InlineKeyboardButton(
                    t(f"role_{role.value}", lang),
                    callback_data=f"ui:pickrole:{role.value}",
                )
            )
            if len(pair) == 2:
                rows.append(pair)
                pair = []
        if pair:
            rows.append(pair)
        rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="ui:shop")])
        return InlineKeyboardMarkup(rows)

    stats = stats or {}
    armed = {
        "protection": bool(stats.get("armed_protection")),
        "documents": bool(stats.get("armed_documents")),
        "active_role": bool(stats.get("armed_active")),
        "chosen_role": bool(stats.get("armed_chosen")),
    }
    labels = {
        "protection": "🛡️",
        "documents": "📁",
        "active_role": "🎎",
        "chosen_role": "🎭",
    }
    use_row: list[InlineKeyboardButton] = []
    for field, emoji in labels.items():
        if int(stats.get(field) or 0) <= 0:
            continue
        if armed.get(field):
            use_row.append(
                InlineKeyboardButton(f"{emoji} {t('btn_armed', lang)}", callback_data="ui:shop")
            )
        else:
            use_row.append(
                InlineKeyboardButton(
                    f"{emoji} {t('btn_use', lang)}",
                    callback_data=f"ui:use:{field}",
                )
            )
        if len(use_row) == 2:
            rows.append(use_row)
            use_row = []
    if use_row:
        rows.append(use_row)
    if int(stats.get("chosen_role") or 0) > 0:
        rows.append(
            [InlineKeyboardButton(t("btn_pick_role", lang), callback_data="ui:pickrole")]
        )

    if items:
        for it in items:
            if not it.get("enabled", True):
                continue
            iid = it.get("id")
            emoji = it.get("emoji") or ""
            title = (
                it.get("title_ru")
                if lang == "ru"
                else (it.get("title_en") if lang == "en" else it.get("title_uz"))
            ) or iid
            money = int(it.get("money") or 0)
            vcoin = int(it.get("vcoin") or it.get("gems") or 0)
            pair = []
            if money > 0:
                pair.append(
                    InlineKeyboardButton(
                        f"{emoji} {title} {money} 💵",
                        callback_data=f"ui:buy:{iid}:money",
                    )
                )
            if vcoin > 0:
                pair.append(
                    InlineKeyboardButton(
                        f"{emoji} {title} {vcoin} 🪙",
                        callback_data=f"ui:buy:{iid}:vcoin",
                    )
                )
            if pair:
                rows.append(pair)

    if market_url:
        rows.insert(
            0,
            [
                InlineKeyboardButton(
                    t("btn_shop", lang), web_app=WebAppInfo(url=market_url)
                )
            ],
        )
    if back:
        rows.append([InlineKeyboardButton(t("btn_back", lang), callback_data="ui:home")])
    return InlineKeyboardMarkup(rows)
