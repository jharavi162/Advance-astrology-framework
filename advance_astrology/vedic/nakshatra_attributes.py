"""Per-nakshatra attributes used in compatibility and muhurta work.

Each of the 27 nakshatras carries a gana (temperament), yoni (animal),
nadi (constitution), ruling deity and planetary lord.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..constants import NAKSHATRA_LORDS, NAKSHATRAS, Planet

DEVA, MANUSHYA, RAKSHASA = "Deva", "Manushya", "Rakshasa"
ADI, MADHYA, ANTYA = "Adi", "Madhya", "Antya"

# Indexed 0..26 (Ashwini..Revati).
GANA = [
    DEVA, MANUSHYA, RAKSHASA, MANUSHYA, DEVA, MANUSHYA, DEVA, DEVA, RAKSHASA,
    RAKSHASA, MANUSHYA, MANUSHYA, DEVA, RAKSHASA, DEVA, RAKSHASA, DEVA,
    RAKSHASA, RAKSHASA, MANUSHYA, MANUSHYA, DEVA, RAKSHASA, RAKSHASA,
    MANUSHYA, MANUSHYA, DEVA,
]

YONI = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep",
    "Cat", "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger",
    "Deer", "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse",
    "Lion", "Cow", "Elephant",
]

NADI = [
    ADI, MADHYA, ANTYA, ANTYA, MADHYA, ADI, ADI, MADHYA, ANTYA,
    ANTYA, MADHYA, ADI, ADI, MADHYA, ANTYA, ANTYA, MADHYA, ADI,
    ADI, MADHYA, ANTYA, ANTYA, MADHYA, ADI, ADI, MADHYA, ANTYA,
]

DEITY = [
    "Ashwini Kumaras", "Yama", "Agni", "Brahma/Prajapati", "Soma", "Rudra",
    "Aditi", "Brihaspati", "Nagas/Sarpas", "Pitris", "Bhaga", "Aryaman",
    "Savitar", "Vishwakarma", "Vayu", "Indra-Agni", "Mitra", "Indra",
    "Nirriti", "Apas", "Vishwadevas", "Vishnu", "Vasus", "Varuna",
    "Aja Ekapada", "Ahir Budhnya", "Pushan",
]


@dataclass(frozen=True)
class NakshatraAttributes:
    index: int
    name: str
    lord: Planet
    gana: str
    yoni: str
    nadi: str
    deity: str


def attributes(index: int) -> NakshatraAttributes:
    return NakshatraAttributes(
        index=index,
        name=NAKSHATRAS[index],
        lord=NAKSHATRA_LORDS[index],
        gana=GANA[index],
        yoni=YONI[index],
        nadi=NADI[index],
        deity=DEITY[index],
    )
