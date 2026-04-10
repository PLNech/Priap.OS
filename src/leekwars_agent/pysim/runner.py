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
        "item": weapon.item,  # constants.ts value (WEAPON_B_LASER = 60)
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
                "id": e.id,        # Effect type constant (Effect.TYPE_* = EFFECT_*)
                "type": e.type,    # Chip category (kept for backwards compat)
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
    """Convert equipment.Chip to engine-compatible dict.

    Note: for chips, constants.ts CHIP_* = chip.id (same as registry id).
    No 'item' field needed — unlike weapons where constants.ts uses item_id.
    """
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
                "id": e.id,        # Effect type constant (Effect.TYPE_* = EFFECT_*)
                "type": e.type,    # Chip category (kept for backwards compat)
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

    def _all_weapons(self) -> list[dict]:
        """Return ALL weapons from registry — for opponent AIs that may use any weapon."""
        return [_build_weapon_dict(w) for w in self._weapon_reg._items]

    def _all_chips(self) -> list[dict]:
        """Return ALL chips from registry — for opponent AIs that may use any chip."""
        return [_build_chip_dict(c) for c in self._chip_reg._items]

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
        science: int = 0,
        power: int = 0,
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

        # Equipment: give ALL weapons and chips to both entities.
        # Each AI's code decides what to use via setWeapon()/useChip().
        # This prevents false negatives where an AI calls setWeapon(WEAPON_SHOTGUN)
        # but the entity doesn't have it in their inventory.
        all_weapons = self._all_weapons()
        all_chips = self._all_chips()

        # Allow overrides for specific A/B tests (e.g., Whip vs no-Whip)
        weapons1 = self._resolve_weapons(weapon_ids) if weapon_ids is not None else all_weapons
        chips1 = self._resolve_chips(chip_ids) if chip_ids is not None else all_chips
        weapons2 = self._resolve_weapons(weapon_ids_2) if weapon_ids_2 is not None else weapons1
        chips2 = self._resolve_chips(chip_ids_2) if chip_ids_2 is not None else chips1

        # Create entities
        e1 = Entity(
            id=1, name="Entity1", team=1, farmer=1, level=level,
            life=life, tp=tp, mp=mp, strength=strength, agility=agility,
            resistance=resistance, wisdom=wisdom, magic=magic,
            science=science, power=power, frequency=frequency,
            weapons=weapons1, chips=chips1,
        )
        e2 = Entity(
            id=2, name="Entity2", team=2, farmer=2, level=level,
            life=life, tp=tp, mp=mp, strength=strength, agility=agility,
            resistance=resistance, wisdom=wisdom, magic=magic,
            science=science, power=power, frequency=frequency,
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

    def setup_from_fight(
        self,
        fight_data: dict,
        ai_path: str | Path,
        *,
        ai_path_2: str | Path | None = None,
        seed: int | None = None,
    ) -> FightEngine:
        """Create a PySim engine matching a real fight's initial conditions.

        Parses the fight JSON (from API) to extract:
        - Map: width, height, obstacles, entity spawn positions
        - Entity stats: life, TP, MP, STR, AGI, RES, WIS, MAG, SCI, frequency
        - Equipment: via all-weapons/all-chips (since we can't know exact loadout)

        Returns an initialized FightEngine ready for run() or step_turn().
        Use engine.snapshot() to inspect, engine.step_turn() to single-step,
        or engine.run() for full fight.

        Args:
            fight_data: Full fight JSON from API (with 'data' key containing leeks, map, actions)
            ai_path: Path to .leek file for entity 0 (team 1)
            ai_path_2: Path to .leek file for entity 1 (team 2). Defaults to ai_path.
            seed: RNG seed override (default: from fight data if available)
        """
        self._load_registries()
        data = fight_data.get("data", fight_data)

        # Parse map
        map_info = data.get("map", {})
        width = map_info.get("width", 18)
        height = map_info.get("height", 18)
        obstacle_dict = map_info.get("obstacles", {})
        obstacle_cells = {int(k) for k in obstacle_dict}

        # Parse entities
        leeks = data.get("leeks", [])
        all_weapons = self._all_weapons()
        all_chips = self._all_chips()

        entities = []
        for lk in leeks:
            e = Entity(
                id=lk["id"],
                name=lk.get("name", f"Entity{lk['id']}"),
                team=lk.get("team", 1),
                farmer=lk.get("farmer", lk["id"]),
                level=lk.get("level", 1),
                life=lk.get("life", 100),
                tp=lk.get("tp", 10),
                mp=lk.get("mp", 3),
                strength=lk.get("strength", 0),
                agility=lk.get("agility", 0),
                resistance=lk.get("resistance", 0),
                wisdom=lk.get("wisdom", 0),
                magic=lk.get("magic", 0),
                science=lk.get("science", 0),
                power=lk.get("power", 0),
                frequency=lk.get("frequency", 100),
                weapons=all_weapons,
                chips=all_chips,
            )
            e.cell = lk.get("cellPos", 0)
            entities.append(e)

        grid = Grid(width, height, obstacles=obstacle_cells)
        fight_seed = seed or fight_data.get("seed", 42)
        engine = FightEngine(grid, entities, seed=fight_seed)

        # Load AI files
        ai1_source = Path(ai_path).read_text(errors="replace")
        ai2_source = Path(ai_path_2 or ai_path).read_text(errors="replace")
        if len(entities) >= 1:
            engine.load_ai(entities[0].id, ai1_source, source_path=str(ai_path))
        if len(entities) >= 2:
            engine.load_ai(entities[1].id, ai2_source,
                           source_path=str(ai_path_2 or ai_path))

        self._last_engine = engine
        return engine

    def replay_and_compare(
        self,
        fight_data: dict,
        ai_path: str | Path,
        *,
        ai_path_2: str | Path | None = None,
        damage_tolerance: int = 5,
    ) -> dict:
        """Replay a real fight in PySim and compare action sequences.

        Returns:
            {
                "real_winner": int, "pysim_winner": int,
                "real_turns": int, "pysim_turns": int,
                "divergences": list[dict],  # from FightEngine.compare_actions
                "pysim_snapshot": dict,  # final state
            }
        """
        data = fight_data.get("data", fight_data)
        real_actions = data.get("actions", [])

        engine = self.setup_from_fight(fight_data, ai_path, ai_path_2=ai_path_2)
        result = engine.run()

        divergences = FightEngine.compare_actions(
            real_actions, result["actions"],
            damage_tolerance=damage_tolerance,
        )

        return {
            "real_winner": fight_data.get("winner", 0),
            "pysim_winner": result["winner"],
            "real_turns": sum(1 for a in real_actions if a[0] == 6),
            "pysim_turns": result["turns"],
            "divergences": divergences,
            "pysim_snapshot": engine.snapshot(),
        }
