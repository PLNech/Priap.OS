"""Equipment registry parsed from leek-wars submodule source files.

This is the CANONICAL source for chip/weapon data in Python. All lookups
(chip_id ↔ template, names, stats, effects) go through here.

Source of truth: tools/leek-wars/src/model/{chips,weapons}.ts
These are parsed once at import time. If the submodule updates, this
module picks up the changes automatically.

Usage:
    from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY

    # Lookup by any key
    flame = CHIP_REGISTRY.by_name("flame")
    flame = CHIP_REGISTRY.by_id(5)
    flame = CHIP_REGISTRY.by_template(10)

    # Decode a fight action template ID
    chip = CHIP_REGISTRY.by_template(57)  # -> Chip(name='tranquilizer', ...)

    # All chips/weapons as dicts
    for chip in CHIP_REGISTRY.all():
        print(f"{chip.name}: id={chip.id}, template={chip.template}")
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar

_T = TypeVar("_T")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Effect:
    """A single effect on a chip or weapon."""
    id: int
    value1: float
    value2: float
    turns: int
    targets: int
    modifiers: int
    type: int  # 1=damage, 2=heal, 4=shield, 5=buff, 6=poison, 7=debuff


@dataclass(frozen=True)
class Chip:
    """A chip parsed from chips.ts."""
    id: int               # chip_id — used by API inventory, sim_defaults
    name: str
    template: int         # used in fight replay actions and LeekScript constants
    level: int
    cost: int
    min_range: int
    max_range: int
    cooldown: int
    initial_cooldown: int
    los: bool
    area: int
    max_uses: int         # -1 = unlimited
    type: int
    effects: tuple[Effect, ...] = field(default_factory=tuple)

    @property
    def leekscript_constant(self) -> str:
        """The CHIP_X constant name used in LeekScript."""
        return f"CHIP_{self.name.upper()}"


@dataclass(frozen=True)
class Weapon:
    """A weapon parsed from weapons.ts."""
    id: int               # weapon_id — used by API
    name: str
    template: int         # used in fight replay actions and LeekScript constants
    item: int             # item_id — used by market/inventory
    level: int
    cost: int
    min_range: int
    max_range: int
    los: bool
    area: int
    max_uses: int         # -1 = unlimited
    forgotten: bool
    effects: tuple[Effect, ...] = field(default_factory=tuple)
    passive_effects: tuple[Effect, ...] = field(default_factory=tuple)

    @property
    def leekscript_constant(self) -> str:
        """The WEAPON_X constant name used in LeekScript."""
        return f"WEAPON_{self.name.upper()}"


# ---------------------------------------------------------------------------
# Registry (generic for chips and weapons)
# ---------------------------------------------------------------------------

class _Registry(Generic[_T]):
    """Generic lookup registry with id, template, and name indexes."""

    def __init__(self, items: list, kind: str):
        self._kind = kind
        self._items = tuple(items)
        self._by_id: dict[int, _T] = {}
        self._by_template: dict[int, _T] = {}
        self._by_name: dict[str, _T] = {}
        for item in items:
            self._by_id[item.id] = item
            self._by_template[item.template] = item
            self._by_name[item.name] = item

    def by_id(self, chip_id: int) -> _T | None:
        return self._by_id.get(chip_id)

    def by_template(self, template: int) -> _T | None:
        return self._by_template.get(template)

    def by_name(self, name: str) -> _T | None:
        return self._by_name.get(name.lower())

    def all(self) -> tuple:
        return self._items

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"<{self._kind}Registry: {len(self)} entries>"


# ---------------------------------------------------------------------------
# Parser: TypeScript object literal → Python dicts
# ---------------------------------------------------------------------------

_SUBMODULE_ROOT = Path(__file__).resolve().parents[3] / "tools" / "leek-wars" / "src" / "model"


def _extract_brace_block(text: str, start: int) -> str | None:
    """Extract a balanced {}-block starting at position `start` (which must be '{')."""
    if text[start] != "{":
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _parse_ts_objects(filepath: Path) -> list[dict]:
    """Parse a TypeScript file containing Object.freeze({...}) with object literals.

    Handles the format used in chips.ts and weapons.ts:
        '1': { id: 1, name: 'shock', ... },

    Uses brace-counting instead of regex to handle nested objects (effects arrays).
    """
    text = filepath.read_text()
    key_pattern = re.compile(r"'(\d+)':\s*\{")
    results = []
    for match in key_pattern.finditer(text):
        brace_start = match.end() - 1  # Position of the opening {
        obj_str = _extract_brace_block(text, brace_start)
        if obj_str is None:
            continue
        # Convert TS object literal to valid JSON:
        # 1. Quote unquoted keys: word: -> "word":
        json_str = re.sub(r"(\w+)\s*:", r'"\1":', obj_str)
        # 2. Replace single-quoted strings with double-quoted
        json_str = json_str.replace("'", '"')
        try:
            results.append(json.loads(json_str))
        except json.JSONDecodeError:
            continue  # Skip malformed entries
    return results


def _parse_effect(raw: dict) -> Effect:
    return Effect(
        id=raw["id"],
        value1=raw["value1"],
        value2=raw["value2"],
        turns=raw["turns"],
        targets=raw["targets"],
        modifiers=raw["modifiers"],
        type=raw["type"],
    )


def _load_chips() -> _Registry[Chip]:
    filepath = _SUBMODULE_ROOT / "chips.ts"
    if not filepath.exists():
        return _Registry([], "Chip")
    raw_list = _parse_ts_objects(filepath)
    chips = []
    for raw in raw_list:
        chips.append(Chip(
            id=raw["id"],
            name=raw["name"],
            template=raw["template"],
            level=raw["level"],
            cost=raw["cost"],
            min_range=raw["min_range"],
            max_range=raw["max_range"],
            cooldown=raw["cooldown"],
            initial_cooldown=raw.get("initial_cooldown", 0),
            los=raw["los"],
            area=raw["area"],
            max_uses=raw.get("max_uses", -1),
            type=raw["type"],
            effects=tuple(_parse_effect(e) for e in raw.get("effects", [])),
        ))
    return _Registry(chips, "Chip")


def _load_weapons() -> _Registry[Weapon]:
    filepath = _SUBMODULE_ROOT / "weapons.ts"
    if not filepath.exists():
        return _Registry([], "Weapon")
    raw_list = _parse_ts_objects(filepath)
    weapons = []
    for raw in raw_list:
        weapons.append(Weapon(
            id=raw["id"],
            name=raw["name"],
            template=raw["template"],
            item=raw["item"],
            level=raw["level"],
            cost=raw["cost"],
            min_range=raw["min_range"],
            max_range=raw["max_range"],
            los=raw["los"],
            area=raw["area"],
            max_uses=raw.get("max_uses", -1),
            forgotten=raw.get("forgotten", False),
            effects=tuple(_parse_effect(e) for e in raw.get("effects", [])),
            passive_effects=tuple(_parse_effect(e) for e in raw.get("passive_effects", [])),
        ))
    return _Registry(weapons, "Weapon")


# ---------------------------------------------------------------------------
# Module-level singletons — parsed once at import time
# ---------------------------------------------------------------------------

CHIP_REGISTRY: _Registry[Chip] = _load_chips()
WEAPON_REGISTRY: _Registry[Weapon] = _load_weapons()
