"""The domain dictionary — life-area DATA, decoupled from any engine.

A `DomainProfile` names a matter's houses, KP fulfil/negate sets, kārakas, Sāham,
and confirming varga. `resolve(word)` (in `interpreter.significators`) maps any
theme word to one of these; every engine reads the profile. This is pure DATA —
no computation, no convergence — so it stands on its own, free of the legacy
`event_evidence` monolith.
"""

from __future__ import annotations

from dataclasses import dataclass

from advance_astrology import Planet


@dataclass(frozen=True)
class DomainProfile:
    name: str
    houses: tuple[int, ...]               # primary bhāvas of the matter
    fulfil_houses: frozenset              # KP houses that MAKE the matter happen
    negate_houses: frozenset              # KP houses that BREAK/deny it (reversal)
    karakas: tuple[str, ...]              # Jaimini chara-kārakas (by name)
    natural_karaka: Planet | None         # natural significator graha
    arudhas: tuple[str, ...]              # Arudha keys (A1..A12, UL)
    saham: str | None                     # Tājika Saham timing the matter
    reversal_saham: str | None            # Saham timing the matter's reversal
    varga: int                            # divisional chart confirming the TYPE
    rupture_matter: bool = False          # the matter IS a rupture (divorce/…)
    base_domain: str | None = None        # underlying matter (divorce → marriage)

    @classmethod
    def from_dict(cls, name: str, spec: dict) -> "DomainProfile":
        return cls(
            name=name,
            houses=tuple(spec["houses"]),
            fulfil_houses=frozenset(spec["fulfil_houses"]),
            negate_houses=frozenset(spec.get("negate_houses", ())),
            karakas=tuple(spec.get("karakas", ())),
            natural_karaka=spec.get("natural_karaka"),
            arudhas=tuple(spec.get("arudhas", ())),
            saham=spec.get("saham"),
            reversal_saham=spec.get("reversal_saham"),
            varga=spec.get("varga", 9),
            rupture_matter=bool(spec.get("rupture_matter", False)),
            base_domain=spec.get("base_domain"),
        )


DOMAIN_PROFILES: dict[str, DomainProfile] = {}


def register_domain(name: str, **spec) -> DomainProfile:
    """Register (or override) a life-area at runtime — keeps domains open-ended."""
    prof = DomainProfile.from_dict(name, spec)
    DOMAIN_PROFILES[name] = prof
    return prof


# The shipped set — illustrative, NOT a closed list. Extend freely.
_SEED = {
    "marriage":  dict(houses=[7], fulfil_houses=[2, 7, 11], negate_houses=[1, 6, 10],
                      karakas=["Darakaraka"], natural_karaka=Planet.VENUS,
                      arudhas=["A7", "UL"], saham="Vivaha",
                      reversal_saham="Punarvivaha", varga=9),
    "career":    dict(houses=[10], fulfil_houses=[2, 6, 10, 11], negate_houses=[5, 8, 9, 12],
                      karakas=["Amatyakaraka"], natural_karaka=Planet.SATURN,
                      arudhas=["A10"], saham="Karma", varga=10),
    "children":  dict(houses=[5], fulfil_houses=[2, 5, 11], negate_houses=[1, 4, 10, 12],
                      karakas=["Putrakaraka"], natural_karaka=Planet.JUPITER,
                      arudhas=["A5"], saham="Putra", varga=7),
    "wealth":    dict(houses=[2, 11], fulfil_houses=[2, 5, 9, 11], negate_houses=[6, 8, 12],
                      natural_karaka=Planet.JUPITER, arudhas=["A2"], saham="Artha", varga=2),
    "mother":    dict(houses=[4], fulfil_houses=[2, 4, 11], negate_houses=[3, 8, 12],
                      karakas=["Matrikaraka"], natural_karaka=Planet.MOON,
                      arudhas=["A4"], varga=4),
    "father":    dict(houses=[9], fulfil_houses=[2, 9, 11], negate_houses=[3, 8, 12],
                      karakas=["Pitrikaraka"], natural_karaka=Planet.SUN,
                      arudhas=["A9"], varga=9),
    "illness":   dict(houses=[6, 8], fulfil_houses=[6, 8, 12], negate_houses=[1, 5, 11],
                      karakas=["Gnatikaraka", "Atmakaraka"], natural_karaka=Planet.SATURN,
                      arudhas=["A6"], saham="Roga", varga=30),
    "education": dict(houses=[4, 5, 9], fulfil_houses=[4, 5, 9, 11], negate_houses=[6, 8, 12],
                      natural_karaka=Planet.MERCURY, arudhas=["A5"], saham="Vidya", varga=24),
    "relocation": dict(houses=[4], fulfil_houses=[3, 4, 11, 12], negate_houses=[1, 6, 8],
                       karakas=["Matrikaraka"], natural_karaka=Planet.MOON,
                       arudhas=["A4"], varga=4),
}
for _n, _s in _SEED.items():
    register_domain(_n, **_s)
