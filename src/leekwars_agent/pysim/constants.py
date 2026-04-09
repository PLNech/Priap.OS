"""Game constants parsed from tools/leek-wars/src/model/constants.ts.

This is the SINGLE SOURCE OF TRUTH for all game constants.
NEVER hand-write constant values — they MUST come from this parser.
"""

from __future__ import annotations

import re
from pathlib import Path

_CONSTANTS_TS = Path(__file__).resolve().parents[3] / "tools" / "leek-wars" / "src" / "model" / "constants.ts"

_cache: dict[str, int | float | str] | None = None


def _parse_constants_ts() -> dict[str, int | float | str]:
    """Parse constants.ts into {name: value} dict.

    Format in file:
      { id: N, name: 'NAME', value: 'VAL', type: T, category: C, deprecated: bool, replacement: ... }
    """
    text = _CONSTANTS_TS.read_text()
    entries = re.findall(r"name:\s*'([A-Z_][A-Z_0-9]*)',\s*value:\s*'([^']*)'", text)

    constants: dict[str, int | float | str] = {}
    for name, val_str in entries:
        if val_str == "Infinity":
            constants[name] = float("inf")
        elif "." in val_str:
            constants[name] = float(val_str)
        else:
            try:
                constants[name] = int(val_str)
            except ValueError:
                constants[name] = val_str
    return constants


def get_all() -> dict[str, int | float | str]:
    """Return all 304 game constants, cached after first parse."""
    global _cache
    if _cache is None:
        _cache = _parse_constants_ts()
    return _cache


def get(name: str) -> int | float | str:
    """Get a single constant by name. Raises KeyError if not found."""
    return get_all()[name]


# ── Convenience accessors for commonly used constant families ──────

def effect_constants() -> dict[str, int]:
    """All EFFECT_* constants: {name: value}."""
    return {k: v for k, v in get_all().items() if k.startswith("EFFECT_") and isinstance(v, int)}


def area_constants() -> dict[str, int]:
    """All AREA_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("AREA_") and isinstance(v, int)}


def entity_constants() -> dict[str, int]:
    """All ENTITY_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("ENTITY_") and isinstance(v, int)}


def fight_constants() -> dict[str, int]:
    """All FIGHT_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("FIGHT_") and isinstance(v, int)}


def color_constants() -> dict[str, int]:
    """All COLOR_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("COLOR_") and isinstance(v, int)}


def cell_constants() -> dict[str, int]:
    """All CELL_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("CELL_") and isinstance(v, int)}


def launch_type_constants() -> dict[str, int]:
    """All LAUNCH_TYPE_* constants."""
    return {k: v for k, v in get_all().items() if k.startswith("LAUNCH_TYPE_") and isinstance(v, int)}


# ── Effect type ID reverse lookup ──────────────────────────────────

_EFFECT_ID_TO_NAME: dict[int, str] | None = None


def effect_id_to_name(eff_id: int) -> str:
    """Reverse lookup: effect type ID → constant name (e.g., 6 → 'EFFECT_ABSOLUTE_SHIELD')."""
    global _EFFECT_ID_TO_NAME
    if _EFFECT_ID_TO_NAME is None:
        _EFFECT_ID_TO_NAME = {}
        for k, v in effect_constants().items():
            # Skip TARGET_*, MODIFIER_* subconstants — they share IDs in a different namespace
            if "TARGET_" in k or "MODIFIER_" in k or "TRANSLATOR" in k:
                continue
            if v not in _EFFECT_ID_TO_NAME:
                _EFFECT_ID_TO_NAME[v] = k
    return _EFFECT_ID_TO_NAME.get(eff_id, f"UNKNOWN_EFFECT_{eff_id}")
