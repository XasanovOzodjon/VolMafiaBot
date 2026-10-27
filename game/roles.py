from enum import Enum


class Role(str, Enum):
    KRASOTKA = "krasotka"
    DOKTOR = "doktor"
    MAFIYA = "mafiya"
    KROSNIY_OTETS = "krosniy_otets"
    SHERIF = "sherif"
    POTRASHITEL = "potrashitel"
    MANYAK = "manyak"
    JURNALIST = "jurnalist"
    SERJANT = "serjant"
    YAKUDZA = "yakudza"
    AHOLI = "aholi"
    KAMIKADZE = "kamikadze"
    ADVOKAT = "advokat"
    MER = "mer"


ROLE_TITLE = {
    Role.KRASOTKA: "💃 Ma'shuqa",
    Role.DOKTOR: "👨‍⚕️ Shifokor",
    Role.MAFIYA: "🤵 Mafia",
    Role.KROSNIY_OTETS: "🤵 Don",
    Role.SHERIF: "🕵️ Komissar Katani",
    Role.POTRASHITEL: "💂 Padrajitel",
    Role.MANYAK: "🔪 Qotil",
    Role.JURNALIST: "📰 Jurnalist",
    Role.SERJANT: "💂 Serjant",
    Role.YAKUDZA: "🤞 Yakudza",
    Role.AHOLI: "👨🏼 Tinch aholi",
    Role.KAMIKADZE: "💣 Kamikadze",
    Role.ADVOKAT: "💼 Advokat",
    Role.MER: "🏛 Mer",
}

VOTE_ALLY_EMOJI = {
    Role.KROSNIY_OTETS: "🤵",
    Role.MAFIYA: "🤵",
    Role.ADVOKAT: "🤵",
    Role.SERJANT: "💂",
    Role.SHERIF: "🕵️",
}

MAFIA_ROLES = {Role.MAFIYA, Role.KROSNIY_OTETS, Role.ADVOKAT}

TOWN_ROLES = {
    Role.KRASOTKA,
    Role.DOKTOR,
    Role.SHERIF,
    Role.POTRASHITEL,
    Role.JURNALIST,
    Role.SERJANT,
    Role.YAKUDZA,
    Role.AHOLI,
    Role.KAMIKADZE,
    Role.MER,
}

# Potrashitel faqat "rolga ega" odamlarni o'ldira oladi
POTRASHITEL_KILLABLE = {
    Role.KRASOTKA,
    Role.DOKTOR,
    Role.MAFIYA,
    Role.KROSNIY_OTETS,
    Role.SHERIF,
    Role.POTRASHITEL,
    Role.MANYAK,
    Role.JURNALIST,
    Role.SERJANT,
    Role.KAMIKADZE,
    Role.ADVOKAT,
    Role.MER,
}

NIGHT_ACTOR_ROLES = {
    Role.KRASOTKA,
    Role.DOKTOR,
    Role.MAFIYA,
    Role.KROSNIY_OTETS,
    Role.SHERIF,
    Role.POTRASHITEL,
    Role.MANYAK,
    Role.JURNALIST,
    Role.ADVOKAT,
}


def is_mafia(role: Role | str) -> bool:
    return Role(role) in MAFIA_ROLES


def title(role: Role | str, lang: str = "uz") -> str:
    from i18n import t

    return t(f"role_{Role(role).value}", lang)


def vote_ally_prefix(
    voter_role: str | None,
    target_role: str | None,
    *,
    target_is_sheriff: bool = False,
) -> str:
    if not voter_role or not target_role:
        return ""
    if is_mafia(voter_role) and is_mafia(target_role):
        return VOTE_ALLY_EMOJI.get(Role(target_role), "🤵")
    if voter_role == Role.SHERIF.value and target_role == Role.SERJANT.value:
        return VOTE_ALLY_EMOJI[Role.SERJANT]
    if voter_role == Role.SERJANT.value and (
        target_role == Role.SHERIF.value or target_is_sheriff
    ):
        return VOTE_ALLY_EMOJI[Role.SHERIF]
    return ""
