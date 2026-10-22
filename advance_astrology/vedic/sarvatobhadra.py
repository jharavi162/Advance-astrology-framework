"""Sarvatobhadra Chakra — the nakṣatra ring and its vedha lines (DATA only).

The Sarvatobhadra Chakra (Narapati Jayacharya, *Narapati-jayacharyā
Svarodaya*) is a 9×9 grid. Its outer ring holds the 28 nakṣatras (the 27 plus
Abhijit), seven to each side, running clockwise from the east:

* **East** (top row, left → right): Kṛttikā … Āśleṣā
* **South** (right column, top → bottom): Maghā … Viśākhā
* **West** (bottom row, right → left): Anurādhā … Śravaṇa (with Abhijit)
* **North** (left column, bottom → top): Dhaniṣṭhā … Bharaṇī

A graha in a nakṣatra casts *vedha* along three straight lines across the
grid: the **front** line (straight across to the opposite side) and the two
**diagonals**. This module gives the grid geometry, the cells each line
crosses, and the nakṣatras where each line lands; for example Kṛttikā's front
line lands on Śravaṇa and its diagonals on Bharaṇī and Viśākhā.

What this module deliberately does NOT encode:

* **The inner rings** (the consonants, vowels, rāśis, tithis and weekdays
  placed in the inner cells). Their exact placement is not encoded until it
  can be checked against the source text; each line's crossed cells are
  returned as grid coordinates so that inner content can be attached later.
* **Which diagonal is "vāma" (left) and which "dakṣiṇa" (right)**, and the
  rule that weights one line by the graha's motion (vakri / śīghra /
  madhya). Sources word this differently. The diagonals are named here by
  geometry (``diagonal_cw`` and ``diagonal_ccw``: the one that lands on the
  next side clockwise vs counter-clockwise), and the graha's motion class is
  returned alongside as data, without picking a line from it.
"""

from __future__ import annotations

from ..angles import norm360
from ..constants import NAKSHATRA_ARC, Planet

# The 28 nakṣatras in zodiacal order (Abhijit between Uttarāṣāḍhā and Śravaṇa).
NAKSHATRAS_28 = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Abhijit",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

# Abhijit: 276°40' to 280°53'20" sidereal (last quarter of Uttarāṣāḍhā and the
# first fifteenth of Śravaṇa).
ABHIJIT_START = 276.0 + 40.0 / 60.0
ABHIJIT_END = 280.0 + 53.0 / 60.0 + 20.0 / 3600.0

SIZE = 9  # 9×9 grid; row 0 = east (top), column 8 = south (right)


def _ring_cells() -> dict[str, tuple[int, int]]:
    """(row, col) of each of the 28 nakṣatras on the outer ring."""
    east = ["Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
            "Pushya", "Ashlesha"]
    south = ["Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
             "Swati", "Vishakha"]
    west = ["Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
            "Abhijit", "Shravana"]
    north = ["Dhanishta", "Shatabhisha", "Purva Bhadrapada",
             "Uttara Bhadrapada", "Revati", "Ashwini", "Bharani"]
    cells = {}
    for k, n in enumerate(east):
        cells[n] = (0, 1 + k)                 # top row, left → right
    for k, n in enumerate(south):
        cells[n] = (1 + k, SIZE - 1)          # right column, top → bottom
    for k, n in enumerate(west):
        cells[n] = (SIZE - 1, SIZE - 2 - k)   # bottom row, right → left
    for k, n in enumerate(north):
        cells[n] = (SIZE - 2 - k, 0)          # left column, bottom → top
    return cells


CELLS = _ring_cells()
_AT = {v: k for k, v in CELLS.items()}
SIDE = {n: ("east" if r == 0 else "west" if r == SIZE - 1
            else "north" if c == 0 else "south")
        for n, (r, c) in CELLS.items()}


def nakshatra_28(sidereal_longitude: float) -> str:
    """The 28-scheme nakṣatra of a sidereal longitude (Abhijit carved out of
    Uttarāṣāḍhā and Śravaṇa)."""
    lon = norm360(sidereal_longitude)
    if ABHIJIT_START <= lon < ABHIJIT_END:
        return "Abhijit"
    names27 = [n for n in NAKSHATRAS_28 if n != "Abhijit"]
    return names27[int(lon // NAKSHATRA_ARC) % 27]


def _inward(side: str) -> tuple[int, int]:
    return {"east": (1, 0), "west": (-1, 0),
            "north": (0, 1), "south": (0, -1)}[side]


def _walk(start: tuple[int, int], step: tuple[int, int]) -> list[tuple[int, int]]:
    """Cells from *start* (exclusive) moving by *step* until the outer ring."""
    r, c = start
    path = []
    while True:
        r, c = r + step[0], c + step[1]
        if not (0 <= r < SIZE and 0 <= c < SIZE):
            break
        path.append((r, c))
        if r in (0, SIZE - 1) or c in (0, SIZE - 1):
            break
    return path


def vedha_lines(nakshatra: str) -> dict[str, dict]:
    """The three vedha lines from *nakshatra* (a 28-scheme name).

    Returns ``front``, ``diagonal_cw`` and ``diagonal_ccw``, each with the grid
    ``cells`` it crosses (row, col) and the nakṣatra it ``lands`` on at the
    outer ring (``None`` if it lands on a corner cell).
    """
    if nakshatra not in CELLS:
        raise ValueError(f"not a 28-scheme nakṣatra: {nakshatra!r}")
    start = CELLS[nakshatra]
    dr, dc = _inward(SIDE[nakshatra])
    # Perpendicular to the inward direction; "cw" is the one that, combined
    # with inward, heads for the next side clockwise (east → south → west →
    # north). For the east side inward is (+1, 0) and clockwise is +col.
    cw = {"east": (0, 1), "south": (1, 0), "west": (0, -1),
          "north": (-1, 0)}[SIDE[nakshatra]]
    lines = {"front": (dr, dc),
             "diagonal_cw": (dr + cw[0], dc + cw[1]),
             "diagonal_ccw": (dr - cw[0], dc - cw[1])}
    out = {}
    for name, step in lines.items():
        cells = _walk(start, step)
        end = cells[-1] if cells else None
        out[name] = dict(cells=cells, lands=_AT.get(end))
    return out


# Mean daily motion (deg/day), for the śīghra / madhya split of direct motion.
MEAN_MOTION = {Planet.SUN: 0.9856, Planet.MOON: 13.1764, Planet.MARS: 0.5240,
               Planet.MERCURY: 0.9856, Planet.JUPITER: 0.0831,
               Planet.VENUS: 0.9856, Planet.SATURN: 0.0335}


def motion_class(planet: Planet, speed: float) -> str:
    """``vakri`` (retrograde), ``shighra`` (faster than its mean motion) or
    ``madhya`` (direct, at or below mean). Rāhu/Ketu are always ``vakri``."""
    if planet in (Planet.RAHU, Planet.KETU) or speed < 0.0:
        return "vakri"
    return "shighra" if speed > MEAN_MOTION[planet] else "madhya"
