"""Planetary states (avasthas)."""

from __future__ import annotations

from ..angles import angular_separation, to_zodiac
from ..constants import RULERSHIPS, VEDIC_GRAHAS, Planet
from .dignities import dignity

# Baladi (five-fold) states by 6° segment within a sign.
BALADI_STATES = ["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
# Relative strength weight traditionally assigned to each baladi state.
BALADI_STRENGTH = {"Bala": 0.25, "Kumara": 0.5, "Yuva": 1.0,
                   "Vriddha": 0.75, "Mrita": 0.0}

# Combustion (astangata) orbs from the Sun, in degrees.
COMBUSTION_ORB = {
    Planet.MOON: 12.0, Planet.MARS: 17.0, Planet.MERCURY: 14.0,
    Planet.JUPITER: 11.0, Planet.VENUS: 10.0, Planet.SATURN: 15.0,
}


def baladi_avastha(longitude: float) -> str:
    """Infant→dead state from the degree within the sign (reversed for even
    signs)."""
    pos = to_zodiac(longitude)
    seg = int(pos.degree_in_sign // 6.0)        # 0..4
    if pos.sign_index % 2 == 1:                 # even-numbered sign -> reversed
        seg = 4 - seg
    return BALADI_STATES[seg]


def jagradadi_avastha(planet: Planet, longitude: float) -> str:
    """Three-fold wakefulness state from sign dignity.

    Jagrat (awake) in own/exaltation, Swapna (dreaming) in friendly/neutral,
    Sushupti (sleeping) in enemy/debilitation.
    """
    dig = dignity(planet, longitude)
    if dig.is_exalted or dig.is_own or dig.is_moolatrikona:
        return "Jagrat"
    if dig.is_debilitated:
        return "Sushupti"
    return "Swapna"


def is_combust(planet: Planet, longitude: float, sun_longitude: float) -> bool:
    """Whether a planet is combust (astangata) — too close to the Sun."""
    if planet not in COMBUSTION_ORB:
        return False
    return angular_separation(longitude, sun_longitude) <= COMBUSTION_ORB[planet]


def deeptadi_avastha(planet: Planet, longitude: float,
                     sun_longitude: float | None = None) -> str:
    """Temperamental mood (Dīptādi) — the fuller eight-state scheme.

    Dīpta (exalted), Svastha (own), Pramudita (great-friend), Śānta
    (friend/neutral), Dīna (enemy), Khala (great-enemy), Vikala (combust),
    Duḥkhita (debilitated). Combustion overrides to Vikala.
    """
    if sun_longitude is not None and is_combust(planet, longitude, sun_longitude):
        return "Vikala"
    dig = dignity(planet, longitude)
    if dig.is_debilitated:
        return "Duhkhita"
    if dig.is_exalted:
        return "Dipta"
    if dig.is_own or dig.is_moolatrikona:
        return "Svastha"
    # Fall back to the dispositor relationship for the remaining moods.
    from ..constants import RULERSHIPS, SIGNS
    from .dignities import natural_relationship
    sign = SIGNS[to_zodiac(longitude).sign_index]
    dispositor = RULERSHIPS[sign]
    rel = natural_relationship(planet, dispositor)
    return {"Friend": "Pramudita", "Neutral": "Shanta", "Enemy": "Dina"}.get(
        rel, "Shanta")


def all_avasthas(planet: Planet, longitude: float,
                 sun_longitude: float | None = None) -> dict[str, str]:
    return {
        "baladi": baladi_avastha(longitude),
        "jagradadi": jagradadi_avastha(planet, longitude),
        "deeptadi": deeptadi_avastha(planet, longitude, sun_longitude),
        "combust": "Yes" if (sun_longitude is not None
                             and is_combust(planet, longitude, sun_longitude))
                   else "No",
    }


# --------------------------------------------------------------------------- #
# Lajjitādi (six moods) — BPHS, avasthā adhyāya
# --------------------------------------------------------------------------- #
LAJJITADI_STATES = ["Lajjita", "Garvita", "Kshudhita", "Trishita", "Mudita", "Kshobhita"]
SAPTA_GRAHAS = (Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                Planet.JUPITER, Planet.VENUS, Planet.SATURN)
WATERY_SIGNS = {3, 7, 11}                    # Karka, Vṛścika, Mīna
VEDIC_SET = set(VEDIC_GRAHAS)


def lajjitadi_avastha(planet: Planet, signs: dict, longitudes: dict, asc_sign: int,
                      *, moon_waxing: bool = True) -> list[dict]:
    """Every Lajjitādi state *planet* is in, each with the condition that met it.

    BPHS (avasthā adhyāya):
      Lajjita   — in the 5th, joined by Rāhu/Ketu, the Sun, Saturn or Mars.
      Garvita   — in exaltation or mūlatrikoṇa.
      Kṣudhita  — in an enemy's sign, or joined or aspected by an enemy, or
                  joined by Saturn.
      Tṛṣita    — in a watery sign, aspected by a malefic and not by a benefic.
      Mudita    — in a friend's sign, or joined or aspected by a benefic, or
                  joined by Jupiter.
      Kṣobhita  — joined by the Sun and aspected by (or joined with) a
                  malefic, or aspected by an enemy.

    Conventions: "joined" is the same sign; drishti is the sign-based graha
    drishti of the seven grahas; friend/enemy is the compound (pañcadhā)
    relationship of *planet* towards the other graha (great friend/enemy
    included); benefic/malefic is natural (waxing Moon and an unafflicted
    Mercury benefic). Applies to the seven grahas; Rāhu/Ketu join only as
    company. A graha may be in several states, or none.
    """
    from ..constants import SIGNS
    from .aspects import aspects_sign
    from .dignities import compound_relationship
    from .nature import natural_benefic
    if planet not in SAPTA_GRAHAS:
        return []
    s = int(signs[planet])
    house = (s - int(asc_sign)) % 12 + 1
    others = [q for q in signs if q != planet and q in VEDIC_SET]
    joined = [q for q in others if int(signs[q]) == s]
    aspecting = [q for q in others if q in SAPTA_GRAHAS
                 and aspects_sign(q, int(signs[q]), s)]
    malefic_with_merc = any(not natural_benefic(q) and q is not Planet.MOON
                            for q in others if int(signs[q]) == int(signs[Planet.MERCURY]))

    def benefic(q):
        return natural_benefic(q, moon_waxing=moon_waxing,
                               mercury_with_malefic=malefic_with_merc)

    def rel(q):
        return compound_relationship(planet, s, q, int(signs[q]))

    enemy = lambda q: rel(q) in ("Enemy", "Great Enemy")
    friend = lambda q: rel(q) in ("Friend", "Great Friend")
    lord = RULERSHIPS[SIGNS[s]]
    names = lambda qs: ", ".join(q.value for q in qs)
    out = []

    def add(state, why):
        out.append(dict(state=state, reason=why))

    lj = [q for q in joined if q in (Planet.RAHU, Planet.KETU, Planet.SUN,
                                     Planet.SATURN, Planet.MARS)]
    if house == 5 and lj:
        add("Lajjita", f"in the 5th with {names(lj)}")
    dig = dignity(planet, longitudes[planet])
    if dig.is_exalted or dig.is_moolatrikona:
        add("Garvita", "exalted" if dig.is_exalted else "in mulatrikona")
    why = []
    if lord != planet and enemy(lord):
        why.append(f"in the sign of enemy {lord.value}")
    if [q for q in joined if q in SAPTA_GRAHAS and enemy(q)]:
        why.append(f"with enemy {names(q for q in joined if q in SAPTA_GRAHAS and enemy(q))}")
    if [q for q in aspecting if enemy(q)]:
        why.append(f"aspected by enemy {names(q for q in aspecting if enemy(q))}")
    if Planet.SATURN in joined:
        why.append("with Saturn")
    if why:
        add("Kshudhita", "; ".join(why))
    mal_asp = [q for q in aspecting if not benefic(q)]
    ben_asp = [q for q in aspecting if benefic(q)]
    if s in WATERY_SIGNS and mal_asp and not ben_asp:
        add("Trishita", f"watery sign, aspected by malefic {names(mal_asp)}, no benefic aspect")
    why = []
    if lord != planet and friend(lord):
        why.append(f"in the sign of friend {lord.value}")
    bj = [q for q in joined if q in SAPTA_GRAHAS and benefic(q)]
    if bj:
        why.append(f"with benefic {names(bj)}")
    if ben_asp:
        why.append(f"aspected by benefic {names(ben_asp)}")
    if Planet.JUPITER in joined and Planet.JUPITER not in bj:
        why.append("with Jupiter")
    if why:
        add("Mudita", "; ".join(why))
    if Planet.SUN in joined:
        mal = [q for q in aspecting + joined if q is not Planet.SUN and not benefic(q)]
        en = [q for q in aspecting if enemy(q)]
        if mal or en:
            add("Kshobhita", "with the Sun and " + "; ".join(
                x for x in (f"malefic {names(dict.fromkeys(mal))}" if mal else "",
                            f"aspected by enemy {names(en)}" if en else "") if x))
    return out


# --------------------------------------------------------------------------- #
# Śayanādi (twelve activities) — BPHS, avasthā adhyāya
# --------------------------------------------------------------------------- #
SHAYANADI_STATES = ["Shayana", "Upaveshana", "Netrapani", "Prakashana", "Gamana",
                    "Agamana", "Sabha", "Agama", "Bhojana", "Nrityalipsa",
                    "Kautuka", "Nidra"]
SHAYANADI_NUMBER = {Planet.SUN: 1, Planet.MOON: 2, Planet.MARS: 3, Planet.MERCURY: 4,
                    Planet.JUPITER: 5, Planet.VENUS: 6, Planet.SATURN: 7,
                    Planet.RAHU: 8, Planet.KETU: 9}


def shayanadi_index(nakshatra: int, planet_number: int, navamsa: int,
                    moon_nakshatra: int, ghati: int, lagna: int) -> int:
    """(C × P × A + M + G + L) mod 12, with 0 read as 12.

    C the planet's nakṣatra (Aśvinī 1), P the planet's number (Sun 1 …
    Saturn 7, Rāhu 8, Ketu 9), A its navāṁśa within the sign (1–9), M the
    Moon's nakṣatra, G the ghaṭī running at birth (counted from sunrise), L
    the lagna sign (Meṣa 1).
    """
    r = (nakshatra * planet_number * navamsa + moon_nakshatra + ghati + lagna) % 12
    return r or 12


def shayanadi_avastha(planet: Planet, longitude: float, moon_longitude: float,
                      asc_sign: int, ghati: int) -> str:
    nak = lambda x: int((float(x) % 360) // (360 / 27)) + 1
    navamsa = int((float(longitude) % 30) // (30 / 9)) + 1
    i = shayanadi_index(nak(longitude), SHAYANADI_NUMBER[planet], navamsa,
                        nak(moon_longitude), ghati, int(asc_sign) + 1)
    return SHAYANADI_STATES[i - 1]


def running_ghati(birth_utc, sunrise) -> int:
    """The ghaṭī running at birth: whole ghaṭīs elapsed since sunrise, plus one."""
    return int((birth_utc - sunrise).total_seconds() // 1440) + 1
