"""Sarvatobhadra Chakra — the full 81-cell grid and its vedha lines (DATA only).

The Sarvatobhadra (Trailokya-dīpikā) Chakra is a 9×9 grid holding the 28
nakṣatras (with Abhijit), the 16 vowels, the name consonants, the 12 rāśis and
the five tithi groups with their weekdays. A graha in a nakṣatra casts vedha
along three lines: **across** (straight to the opposite wall), **fore** (the
diagonal tilted in the zodiacal direction of travel along that wall) and
**hind** (the reverse diagonal). Every box a line crosses is under vedha.

Sources:
* Janārdana Harjī, *Mānasāgarī* ("trailokya-dīpika chakra") and the
  Brahmayāmala, as cited for the chakra; Narapati Jayacharya's *Svarodaya*
  tradition.
* Sanjay Rath, "Sarvatobhadra Cakra", *Saptarishis Astrology* — Rules I–III
  and the corner rule, with worked lines used here as doctrine tests:
  Kṛttikā (fore: a, Vṛṣabha, Nandā, Bhadrā, Tulā, ta, Viśākhā; hind: Bharaṇī;
  across: Śravaṇa), Rohiṇī, Mṛgaśirā and Punarvasu.
* The cell layout matches the published calculator at ayurastro.com cell for
  cell along all of those worked lines.

Orientation (as in those diagrams): North at the top, East on the right; the
nakṣatras run clockwise from the north-east corner — Kṛttikā…Āśleṣā down the
east wall, Maghā…Viśākhā right→left along the south, Anurādhā…Śravaṇa up the
west wall (with Abhijit), Dhaniṣṭhā…Bharaṇī left→right along the north.

Motion rule (Rath, Rules II–III): Rāhu/Ketu (always retrograde) — hind vedha
predominates; Sun and Moon (always direct) — fore predominates; Mars to
Saturn — retrograde → hind, direct and swift → fore, direct and normal →
across. Other teachers have the luminaries and nodes cast all three lines
equally, so all three lines are always returned and the predominant one is a
separate field.

Not encoded: the vedha-strength multipliers (×2 retrograde, ×3 exalted, ×½
debilitated) — a weighting, not data — and the uncertain fifth interchangeable
syllable pair.
"""

from __future__ import annotations

from ..angles import norm360
from ..constants import NAKSHATRA_ARC, SIGNS, Planet

NAKSHATRAS_28 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Abhijit",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

# Abhijit: 276°40' to 280°53'20" sidereal.
ABHIJIT_START = 276.0 + 40.0 / 60.0
ABHIJIT_END = 280.0 + 53.0 / 60.0 + 20.0 / 3600.0

TITHI_GROUPS = ["Nanda", "Bhadra", "Jaya", "Rikta", "Purna"]
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday"]
SIZE = 9


def _n(name):            return dict(kind="nakshatra", name=name)
def _v(name):            return dict(kind="vowel", name=name)
def _c(name, extra=()):  return dict(kind="consonant", name=name, attached=list(extra))
def _r(i):               return dict(kind="rashi", name=SIGNS[i])
def _t(g, days):         return dict(kind="tithi", name=TITHI_GROUPS[g],
                                     weekdays=[WEEKDAYS[d] for d in days])


N = NAKSHATRAS_28
# Row 0 = north (top), column 8 = east (right).
GRID = [
    [_v("ii"), _n(N[23]), _n(N[24]), _n(N[25]), _n(N[26]), _n(N[27]), _n(N[0]), _n(N[1]), _v("a")],
    [_n(N[22]), _v("rii"), _c("ga"), _c("sa"), _c("da", ("tha", "jha", "nya")), _c("ca"), _c("la"), _v("u"), _n(N[2])],
    [_n(N[21]), _c("kha"), _v("ai"), _r(10), _r(11), _r(0), _v("lri"), _v("a"), _n(N[3])],
    [_n(N[20]), _c("ja"), _r(9), _v("ah"), _t(3, [5]), _v("o"), _r(1), _c("va"), _n(N[4])],
    [_n(N[19]), _c("bha", ("dha", "pha", "ddha")), _r(8), _t(2, [4]), _t(4, [6]), _t(0, [0, 2]), _r(2), _c("ka", ("gha", "nga", "cha")), _n(N[5])],
    [_n(N[18]), _c("ya"), _r(7), _v("am"), _t(1, [1, 3]), _v("au"), _r(3), _c("ha"), _n(N[6])],
    [_n(N[17]), _c("na"), _v("e"), _r(6), _r(5), _r(4), _v("lrii"), _c("dda"), _n(N[7])],
    [_n(N[16]), _v("ri"), _c("ta"), _c("ra"), _c("pa", ("ssa", "nna", "ttha")), _c("tta"), _c("ma"), _v("uu"), _n(N[8])],
    [_v("i"), _n(N[15]), _n(N[14]), _n(N[13]), _n(N[12]), _n(N[11]), _n(N[10]), _n(N[9]), _v("aa")],
]

CELLS = {cell["name"]: (r, c) for r, row in enumerate(GRID)
         for c, cell in enumerate(row) if cell["kind"] == "nakshatra"}
SIDE = {n: ("east" if c == SIZE - 1 else "south" if r == SIZE - 1
            else "west" if c == 0 else "north")
        for n, (r, c) in CELLS.items()}

# Interchangeable syllables: a vedha on one is a vedha on the other.
VOWEL_PAIRS = [("a", "aa"), ("i", "ii"), ("u", "uu"), ("ri", "rii"),
               ("lri", "lrii"), ("e", "ai"), ("o", "au"), ("am", "ah")]
CONSONANT_PAIRS = [("ba", "va"), ("sa", "sha"), ("kha", "ssa"), ("ja", "ya")]

# Corner rule: Bharaṇī p4 + Kṛttikā p1 (NE), Āśleṣā p4 + Maghā p1 (SE),
# Viśākhā p4 + Anurādhā p1 (SW), Śravaṇa p4 + Dhaniṣṭhā p1 (NW) activate the
# corner vowel and the Pūrṇā tithi at the centre.
_PADA = NAKSHATRA_ARC / 4.0
CORNERS = {
    "NE": dict(cell=(0, 8), span=(2 * NAKSHATRA_ARC - _PADA, 2 * NAKSHATRA_ARC + _PADA)),
    "SE": dict(cell=(8, 8), span=(9 * NAKSHATRA_ARC - _PADA, 9 * NAKSHATRA_ARC + _PADA)),
    "SW": dict(cell=(8, 0), span=(16 * NAKSHATRA_ARC - _PADA, 16 * NAKSHATRA_ARC + _PADA)),
    "NW": dict(cell=(0, 0), span=(22 * NAKSHATRA_ARC - _PADA, 22 * NAKSHATRA_ARC + _PADA)),
}


def nakshatra_28(sidereal_longitude: float) -> str:
    """The 28-scheme nakṣatra of a sidereal longitude."""
    lon = norm360(sidereal_longitude)
    if ABHIJIT_START <= lon < ABHIJIT_END:
        return "Abhijit"
    names27 = [n for n in NAKSHATRAS_28 if n != "Abhijit"]
    return names27[int(lon // NAKSHATRA_ARC) % 27]


def _walk(r, c, dr, dc):
    out = []
    r, c = r + dr, c + dc
    while 0 <= r < SIZE and 0 <= c < SIZE:
        out.append((r, c))
        r, c = r + dr, c + dc
    return out


# (across, fore, hind) steps per wall; fore follows the zodiacal direction.
_STEPS = {
    "east":  ((0, -1), (1, -1), (-1, -1)),
    "south": ((-1, 0), (-1, -1), (-1, 1)),
    "west":  ((0, 1), (-1, 1), (1, 1)),
    "north": ((1, 0), (1, 1), (1, -1)),
}


def _line(cells):
    content = [dict(GRID[r][c], cell=(r, c)) for r, c in cells]
    end = content[-1] if content else None
    return dict(cells=cells, content=content,
                lands=end["name"] if end and end["kind"] == "nakshatra" else None)


def vedha_lines(nakshatra: str) -> dict[str, dict]:
    """The across, fore and hind vedha lines from *nakshatra* (28-scheme name).

    Each line gives the grid ``cells`` crossed, their ``content`` (kind/name;
    consonants carry their ``attached`` triplet, tithi cells their weekdays)
    and the nakṣatra it ``lands`` on.
    """
    if nakshatra not in CELLS:
        raise ValueError(f"not a 28-scheme nakṣatra: {nakshatra!r}")
    r, c = CELLS[nakshatra]
    a, f, h = _STEPS[SIDE[nakshatra]]
    return dict(across=_line(_walk(r, c, *a)), fore=_line(_walk(r, c, *f)),
                hind=_line(_walk(r, c, *h)))


def corner_trigger(sidereal_longitude: float):
    """Corner rule (Rath): a graha in the last pada before a corner or the first
    pada after it also has vedha on that corner's vowel and on the Pūrṇā tithi
    at the centre (the other vowels on the diagonal are NOT activated).
    Returns the corner name, its vowel, the ``activated`` boxes and the
    diagonal's cells for reference; ``None`` outside the eight corner padas."""
    lon = norm360(sidereal_longitude)
    for name, k in CORNERS.items():
        lo, hi = k["span"]
        if lo <= lon < hi:
            r, c = k["cell"]
            diag = [(i, i) for i in range(SIZE)] if r == c else \
                   [(i, SIZE - 1 - i) for i in range(SIZE)]
            vowel = GRID[r][c]["name"]
            return dict(corner=name, vowel=vowel, activated=[vowel, "Purna"],
                        diagonal_cells=diag)
    return None


def syllables_hit(content: list[dict]) -> set[str]:
    """Every syllable a line touches, expanded by the attached triplets and the
    interchangeable pairs."""
    out = set()
    for x in content:
        if x["kind"] in ("vowel", "consonant"):
            out.add(x["name"])
            out.update(x.get("attached", []))
    for a, b in VOWEL_PAIRS + CONSONANT_PAIRS:
        if a in out or b in out:
            out.update((a, b))
    return out


# Mean daily motion (deg/day): the śīghra / madhya split of direct motion.
MEAN_MOTION = {Planet.SUN: 0.9856, Planet.MOON: 13.1764, Planet.MARS: 0.5240,
               Planet.MERCURY: 0.9856, Planet.JUPITER: 0.0831,
               Planet.VENUS: 0.9856, Planet.SATURN: 0.0335}


def motion_class(planet: Planet, speed: float) -> str:
    """``vakri`` (retrograde), ``shighra`` (faster than mean) or ``madhya``.
    Rāhu/Ketu are always ``vakri``."""
    if planet in (Planet.RAHU, Planet.KETU) or speed < 0.0:
        return "vakri"
    return "shighra" if speed > MEAN_MOTION[planet] else "madhya"


def predominant_line(planet: Planet, motion: str) -> str:
    """Rath, Rules II–III: which vedha line predominates."""
    if planet in (Planet.RAHU, Planet.KETU):
        return "hind"
    if planet in (Planet.SUN, Planet.MOON):
        return "fore"
    return {"vakri": "hind", "shighra": "fore", "madhya": "across"}[motion]


def tithi_group(tithi_number: int) -> str:
    """Nandā / Bhadrā / Jayā / Riktā / Pūrṇā for a tithi 1..30."""
    n = (tithi_number - 1) % 15 + 1
    return TITHI_GROUPS[(n - 1) % 5]
