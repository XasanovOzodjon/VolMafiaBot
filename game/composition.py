from collections import Counter

from game.roles import Role

# (mafia, doktor, sherif, manyak, yakudza, krasotka, potrashitel, aholi, jurnalist, serjant)
# mafia = Don + oddiy mafia
_TABLE: dict[int, tuple[int, int, int, int, int, int, int, int, int, int]] = {
    4: (1, 1, 1, 0, 0, 0, 0, 1, 0, 0),
    5: (1, 1, 1, 0, 0, 0, 0, 2, 0, 0),
    6: (1, 1, 1, 1, 1, 0, 0, 1, 0, 0),
    7: (2, 1, 1, 1, 1, 0, 0, 1, 0, 0),
    8: (3, 1, 1, 1, 1, 1, 0, 0, 0, 0),
    9: (3, 1, 1, 1, 1, 1, 0, 1, 0, 0),
    10: (4, 1, 1, 1, 1, 1, 1, 0, 0, 0),
    11: (4, 1, 1, 1, 1, 1, 1, 1, 0, 0),
    12: (4, 1, 1, 1, 2, 1, 1, 1, 0, 0),
    13: (5, 1, 1, 1, 2, 1, 1, 1, 0, 0),
    14: (6, 1, 1, 1, 2, 1, 1, 1, 0, 0),
    15: (6, 1, 1, 1, 2, 1, 1, 1, 1, 0),
    16: (6, 1, 1, 1, 2, 1, 1, 2, 1, 0),
    17: (6, 1, 1, 1, 2, 1, 1, 2, 1, 1),
    18: (6, 1, 1, 1, 2, 1, 1, 3, 1, 1),
    19: (6, 1, 1, 2, 2, 1, 1, 3, 1, 1),
    20: (6, 1, 1, 2, 3, 1, 1, 3, 1, 1),
    21: (7, 1, 1, 2, 3, 1, 1, 3, 1, 1),
}


def _row(n: int) -> tuple[int, int, int, int, int, int, int, int, int, int]:
    if n in _TABLE:
        return _TABLE[n]
    if n < 4:
        return _TABLE[4]
    row = list(_TABLE[21])
    row[7] += n - 21
    return tuple(row)


def mafia_count(n: int) -> int:
    return _row(n)[0]


def build_roles(n: int) -> list[Role]:
    """O'yinchilar soniga qarab rollarni yig'adi (aralashtirilmagan)."""
    mafia, doktor, sherif, manyak, yakudza, krasotka, potrashitel, aholi, jurnalist, serjant = _row(n)
    roles: list[Role] = []
    if mafia >= 1:
        roles.append(Role.KROSNIY_OTETS)
        roles.extend([Role.MAFIYA] * (mafia - 1))
    roles.extend([Role.DOKTOR] * doktor)
    roles.extend([Role.SHERIF] * sherif)
    roles.extend([Role.MANYAK] * manyak)
    roles.extend([Role.YAKUDZA] * yakudza)
    roles.extend([Role.KRASOTKA] * krasotka)
    roles.extend([Role.POTRASHITEL] * potrashitel)
    roles.extend([Role.JURNALIST] * jurnalist)
    roles.extend([Role.SERJANT] * serjant)
    roles.extend([Role.AHOLI] * aholi)
    if len(roles) != n:
        raise ValueError(f"Rol tarkibi {n} o'yinchiga mos emas ({len(roles)})")
    return roles


_UNIQUE_ROLES = {
    Role.KROSNIY_OTETS,
    Role.SHERIF,
    Role.DOKTOR,
    Role.KRASOTKA,
    Role.JURNALIST,
    Role.SERJANT,
    Role.POTRASHITEL,
}


def build_roles_forced(n: int, forced: Role) -> list[Role]:
    """Test: tarkibda `forced` roli aniq bitta (mafia/aholi ko'p bo'lishi mumkin)."""
    return build_roles_with_claims(n, [forced])


def can_claim_role(n: int, others: list[Role], role: Role) -> bool:
    if role in _UNIQUE_ROLES and role in others:
        return False
    composition = build_roles(n)
    cap = composition.count(role)
    if cap == 0 and role != Role.AHOLI:
        cap = 1
    if role == Role.AHOLI:
        return True
    return others.count(role) < cap


def build_roles_with_claims(n: int, claims: list[Role]) -> list[Role]:
    """Tarkibda har bir tanlangan rol bo'lsin; qolgani odatiy kompozitsiya."""
    roles = build_roles(n)
    need: Counter[Role] = Counter()
    for role in claims:
        if role in _UNIQUE_ROLES:
            need[role] = 1
        else:
            need[role] += 1
    have = Counter(roles)
    for role, cnt in need.items():
        while have[role] < cnt:
            if have[Role.AHOLI] > 0:
                i = roles.index(Role.AHOLI)
                roles[i] = role
                have[Role.AHOLI] -= 1
                have[role] += 1
                continue
            stolen = False
            for i, current in enumerate(roles):
                if have[current] > need[current]:
                    roles[i] = role
                    have[current] -= 1
                    have[role] += 1
                    stolen = True
                    break
            if not stolen:
                break
    if len(roles) > n:
        roles = roles[:n]
    while len(roles) < n:
        roles.append(Role.AHOLI)
    return roles
