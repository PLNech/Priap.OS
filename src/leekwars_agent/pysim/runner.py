"""PySim runner — bridges existing sim infrastructure to PySim fight engine.

Converts EntityConfig + equipment registry data into PySim Entity + weapon/chip
dicts that the engine understands.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .grid import Grid
from .entity import Entity
from .engine import FightEngine
from .maps import RealMapLibrary


def _build_weapon_dict(weapon) -> dict:
    """Convert equipment.Weapon to engine-compatible dict."""
    return {
        "id": weapon.id,
        "name": weapon.name,
        "template": weapon.template,
        "cost": weapon.cost,
        "min_range": weapon.min_range,
        "max_range": weapon.max_range,
        "los": weapon.los,
        "area": weapon.area,
        "max_uses": weapon.max_uses,
        "launch_type": weapon.launch_type,
        "effects": [
            {
                "type": e.type,
                "value1": e.value1,
                "value2": e.value2,
                "turns": e.turns,
                "targets": e.targets,
                "modifiers": e.modifiers,
            }
            for e in weapon.effects
        ],
    }


def _build_chip_dict(chip) -> dict:
    """Convert equipment.Chip to engine-compatible dict."""
    return {
        "id": chip.id,
        "name": chip.name,
        "template": chip.template,
        "cost": chip.cost,
        "min_range": chip.min_range,
        "max_range": chip.max_range,
        "cooldown": chip.cooldown,
        "initial_cooldown": chip.initial_cooldown,
        "los": chip.los,
        "area": chip.area,
        "max_uses": chip.max_uses,
        "launch_type": chip.launch_type,
        "effects": [
            {
                "type": e.type,
                "value1": e.value1,
                "value2": e.value2,
                "turns": e.turns,
                "targets": e.targets,
                "modifiers": e.modifiers,
            }
            for e in chip.effects
        ],
    }


class PySimRunner:
    """Run PySim fights using existing infrastructure (EntityConfig, equipment registry)."""

    def __init__(self):
        # Lazy-load equipment registry and map library
        self._chip_reg = None
        self._weapon_reg = None
        self._map_lib: RealMapLibrary | None = None

    def _load_registries(self):
        if self._chip_reg is None:
            from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY
            self._chip_reg = CHIP_REGISTRY
            self._weapon_reg = WEAPON_REGISTRY

    def _get_map_lib(self) -> RealMapLibrary:
        if self._map_lib is None:
            self._map_lib = RealMapLibrary()
        return self._map_lib

    def _resolve_weapons(self, weapon_ids: list[int]) -> list[dict]:
        """Resolve weapon item/id/template IDs to engine weapon dicts."""
        weapons = []
        for wid in weapon_ids:
            w = self._weapon_reg.by_item(wid)
            if w is None:
                w = self._weapon_reg.by_id(wid)
            if w is None:
                w = self._weapon_reg.by_template(wid)
            if w:
                weapons.append(_build_weapon_dict(w))
        return weapons

    def _resolve_chips(self, chip_ids: list[int]) -> list[dict]:
        """Resolve chip IDs to engine chip dicts."""
        chips = []
        for cid in chip_ids:
            c = self._chip_reg.by_id(cid)
            if c:
                chips.append(_build_chip_dict(c))
        return chips

    def run_1v1(
        self,
        ai1_path: str | Path,
        ai2_path: str | Path,
        *,
        level: int = 146,
        life: int = 1099,
        tp: int = 14,
        mp: int = 4,
        strength: int = 452,
        agility: int = 10,
        resistance: int = 219,
        wisdom: int = 40,
        magic: int = 0,
        frequency: int = 140,
        weapon_ids: list[int] | None = None,
        chip_ids: list[int] | None = None,
        chip_ids_2: list[int] | None = None,
        weapon_ids_2: list[int] | None = None,
        seed: int = 42,
        obstacles: set[int] | None = None,
        spawn1: int | None = None,
        spawn2: int | None = None,
        use_real_maps: bool = True,
    ) -> dict:
        """Run a 1v1 fight (same stats, optionally different equipment).

        Args:
            ai1_path: Path to team 1's .leek file
            ai2_path: Path to team 2's .leek file
            weapon_ids: Weapon IDs for team 1 (and team 2 unless overridden).
            chip_ids: Chip IDs for team 1 (and team 2 unless overridden).
            weapon_ids_2: Weapon IDs for team 2 only (for A/B tests).
            chip_ids_2: Chip IDs for team 2 only (for A/B tests).
            seed: RNG seed for deterministic fights.
            spawn1/spawn2: Starting cell IDs on diamond grid.

        Returns:
            Fight outcome dict with winner, turns, actions, debug_logs.
        """
        self._load_registries()

        # Default equipment: our current build
        if weapon_ids is None:
            weapon_ids = [45, 42, 60]  # Magnum, Laser, b_laser
        if chip_ids is None:
            chip_ids = [94, 5, 22, 88, 20, 21]  # Tranq, Flame, Armor, Whip, Shield, Helmet

        weapons1 = self._resolve_weapons(weapon_ids)
        chips1 = self._resolve_chips(chip_ids)

        # Team 2: use overrides if provided, otherwise same as team 1
        weapons2 = self._resolve_weapons(weapon_ids_2) if weapon_ids_2 else weapons1
        chips2 = self._resolve_chips(chip_ids_2) if chip_ids_2 else chips1

        # Create entities
        e1 = Entity(
            id=1, name="Entity1", team=1, farmer=1, level=level,
            life=life, tp=tp, mp=mp, strength=strength, agility=agility,
            resistance=resistance, wisdom=wisdom, magic=magic, frequency=frequency,
            weapons=weapons1, chips=chips1,
        )
        e2 = Entity(
            id=2, name="Entity2", team=2, farmer=2, level=level,
            life=life, tp=tp, mp=mp, strength=strength, agility=agility,
            resistance=resistance, wisdom=wisdom, magic=magic, frequency=frequency,
            weapons=weapons2, chips=chips2,
        )

        # Resolve map: real map from DB, explicit params, or defaults
        if obstacles is not None or (spawn1 is not None and spawn2 is not None):
            # Explicit map parameters
            grid_obstacles = obstacles or set()
            s1 = spawn1 if spawn1 is not None else 100
            s2 = spawn2 if spawn2 is not None else 450
        elif use_real_maps:
            # Sample a real map from our fight database
            map_lib = self._get_map_lib()
            fight_map = map_lib.get_map(seed)  # deterministic by seed
            grid_obstacles = fight_map.obstacle_set
            s1 = fight_map.spawn1
            s2 = fight_map.spawn2
        else:
            # Fallback: empty map, fixed spawns
            grid_obstacles = set()
            s1 = 100
            s2 = 450

        e1.cell = s1
        e2.cell = s2
        grid = Grid(18, 18, obstacles=grid_obstacles)

        # Create engine
        engine = FightEngine(grid, [e1, e2], seed=seed)

        # Load AI files
        ai1_source = Path(ai1_path).read_text(errors="replace")
        ai2_source = Path(ai2_path).read_text(errors="replace")
        engine.load_ai(1, ai1_source, source_path=str(ai1_path))
        engine.load_ai(2, ai2_source, source_path=str(ai2_path))

        # Run fight
        self._last_engine = engine  # expose for debugging/diagnostics
        return engine.run()
