"""PySim fight engine — turn loop + game API bindings.

Creates game API functions as closures capturing entity/engine state,
injects them into the interpreter. The interpreter calls these when
running .leek code — it knows nothing about game mechanics.
"""

from __future__ import annotations

import random
from typing import Any, Callable

from .leekscript.lexer import tokenize
from .leekscript.parser import Parser, Program
from .leekscript.interpreter import Interpreter
from .grid import Grid
from .entity import Entity, ActiveEffect
from .effects import (
    calc_damage, calc_heal, calc_abs_shield, calc_rel_shield,
    calc_tp_shackle, calc_raw_tp_buff, roll_critical,
)

# Game constants (match Java generator)
USE_SUCCESS = 1
USE_FAILED = 2
USE_NOT_ENOUGH_TP = 3
USE_INVALID_TARGET = 4
USE_INVALID_POSITION = 5
USE_TOO_FAR = 6
USE_INVALID_COOLDOWN = 7

CELL_EMPTY = -1
CELL_OBSTACLE = -2

SET_WEAPON_COST = 1
MAX_TURNS = 64


class FightEngine:
    """Runs a PySim fight: two entities, each with a .leek AI, battle on a grid."""

    def __init__(self, grid: Grid, entities: list[Entity], seed: int = 42):
        self.grid = grid
        self.entities: dict[int, Entity] = {e.id: e for e in entities}
        self.entity_list = entities
        self.rng = random.Random(seed)
        self.turn = 0
        self.actions: list[list[Any]] = []
        self.debug_logs: dict[int, list[str]] = {e.id: [] for e in entities}
        self.interpreters: dict[int, Interpreter] = {}
        self.programs: dict[int, Program] = {}
        self._current_entity_id: int = 0

    def load_ai(self, entity_id: int, leek_source: str,
                source_path: str | None = None):
        """Parse .leek file and create interpreter for entity."""
        tokens = tokenize(leek_source)
        program = Parser(tokens).parse()
        self.programs[entity_id] = program

        api = self._build_game_api(entity_id)
        self.interpreters[entity_id] = Interpreter(
            game_api=api, source_path=source_path,
        )

    def _emit(self, *action):
        self.actions.append(list(action))

    def _entity_cells(self, exclude: int | None = None) -> set[int]:
        """Cells occupied by living entities, optionally excluding one."""
        return {e.cell for e in self.entities.values()
                if not e.dead and e.id != exclude}

    def _fight_over(self) -> bool:
        """Check if one team is eliminated."""
        teams_alive = set()
        for e in self.entities.values():
            if not e.dead:
                teams_alive.add(e.team)
        return len(teams_alive) < 2

    def _get_winner(self) -> int:
        """0=draw, 1=team1, 2=team2."""
        teams_alive = {}
        for e in self.entities.values():
            if not e.dead:
                teams_alive[e.team] = True
        if len(teams_alive) == 1:
            return next(iter(teams_alive))
        return 0  # draw

    # ── Game API factory ────────────────────────────────────────────

    def _build_game_api(self, entity_id: int) -> dict[str, Any]:
        """Build all game API functions for this entity as closures."""
        me = self.entities[entity_id]
        engine = self

        # ── State queries ───────────────────────────────────────────

        def getLife(target=None):
            if target is None:
                return me.life
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.life if t else 0

        def getTotalLife(target=None):
            if target is None:
                return me.max_life
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.max_life if t else 0

        def getTP(target=None):
            if target is None:
                return me.tp
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.tp if t else 0

        def getMP(target=None):
            if target is None:
                return me.mp
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.mp if t else 0

        def getCell(target=None):
            if target is None:
                return me.cell
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.cell if t else -1

        def getCellDistance(c1, c2):
            if c1 is None or c2 is None:
                return 999
            return engine.grid.distance(int(c1), int(c2))

        def getEntity():
            return me.id

        def getStrength():
            return me.strength

        def getAgility():
            return me.agility

        def getResistance():
            return me.resistance

        def getWisdom():
            return me.wisdom

        def getMagic():
            return me.magic

        def getFrequency():
            return me.frequency

        def getLevel():
            return me.level

        def getName(target=None):
            if target is None:
                return me.name
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.name if t else ""

        def getOperations():
            interp = engine.interpreters.get(entity_id)
            return interp.ops if interp else 0

        # ── Enemy queries ───────────────────────────────────────────

        def getEnemies():
            return [e.id for e in engine.entities.values()
                    if not e.dead and e.team != me.team]

        def getAllies():
            return [e.id for e in engine.entities.values()
                    if not e.dead and e.team == me.team and e.id != me.id]

        def getNearestEnemy():
            enemies = getEnemies()
            if not enemies:
                return None
            return min(enemies,
                       key=lambda eid: engine.grid.distance(me.cell, engine.entities[eid].cell))

        def isSummon(target=None):
            if target is None:
                return me.is_summon
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.is_summon if t else False

        def isDead(target=None):
            if target is None:
                return me.dead
            t = engine.entities.get(target if isinstance(target, int) else int(target))
            return t.dead if t else True

        def isAlive(target=None):
            return not isDead(target)

        # ── Weapon queries ──────────────────────────────────────────

        def getWeapon():
            if me.current_weapon is None:
                return None
            return me.current_weapon["id"]

        def getWeapons():
            return [w["id"] for w in me.weapons]

        def getWeaponCost(w_id=None):
            w = _find_weapon(w_id)
            return w["cost"] if w else 0

        def getWeaponMinRange(w_id=None):
            w = _find_weapon(w_id)
            return w["min_range"] if w else 0

        def getWeaponMaxRange(w_id=None):
            w = _find_weapon(w_id)
            return w["max_range"] if w else 0

        def getWeaponEffects(w_id=None):
            w = _find_weapon(w_id)
            if not w:
                return []
            # Return effects as arrays: [type, value1, value2, turns, targets, modifiers]
            return [[e["type"], e["value1"], e["value2"], e["turns"], e["targets"], e["modifiers"]]
                    for e in w.get("effects", [])]

        def _find_weapon(w_id=None):
            if w_id is None:
                return me.current_weapon
            w_id = int(w_id)
            for w in me.weapons:
                # LS constants use template IDs; also match on id for compat
                if w["template"] == w_id or w["id"] == w_id:
                    return w
            return None

        # ── Chip queries ────────────────────────────────────────────

        def getChips():
            return [c["id"] for c in me.chips]

        def getChipName(chip_id):
            chip_id = int(chip_id)
            for c in me.chips:
                if c["id"] == chip_id:
                    return c["name"]
            return ""

        def getChipCost(chip_id):
            c = _find_chip(chip_id)
            return c["cost"] if c else 0

        def getCooldown(chip_id):
            chip_id = int(chip_id)
            return me.cooldowns.get(chip_id, 0)

        def getChipMinRange(chip_id):
            c = _find_chip(chip_id)
            return c["min_range"] if c else 0

        def getChipMaxRange(chip_id):
            c = _find_chip(chip_id)
            return c["max_range"] if c else 0

        def getChipEffects(chip_id):
            c = _find_chip(chip_id)
            if not c:
                return []
            return [[e["type"], e["value1"], e["value2"], e["turns"], e["targets"], e["modifiers"]]
                    for e in c.get("effects", [])]

        def _find_chip(chip_id):
            if chip_id is None:
                return None
            chip_id = int(chip_id)
            for c in me.chips:
                # LS constants use template IDs; also match on id for compat
                if c["template"] == chip_id or c["id"] == chip_id:
                    return c
            return None

        # ── Map queries ─────────────────────────────────────────────

        def isEmptyCell(cell):
            cell = int(cell)
            if cell < 0 or cell >= Grid.CELLS:
                return False
            if cell in engine.grid.obstacles:
                return False
            # Check for entities on that cell
            for e in engine.entities.values():
                if not e.dead and e.cell == cell:
                    return False
            return True

        def getCellContent(cell):
            cell = int(cell)
            if cell < 0 or cell >= Grid.CELLS:
                return CELL_OBSTACLE
            if cell in engine.grid.obstacles:
                return CELL_OBSTACLE
            for e in engine.entities.values():
                if not e.dead and e.cell == cell:
                    return e.id
            return CELL_EMPTY

        def lineOfSight(c1, c2=None, ignore=None):
            if c2 is None:
                # lineOfSight(target) — from my cell
                c2 = c1
                c1 = me.cell
            c1, c2 = int(c1), int(c2)
            blocking = engine._entity_cells(exclude=me.id)
            # Don't block on start/end cells
            blocking.discard(c1)
            blocking.discard(c2)
            return engine.grid.line_of_sight(c1, c2, blocking)

        # ── Actions ─────────────────────────────────────────────────

        def setWeapon(w_id):
            w_id = int(w_id)
            w = _find_weapon(w_id)
            if w is None:
                return USE_FAILED
            if me.tp < SET_WEAPON_COST:
                return USE_NOT_ENOUGH_TP
            me.tp_used += SET_WEAPON_COST
            me.current_weapon = w
            engine._emit(13, w["template"])  # SET_WEAPON
            return USE_SUCCESS

        def useWeapon(target_id):
            target_id = int(target_id)
            target = engine.entities.get(target_id)
            if target is None or target.dead:
                return USE_INVALID_TARGET
            w = me.current_weapon
            if w is None:
                return USE_FAILED
            if me.tp < w["cost"]:
                return USE_NOT_ENOUGH_TP

            dist = engine.grid.distance(me.cell, target.cell)
            if dist < w["min_range"] or dist > w["max_range"]:
                return USE_INVALID_TARGET
            if w.get("los", True) and not engine.grid.line_of_sight(
                me.cell, target.cell, engine._entity_cells(exclude=me.id) - {target.cell}
            ):
                return USE_INVALID_TARGET

            me.tp_used += w["cost"]
            engine._emit(16, me.cell, [target_id])  # USE_WEAPON

            # Apply weapon effects
            for eff in w.get("effects", []):
                engine._apply_effect(eff, me, target)

            # Check kill
            if target.dead:
                engine._emit(11, target.id)  # KILL

            return USE_SUCCESS

        def useChip(chip_id, target_id):
            chip_id = int(chip_id)
            target_id = int(target_id)
            target = engine.entities.get(target_id)
            if target is None or target.dead:
                return USE_INVALID_TARGET

            c = _find_chip(chip_id)
            if c is None:
                return USE_FAILED
            if me.tp < c["cost"]:
                return USE_NOT_ENOUGH_TP
            if me.cooldowns.get(chip_id, 0) > 0:
                return USE_INVALID_COOLDOWN
            if c.get("max_uses", -1) > 0:
                uses = me.chip_fight_uses.get(chip_id, 0)
                if uses >= c["max_uses"]:
                    return USE_FAILED

            dist = engine.grid.distance(me.cell, target.cell)
            if dist < c["min_range"] or dist > c["max_range"]:
                return USE_INVALID_TARGET
            if c.get("los", True) and target_id != me.id:
                if not engine.grid.line_of_sight(
                    me.cell, target.cell, engine._entity_cells(exclude=me.id) - {target.cell}
                ):
                    return USE_INVALID_TARGET

            # Spend TP and track usage
            me.tp_used += c["cost"]
            me.chip_fight_uses[chip_id] = me.chip_fight_uses.get(chip_id, 0) + 1
            if c.get("cooldown", 0) > 0:
                me.cooldowns[chip_id] = c["cooldown"]

            engine._emit(12, c["template"], me.cell, 1)  # USE_CHIP, success

            # Apply chip effects
            for eff in c.get("effects", []):
                engine._apply_effect(eff, me, target)

            # Check kill
            if target.dead:
                engine._emit(11, target.id)  # KILL

            return USE_SUCCESS

        def moveToward(target, steps=None):
            """Move toward entity or cell. 1 MP per cell."""
            if isinstance(target, int) and target in engine.entities:
                target_cell = engine.entities[target].cell
            else:
                target_cell = int(target)

            max_steps = me.mp if steps is None else min(int(steps), me.mp)
            if max_steps <= 0:
                return 0

            blocked = engine._entity_cells(exclude=me.id)
            path = engine.grid.move_toward(me.cell, target_cell, max_steps, blocked)

            if path:
                me.mp_used += len(path)
                me.cell = path[-1]
                engine._emit(10, me.id, path)  # MOVE_TO

            return len(path)

        def moveTowardCell(cell, steps=None):
            cell = int(cell)
            max_steps = me.mp if steps is None else min(int(steps), me.mp)
            if max_steps <= 0:
                return 0

            blocked = engine._entity_cells(exclude=me.id)
            path = engine.grid.move_toward(me.cell, cell, max_steps, blocked)

            if path:
                me.mp_used += len(path)
                me.cell = path[-1]
                engine._emit(10, me.id, path)

            return len(path)

        def moveAwayFrom(target, steps=None):
            if isinstance(target, int) and target in engine.entities:
                target_cell = engine.entities[target].cell
            else:
                target_cell = int(target)

            max_steps = me.mp if steps is None else min(int(steps), me.mp)
            if max_steps <= 0:
                return 0

            blocked = engine._entity_cells(exclude=me.id)
            path = engine.grid.move_away_from(me.cell, target_cell, max_steps, blocked)

            if path:
                me.mp_used += len(path)
                me.cell = path[-1]
                engine._emit(10, me.id, path)

            return len(path)

        def moveAwayFromCell(cell, steps=None):
            return moveAwayFrom(int(cell), steps)

        def say(msg):
            engine._emit(203, me.id, str(msg))
            me.tp_used += 1  # say costs 1 TP
            return None

        # ── Build API dict ──────────────────────────────────────────

        api = {
            # State
            "getLife": getLife,
            "getTotalLife": getTotalLife,
            "getTP": getTP,
            "getMP": getMP,
            "getCell": getCell,
            "getCellDistance": getCellDistance,
            "getEntity": getEntity,
            "getStrength": getStrength,
            "getAgility": getAgility,
            "getResistance": getResistance,
            "getWisdom": getWisdom,
            "getMagic": getMagic,
            "getFrequency": getFrequency,
            "getLevel": getLevel,
            "getName": getName,
            "getOperations": getOperations,
            # Enemy
            "getEnemies": getEnemies,
            "getAllies": getAllies,
            "getNearestEnemy": getNearestEnemy,
            "isSummon": isSummon,
            "isDead": isDead,
            "isAlive": isAlive,
            # Weapon
            "getWeapon": getWeapon,
            "getWeapons": getWeapons,
            "getWeaponCost": getWeaponCost,
            "getWeaponMinRange": getWeaponMinRange,
            "getWeaponMaxRange": getWeaponMaxRange,
            "getWeaponEffects": getWeaponEffects,
            # Chip
            "getChips": getChips,
            "getChipName": getChipName,
            "getChipCost": getChipCost,
            "getCooldown": getCooldown,
            "getChipMinRange": getChipMinRange,
            "getChipMaxRange": getChipMaxRange,
            "getChipEffects": getChipEffects,
            # Map
            "isEmptyCell": isEmptyCell,
            "getCellContent": getCellContent,
            "lineOfSight": lineOfSight,
            # Actions
            "moveToward": moveToward,
            "moveTowardCell": moveTowardCell,
            "moveAwayFrom": moveAwayFrom,
            "moveAwayFromCell": moveAwayFromCell,
            "setWeapon": setWeapon,
            "useWeapon": useWeapon,
            "useChip": useChip,
            "say": say,
            # Constants
            "CELL_EMPTY": CELL_EMPTY,
            "CELL_OBSTACLE": CELL_OBSTACLE,
            "USE_SUCCESS": USE_SUCCESS,
            "USE_FAILED": USE_FAILED,
            "USE_NOT_ENOUGH_TP": USE_NOT_ENOUGH_TP,
            "USE_INVALID_TARGET": USE_INVALID_TARGET,
            "USE_INVALID_POSITION": USE_INVALID_POSITION,
            "USE_TOO_FAR": USE_TOO_FAR,
            "USE_INVALID_COOLDOWN": USE_INVALID_COOLDOWN,
            # Effect type constants
            "EFFECT_DAMAGE": 1,
            "EFFECT_HEAL": 2,
            "EFFECT_ABSOLUTE_SHIELD": 4,
            "EFFECT_BUFF_TP": 5,
            "EFFECT_RELATIVE_SHIELD": 6,
            "EFFECT_SHACKLE_TP": 15,
            # Entity type constants
            "ENTITY_LEEK": 1,
            "ENTITY_BULB": 2,
        }
        # Inject chip/weapon template constants (CHIP_SPARK, WEAPON_PISTOL, etc.)
        api.update(self._get_equipment_constants())
        return api

    _equipment_constants_cache: dict[str, int] | None = None

    @classmethod
    def _get_equipment_constants(cls) -> dict[str, int]:
        """Generate CHIP_* and WEAPON_* constants from equipment registry."""
        if cls._equipment_constants_cache is not None:
            return cls._equipment_constants_cache

        from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY

        constants: dict[str, int] = {}
        for chip in CHIP_REGISTRY._items:
            name = "CHIP_" + chip.name.upper().replace("-", "_").replace(" ", "_")
            constants[name] = chip.template
        for weapon in WEAPON_REGISTRY._items:
            name = "WEAPON_" + weapon.name.upper().replace("-", "_").replace(" ", "_")
            constants[name] = weapon.template

        cls._equipment_constants_cache = constants
        return constants

    # ── Effect application ──────────────────────────────────────────

    def _apply_effect(self, eff: dict, caster: Entity, target: Entity):
        """Apply a single effect from a weapon or chip."""
        eff_type = eff["type"]
        v1 = eff["value1"]
        v2 = eff["value2"]
        turns = eff.get("turns", 0)

        if eff_type == 1:  # Damage
            raw, crit = calc_damage(v1, v2, caster.strength, caster.agility, self.rng)
            actual = target.take_damage(raw)
            self._emit(101, target.id, actual)  # LOST_LIFE
            # Life steal: WIS/1000 of damage dealt
            if caster.wisdom > 0 and actual > 0:
                steal = int(actual * caster.wisdom / 1000)
                if steal > 0:
                    healed = caster.heal(steal)
                    if healed > 0:
                        self._emit(103, caster.id, healed)  # HEAL

        elif eff_type == 2:  # Heal
            raw, crit = calc_heal(v1, v2, caster.wisdom, caster.agility, self.rng)
            actual = target.heal(raw)
            self._emit(103, target.id, actual)  # HEAL

        elif eff_type == 4:  # Absolute shield
            value, crit = calc_abs_shield(v1, v2, caster.resistance, caster.agility, self.rng)
            target.add_effect(ActiveEffect("abs_shield", value, turns, caster.id))
            self._emit(14, target.id, 4, value, turns)  # STACK_EFFECT

        elif eff_type == 5:  # Buff (Whip = raw TP buff)
            tp_gained, crit = calc_raw_tp_buff(v1, v2, target.base_tp, caster.agility, self.rng)
            target.add_effect(ActiveEffect("tp_buff", tp_gained, turns, caster.id))
            self._emit(14, target.id, 5, tp_gained, turns)  # STACK_EFFECT

        elif eff_type == 6:  # Poison
            raw, crit = calc_damage(v1, v2, caster.magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("poison", raw, turns, caster.id))
            self._emit(14, target.id, 6, raw, turns)

        elif eff_type == 7:  # Debuff (Tranquilizer = TP shackle)
            tp_lost, crit = calc_tp_shackle(v1, v2, caster.magic, target.base_tp, caster.agility, self.rng)
            target.add_effect(ActiveEffect("tp_shackle", tp_lost, turns, caster.id))
            self._emit(100, target.id, tp_lost)  # LOST_PT (TP)

        elif eff_type == 3:  # Relative shield
            value, crit = calc_rel_shield(v1, v2, caster.resistance, caster.agility, self.rng)
            target.add_effect(ActiveEffect("rel_shield", value, turns, caster.id))
            self._emit(14, target.id, 3, value, turns)

        elif eff_type == 8:  # Raw buff strength
            target.add_effect(ActiveEffect("str_buff", v1, turns, caster.id))
            self._emit(14, target.id, 8, v1, turns)

    # ── Turn loop ───────────────────────────────────────────────────

    def run(self) -> dict:
        """Execute the full fight. Returns outcome dict."""
        # Determine turn order by frequency (higher = first)
        # Equal frequency → randomize (matches real game behavior)
        eids = [e.id for e in self.entity_list]
        self.rng.shuffle(eids)  # randomize before stable sort
        turn_order = sorted(
            eids,
            key=lambda eid: -self.entities[eid].frequency,
        )

        self._emit(0)  # START_FIGHT

        while self.turn < MAX_TURNS:
            self.turn += 1
            self._emit(6, self.turn)  # NEW_TURN

            for eid in turn_order:
                entity = self.entities[eid]
                if entity.dead:
                    continue

                entity.start_turn()
                self._current_entity_id = eid
                self._emit(7, eid)  # LEEK_TURN

                # Apply poison damage at turn start
                for eff in entity.effects:
                    if eff.effect_type == "poison":
                        actual = entity.take_damage(eff.value)
                        if actual > 0:
                            self._emit(110, entity.id, actual)  # POISON_DAMAGE
                        if entity.dead:
                            self._emit(11, entity.id)  # KILL
                            break

                if not entity.dead:
                    # Run the AI
                    interp = self.interpreters.get(eid)
                    program = self.programs.get(eid)
                    if interp and program:
                        try:
                            interp.run(program)
                        except Exception as exc:
                            # AI crashed — log and continue
                            self.debug_logs[eid].append(f"AI ERROR: {exc}")
                        # Collect debug output
                        self.debug_logs[eid].extend(interp.debug_log)
                        interp.debug_log.clear()

                entity.end_turn()
                self._emit(8, eid)  # END_TURN

                if self._fight_over():
                    break

            if self._fight_over():
                break

        winner = self._get_winner()
        self._emit(4, winner)  # END_FIGHT

        return {
            "winner": winner,
            "turns": self.turn,
            "actions": self.actions,
            "debug_logs": self.debug_logs,
        }
