"""Download a JPL ephemeris kernel.

The package already ships ``de421.bsp`` (covering 1899-2053). Use this helper
to fetch a wider-range kernel such as ``de440`` (1550-2650) if you need birth
dates outside the bundled range, then point the engine at it via the
``ASTRO_EPHEMERIS`` environment variable or ``Ephemeris(bsp_path=...)``.

    python scripts/download_ephemeris.py de440s.bsp
"""

import sys
from pathlib import Path

from skyfield.api import Loader

KERNELS = {
    "de421.bsp": "1899-2053, ~17 MB (bundled)",
    "de440s.bsp": "1849-2150, ~32 MB",
    "de440.bsp": "1550-2650, ~114 MB",
    "de406.bsp": "−3000 to +3000, ~190 MB",
}


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "de440s.bsp"
    dest = Path(__file__).resolve().parent.parent / "advance_astrology" / "data"
    dest.mkdir(parents=True, exist_ok=True)

    if target not in KERNELS:
        print(f"Unknown kernel '{target}'. Known kernels:")
        for name, desc in KERNELS.items():
            print(f"  {name:<12} {desc}")
        return 1

    print(f"Downloading {target} ({KERNELS[target]}) to {dest} ...")
    load = Loader(str(dest))
    load(target)
    print("Done. Use it with:")
    print(f"  export ASTRO_EPHEMERIS={dest / target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
