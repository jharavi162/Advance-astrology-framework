"""Significator DICTIONARY — pick a domain from a word.

Every life-theme a human can name has significators in the chart (a bhāva, a
kāraka, a varga). This module is the **lexicon** that maps any theme word (English
or Hindi/Hinglish) to a `DomainProfile`, so the engine can answer a question about
*anything* without a domain being hand-registered first:

    resolve("vahan")  -> the vehicle domain (4th, Venus, D16)
    resolve("videsh") -> the foreign/abroad domain (9/12, Rahu, D12)

This is DATA only (CLAUDE.md routing: a new life-area / its houses-kāraka-saham-
varga is DATA), grounded in classical bhāva/graha/varga significations (BPHS;
Phaladeepika). It registers the resolved profile into `DOMAIN_PROFILES`, after
which the full generative panel (build_panel) judges it like any other matter.

Three-tier resolution:
  1. an already-registered domain (the curated 8 + relocation),
  2. a curated theme spec in `THEME_LEXICON` (classically tuned),
  3. a last-resort DERIVATION from house/planet/varga significations for an
     unknown word (flagged approximate).
"""

from __future__ import annotations

from advance_astrology import Planet
from interpreter.event_evidence import DOMAIN_PROFILES, register_domain

# --------------------------------------------------------------------------- #
# Classical significations — the alphabet for the unknown-word fallback (BPHS).
# --------------------------------------------------------------------------- #
HOUSE_THEMES: dict[int, set[str]] = {
    1: {"self", "body", "health", "personality", "appearance", "vitality", "life"},
    2: {"wealth", "money", "savings", "family", "speech", "food", "face", "assets"},
    3: {"sibling", "siblings", "brother", "sister", "courage", "communication",
        "short travel", "skill", "skills", "hobby", "writing", "effort"},
    4: {"home", "house", "property", "land", "mother", "vehicle", "car", "comfort",
        "real estate", "happiness", "domicile"},
    5: {"children", "child", "progeny", "romance", "love", "affair", "intelligence",
        "education", "creativity", "speculation", "mantra", "devotion"},
    6: {"enemy", "enemies", "disease", "illness", "debt", "loan", "litigation",
        "lawsuit", "competition", "service", "obstacle", "obstacles", "injury"},
    7: {"spouse", "marriage", "partner", "partnership", "business", "trade",
        "relationship", "wife", "husband", "contract"},
    8: {"longevity", "death", "inheritance", "secret", "secrets", "occult",
        "sudden", "transformation", "accident", "in-laws", "insurance", "scandal"},
    9: {"father", "fortune", "luck", "dharma", "religion", "higher education",
        "long travel", "guru", "pilgrimage", "law", "philosophy", "blessing"},
    10: {"career", "profession", "job", "status", "authority", "fame", "government",
         "promotion", "work", "power", "reputation"},
    11: {"gains", "gain", "income", "profit", "friends", "elder sibling",
         "fulfilment", "network", "aspiration", "ambition"},
    12: {"loss", "expense", "foreign", "abroad", "isolation", "hospital", "prison",
         "spirituality", "moksha", "liberation", "bed pleasures", "sleep", "exit"},
}

KARAKA_THEMES: dict[Planet, set[str]] = {
    Planet.SUN: {"father", "soul", "authority", "government", "power", "status"},
    Planet.MOON: {"mother", "mind", "emotion", "emotions", "home", "public", "water"},
    Planet.MARS: {"sibling", "brother", "land", "property", "courage", "accident",
                  "surgery", "energy", "litigation", "enemy"},
    Planet.MERCURY: {"intellect", "speech", "communication", "commerce", "education",
                     "trade", "business", "writing"},
    Planet.JUPITER: {"children", "child", "wisdom", "wealth", "guru", "husband",
                     "fortune", "dharma", "knowledge"},
    Planet.VENUS: {"spouse", "wife", "love", "romance", "marriage", "luxury",
                   "vehicle", "car", "art", "pleasure", "comfort"},
    Planet.SATURN: {"longevity", "service", "labour", "sorrow", "discipline",
                    "masses", "career", "debt", "death"},
    Planet.RAHU: {"foreign", "abroad", "obsession", "secret", "unconventional",
                  "sudden", "occult"},
    Planet.KETU: {"spirituality", "moksha", "detachment", "loss", "occult",
                  "liberation"},
}

VARGA_THEMES: dict[str, int] = {
    "marriage": 9, "spouse": 9, "romance": 9, "children": 7, "child": 7,
    "career": 10, "job": 10, "business": 10, "wealth": 2, "money": 2,
    "property": 4, "home": 4, "vehicle": 16, "luxury": 16, "education": 24,
    "higher education": 24, "father": 9, "mother": 4, "sibling": 3, "siblings": 3,
    "illness": 30, "disease": 30, "longevity": 30, "surgery": 30, "foreign": 12,
    "abroad": 12, "spirituality": 20, "moksha": 20, "father wealth": 9,
}


# --------------------------------------------------------------------------- #
# Curated theme lexicon — classically tuned specs (override the derivation).
# Each value is a DomainProfile spec; `synonyms` keys it from many words.
# --------------------------------------------------------------------------- #
THEME_LEXICON: dict[str, dict] = {
    "vehicle": dict(houses=[4], fulfil_houses=[4, 11], negate_houses=[6, 8, 12],
                    natural_karaka=Planet.VENUS, arudhas=["A4"], varga=16,
                    synonyms=["vahan", "vahana", "gaadi", "gadi", "car", "bike",
                              "conveyance", "automobile"]),
    "property": dict(houses=[4], fulfil_houses=[4, 11], negate_houses=[3, 8, 12],
                     natural_karaka=Planet.MARS, arudhas=["A4"], varga=4,
                     synonyms=["makaan", "makan", "ghar", "land", "zameen",
                               "real estate", "plot", "house buy", "flat"]),
    "romance": dict(houses=[5, 7], fulfil_houses=[5, 7, 11], negate_houses=[6, 8, 12],
                    natural_karaka=Planet.VENUS, arudhas=["A5", "UL"], varga=9,
                    synonyms=["love", "prem", "pyar", "pyaar", "affair", "dating",
                              "girlfriend", "boyfriend", "crush", "ishq"]),
    "business": dict(houses=[7, 10], fulfil_houses=[7, 10, 11], negate_houses=[5, 8, 12],
                     natural_karaka=Planet.MERCURY, arudhas=["A7", "A10"],
                     saham="Karma", varga=10,
                     synonyms=["vyapar", "vyavasaya", "trade", "startup", "venture",
                               "self employment", "dhandha"]),
    "foreign": dict(houses=[9, 12], fulfil_houses=[3, 9, 11, 12], negate_houses=[4, 8],
                    natural_karaka=Planet.RAHU, arudhas=["A12"], varga=12,
                    synonyms=["videsh", "abroad", "overseas", "immigration", "visa",
                              "foreign settlement", "nri", "travel abroad"]),
    "litigation": dict(houses=[6], fulfil_houses=[6, 11], negate_houses=[8, 12],
                       natural_karaka=Planet.MARS, arudhas=["A6"], varga=9,
                       synonyms=["mukadma", "case", "lawsuit", "court", "dispute",
                               "legal", "kanooni"]),
    "debt": dict(houses=[6], fulfil_houses=[6, 11], negate_houses=[8, 12],
                 natural_karaka=Planet.SATURN, arudhas=["A6"], varga=2,
                 synonyms=["karza", "karz", "loan", "borrowing", "udhaar", "emi"]),
    "inheritance": dict(houses=[8], fulfil_houses=[2, 8, 11], negate_houses=[6, 12],
                        natural_karaka=Planet.JUPITER, arudhas=["A8"], varga=2,
                        synonyms=["virasat", "legacy", "ancestral", "will",
                                  "wirasat", "patrimony"]),
    "spirituality": dict(houses=[9, 12], fulfil_houses=[5, 9, 12], negate_houses=[6, 11],
                         natural_karaka=Planet.KETU, arudhas=["A12"], varga=20,
                         synonyms=["moksha", "dharma", "religion", "sadhana",
                                   "adhyatma", "enlightenment", "guru diksha"]),
    "fame": dict(houses=[10], fulfil_houses=[1, 10, 11], negate_houses=[8, 12],
                 natural_karaka=Planet.SUN, arudhas=["A10"], saham="Yasas", varga=10,
                 synonyms=["kirti", "naam", "reputation", "status", "prasiddhi",
                           "recognition", "pratishtha"]),
    "surgery": dict(houses=[6, 8], fulfil_houses=[6, 8, 12], negate_houses=[1, 5, 11],
                    natural_karaka=Planet.MARS, arudhas=["A6"], varga=30,
                    synonyms=["operation", "accident", "injury", "wound", "chot"]),
}


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #
def _normalize(query: str) -> str:
    return " ".join(query.strip().lower().split())


def _synonym_index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for canon, spec in THEME_LEXICON.items():
        idx[canon] = canon
        for syn in spec.get("synonyms", ()):
            idx[_normalize(syn)] = canon
    # let synonyms also reach the already-registered (seeded) domains
    for seeded in DOMAIN_PROFILES:
        idx.setdefault(seeded, seeded)
    for word, dom in _SEEDED_SYNONYMS.items():
        idx[word] = dom
    return idx


# Synonyms that point at the curated seeded domains (marriage/career/… + relocation)
_SEEDED_SYNONYMS = {
    "shaadi": "marriage", "shadi": "marriage", "vivah": "marriage", "vivaah": "marriage",
    "wedding": "marriage", "spouse": "marriage", "naukri": "career", "job": "career",
    "profession": "career", "kaam": "career", "santaan": "children", "santan": "children",
    "bachche": "children", "bachcha": "children", "kids": "children", "progeny": "children",
    "paisa": "wealth", "dhan": "wealth", "money": "wealth", "daulat": "wealth",
    "maa": "mother", "mata": "mother", "pita": "father", "papa": "father",
    "bimari": "illness", "rog": "illness", "health": "illness", "disease": "illness",
    "padhai": "education", "shiksha": "education", "study": "education",
    "relocation": "relocation", "shift": "relocation", "move": "relocation",
    "sheher change": "relocation", "base change": "relocation",
}


def _derive_houses(key: str) -> list[int]:
    """Fallback: which houses signify this word (classical bhāva significations)."""
    hits = [h for h, themes in HOUSE_THEMES.items()
            if key in themes or any(t in key or key in t for t in themes)]
    return hits


def _derive_karaka(key: str) -> Planet | None:
    for p, themes in KARAKA_THEMES.items():
        if key in themes or any(t in key for t in themes):
            return p
    return None


def _dusthana_from(houses: list[int]) -> list[int]:
    out: set[int] = set()
    for h in houses:
        for off in (6, 8, 12):                 # the 6/8/12 reckoned FROM the house
            out.add((h - 1 + off - 1) % 12 + 1)
    return sorted(out)


def _complete(spec: dict) -> dict:
    """Fill fulfil/negate from the houses if a curated spec left them implicit."""
    spec = {k: v for k, v in spec.items() if k != "synonyms"}
    houses = list(spec["houses"])
    spec.setdefault("fulfil_houses", sorted(set(houses) | {11}))
    spec.setdefault("negate_houses", _dusthana_from(houses))
    return spec


def resolve(query: str):
    """Map any theme word to a DomainProfile (registering it if new)."""
    key = _normalize(query)
    idx = _synonym_index()
    canon = idx.get(key)

    # Phrase/word-boundary match against synonyms (so a multi-word query like
    # "career kaisa rahega" matches the WORD "career", not the substring "car"
    # inside it — naive substring matching mis-maps career→vehicle).
    if canon is None:
        import re
        tokens = set(re.findall(r"[a-z]+", key))
        for word, c in idx.items():
            if " " in word:                # multi-word synonym → phrase match
                if word in key:
                    canon = c
                    break
            elif word in tokens:           # single word → whole-word match
                canon = c
                break

    if canon and canon in DOMAIN_PROFILES:
        return DOMAIN_PROFILES[canon]
    if canon and canon in THEME_LEXICON:
        return register_domain(canon, **_complete(THEME_LEXICON[canon]))

    # tier 3 — derive from classical significations for a truly unknown word
    houses = _derive_houses(key)
    if houses:
        karaka = _derive_karaka(key)
        varga = next((VARGA_THEMES[t] for t in VARGA_THEMES if t in key), 9)
        return register_domain(
            key, houses=houses, fulfil_houses=sorted(set(houses) | {11}),
            negate_houses=_dusthana_from(houses), natural_karaka=karaka, varga=varga)

    raise ValueError(
        f"could not map {query!r} to any significator; add it to THEME_LEXICON "
        f"or use a registered domain {sorted(DOMAIN_PROFILES)}")
