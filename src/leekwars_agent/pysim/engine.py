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
from .leekscript.interpreter import Interpreter, OpsLimitExceeded, MAX_OPS
from .grid import Grid
from .entity import Entity, ActiveEffect
from .effects import (
    calc_damage, calc_heal, calc_abs_shield, calc_rel_shield,
    calc_tp_shackle, calc_raw_tp_buff, roll_critical,
    calc_stat_shackle, calc_stat_buff, calc_vulnerability, calc_damage_return,
)
from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY
from . import constants as game_constants

# Game constants — parsed from constants.ts (verified against Java source)
USE_SUCCESS = game_constants.get("USE_SUCCESS")             # 1
USE_FAILED = game_constants.get("USE_FAILED")               # 0
USE_NOT_ENOUGH_TP = game_constants.get("USE_NOT_ENOUGH_TP") # -2
USE_INVALID_TARGET = game_constants.get("USE_INVALID_TARGET") # -1
USE_INVALID_POSITION = game_constants.get("USE_INVALID_POSITION") # -4
USE_INVALID_COOLDOWN = game_constants.get("USE_INVALID_COOLDOWN") # -3
USE_TOO_FAR = -6  # not in constants.ts, rarely used

# Cell content values exposed to AI code (from constants.ts)
CELL_EMPTY = game_constants.get("CELL_EMPTY")      # 0
CELL_OBSTACLE = game_constants.get("CELL_OBSTACLE")  # 2
CELL_ENTITY = game_constants.get("CELL_ENTITY")      # 1

SET_WEAPON_COST = 1
MAX_TURNS = 64


def _safe_int(val, default=0):
    """Convert value to int, handling None and non-numeric gracefully."""
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


# Operations costs per API function (from FightFunctions.java)
# Maps function name → ops cost. Unlisted functions default to 15.
API_OPS_COSTS: dict[str, int] = {
    # Cheap queries (5)
    "getCell": 5, "getEntity": 5, "getLeek": 5, "getCellX": 5, "getCellY": 5,
    "getCellFromXY": 5, "getMapType": 5, "getFightID": 5, "getSide": 5,
    # Standard queries (10-15)
    "getLife": 15, "getTotalLife": 15, "getTP": 15, "getMP": 15,
    "getStrength": 15, "getAgility": 15, "getResistance": 15,
    "getWisdom": 15, "getMagic": 15, "getFrequency": 15, "getLevel": 15,
    "getName": 15, "getWeapon": 15, "getCellDistance": 15, "getDistance": 15,
    "getFarmerID": 15, "getFarmerName": 15, "getType": 15, "getWeaponCost": 15,
    "getWeaponMinRange": 15, "getWeaponMaxRange": 15, "getWeaponName": 15,
    "getWeaponLaunchType": 15, "getChipName": 15, "getChipCost": 15,
    "getChipMinRange": 15, "getChipMaxRange": 15, "getChipCooldown": 15,
    "getChipLaunchType": 15, "isWeapon": 15, "isObstacle": 10,
    "isEmptyCell": 10, "isOnSameLine": 15, "isInlineWeapon": 10,
    "weaponNeedLos": 10, "chipNeedLos": 10, "isSummon": 10,
    "isDead": 15, "isAlive": 15, "isLeek": 10, "isEntity": 10,
    "getLeekOnCell": 15, "getEntityOnCell": 15, "getCellContent": 6,
    "getTurn": 15, "getOperations": 5,
    # Medium queries (25-50)
    "getNearestEnemy": 25, "getAliveEnemiesCount": 25, "getAliveAlliesCount": 25,
    "getCooldown": 30, "getEffects": 25, "getEntityTurnOrder": 30,
    "lineOfSight": 31, "say": 30,
    # Expensive queries (40-125)
    "getWeapons": 50, "getChips": 40, "getWeaponEffects": 125,
    "getChipEffects": 125, "canUseWeapon": 45, "canUseWeaponOnCell": 45,
    "canUseChip": 45, "canUseChipOnCell": 45, "getWeaponTargets": 40,
    "getChipTargets": 40,
    "getEnemies": 100, "getAllies": 100, "getAliveEnemies": 100,
    "getAliveAllies": 100,
    # Movement (500 each)
    "moveToward": 500, "moveTowardCell": 500, "moveAwayFrom": 500,
    "moveAwayFromCell": 500, "moveTowardLine": 500,
    # Combat (3000 each)
    "useWeapon": 3000, "useChip": 3000,
    # Spatial queries (very expensive)
    "getCellsToUseWeapon": 25834, "getCellsToUseWeaponOnCell": 25834,
    "getCellsToUseChip": 25834, "getCellsToUseChipOnCell": 25834,
    "getCellToUseWeapon": 38080, "getCellToUseChip": 38080,
    # Mark/visual (164)
    "mark": 164, "markText": 164,
    # getPathLength: base 100, plus distance²×20 (charged dynamically)
    "getPathLength": 100, "getPath": 100,
}


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
            t = engine.entities.get(_safe_int(target))
            return t.life if t else 0

        def getTotalLife(target=None):
            if target is None:
                return me.max_life
            t = engine.entities.get(_safe_int(target))
            return t.max_life if t else 0

        def getTP(target=None):
            if target is None:
                return me.tp
            t = engine.entities.get(_safe_int(target))
            return t.tp if t else 0

        def getMP(target=None):
            if target is None:
                return me.mp
            t = engine.entities.get(_safe_int(target))
            return t.mp if t else 0

        def getCell(target=None):
            if target is None:
                return me.cell
            t = engine.entities.get(_safe_int(target))
            return t.cell if t else -1

        def getCellDistance(c1, c2):
            if c1 is None or c2 is None:
                return 999
            return engine.grid.distance(_safe_int(c1), _safe_int(c2))

        def getEntity():
            return me.id

        def _stat_getter(attr):
            """Factory for stat getters with optional target param."""
            def getter(target=None):
                if target is None:
                    return getattr(me, attr)
                t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
                return getattr(t, attr, 0) if t else 0
            return getter

        getStrength = _stat_getter("strength")
        getAgility = _stat_getter("agility")
        getResistance = _stat_getter("resistance")
        getWisdom = _stat_getter("wisdom")
        getMagic = _stat_getter("magic")
        getFrequency = _stat_getter("frequency")
        getLevel = _stat_getter("level")

        def getName(target=None):
            if target is None:
                return me.name
            t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
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
            t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
            return t.is_summon if t else False

        def isDead(target=None):
            if target is None:
                return me.dead
            t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
            return t.dead if t else True

        def isAlive(target=None):
            return not isDead(target)

        # ── Weapon queries ──────────────────────────────────────────

        def getWeapon(target=None):
            if target is None:
                if me.current_weapon is None:
                    return None
                return me.current_weapon["id"]
            t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
            if t is None or t.current_weapon is None:
                return None
            return t.current_weapon["id"]

        def getWeapons(target=None):
            if target is None:
                return [w["id"] for w in me.weapons]
            t = engine.entities.get(_safe_int(target))
            return [w["id"] for w in t.weapons] if t else []

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
            # Java: [id, value1, value1+value2, turns, targets, modifiers]
            # id = effect type constant (Effect.TYPE_*), NOT category
            # [2] = max value (v1+v2), NOT raw v2
            return [[e["id"], e["value1"], e["value1"] + e["value2"], e["turns"], e["targets"], e["modifiers"]]
                    for e in w.get("effects", [])]

        def _find_weapon(w_id=None):
            if w_id is None:
                return me.current_weapon
            w_id = _safe_int(w_id)
            for w in me.weapons:
                # LS constants use template IDs; also match on id for compat
                if w["template"] == w_id or w["id"] == w_id:
                    return w
            # Fallback: look up in global registry by template (e.g. WEAPON_PISTOL
            # is always equippable — every leek starts with one in the real game)
            try:
                from leekwars_agent.models.equipment import WEAPON_REGISTRY
                from .runner import _build_weapon_dict
                reg_w = WEAPON_REGISTRY.by_template(w_id)
                if reg_w is not None:
                    return _build_weapon_dict(reg_w)
            except Exception:
                pass
            return None

        # ── Chip queries ────────────────────────────────────────────

        def getChips(target=None):
            if target is None:
                return [c["id"] for c in me.chips]
            t = engine.entities.get(_safe_int(target))
            return [c["id"] for c in t.chips] if t else []

        def getChipName(chip_id):
            chip_id = _safe_int(chip_id)
            for c in me.chips:
                if c["id"] == chip_id:
                    return c["name"]
            return ""

        def getChipCost(chip_id):
            c = _find_chip(chip_id)
            return c["cost"] if c else 0

        def getCooldown(chip_id, target=None):
            """Get remaining cooldown for a chip. target param ignored (always checks own cooldowns)."""
            chip_id = _safe_int(chip_id)
            if target is not None:
                t = engine.entities.get(_safe_int(target))
                if t:
                    return t.cooldowns.get(chip_id, 0)
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
            # Java: [id, value1, value1+value2, turns, targets, modifiers]
            return [[e["id"], e["value1"], e["value1"] + e["value2"], e["turns"], e["targets"], e["modifiers"]]
                    for e in c.get("effects", [])]

        def _find_chip(chip_id):
            if chip_id is None:
                return None
            chip_id = _safe_int(chip_id)
            for c in me.chips:
                # LS constants use template IDs; also match on id for compat
                if c["template"] == chip_id or c["id"] == chip_id:
                    return c
            return None

        def getChipMaxUses(chip_id):
            c = _find_chip(chip_id)
            return c.get("max_uses", -1) if c else -1

        def getChipInitialCooldown(chip_id):
            c = _find_chip(chip_id)
            return c.get("initial_cooldown", 0) if c else 0

        def getWeaponMaxUses(w_id=None):
            w = _find_weapon(w_id)
            return w.get("max_uses", -1) if w else -1

        def getWeaponLaunchType(w_id=None):
            w = _find_weapon(w_id)
            return w.get("launch_type", 1) if w else 1

        def getChipLaunchType(chip_id):
            c = _find_chip(chip_id)
            return c.get("launch_type", 1) if c else 1

        def getAllChips(target=None):
            """Get all chip template IDs (same as getChips but using templates)."""
            if target is None:
                return [c["template"] for c in me.chips]
            t = engine.entities.get(_safe_int(target))
            return [c["template"] for c in t.chips] if t else []

        def getAllWeapons(target=None):
            """Get all weapon template IDs."""
            if target is None:
                return [w["template"] for w in me.weapons]
            t = engine.entities.get(_safe_int(target))
            return [w["template"] for w in t.weapons] if t else []

        def getCores(target=None):
            """Get entity cores (determines ops budget). Default 1 in sim."""
            return 1

        def getRAM(target=None):
            """Get entity RAM (determines max chip slots). Default 6 in sim."""
            return 6

        def getStates(target=None):
            """Get entity state bitfield. Returns list of active state IDs."""
            if target is None:
                return list(me.states) if hasattr(me, 'states') and me.states else []
            t = engine.entities.get(_safe_int(target))
            if t and hasattr(t, 'states') and t.states:
                return list(t.states)
            return []

        # ── Summons ────────────────────────────────────────────────

        def getSummons(target=None):
            """Get summon entity IDs — always empty in our sim (no summon support)."""
            return []

        # ── Registers (persistent AI state) ────────────────────────

        _registers = {}

        def getRegister(key):
            return _registers.get(str(key))

        def setRegister(key, value):
            _registers[str(key)] = str(value) if value is not None else None

        # ── Resource monitoring ────────────────────────────────────

        def getUsedRAM():
            return 0  # Not tracked in sim

        def getMaxRAM():
            return 100  # Default RAM

        def getMaxOperations():
            return MAX_OPS

        def pause():
            pass  # no-op in sim

        def getInstructionsCount():
            return 0

        def getBirthTurn(target=None):
            """Turn entity was created. 0 for leeks, summon turn for bulbs."""
            return 0

        def addOperation(*args):
            """No-op — internal debug counter, not meaningful in sim."""
            pass

        # ── Map queries ─────────────────────────────────────────────

        def isEmptyCell(cell):
            cell = _safe_int(cell)
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
            cell = _safe_int(cell)
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
            c1, c2 = _safe_int(c1), _safe_int(c2)
            blocking = engine._entity_cells(exclude=me.id)
            # Don't block on start/end cells
            blocking.discard(c1)
            blocking.discard(c2)
            return engine.grid.line_of_sight(c1, c2, blocking)

        # ── Actions ─────────────────────────────────────────────────

        def setWeapon(w_id):
            w_id = _safe_int(w_id)
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
            target_id = _safe_int(target_id)
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
            chip_id = _safe_int(chip_id)
            target_id = _safe_int(target_id)
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
            if target is None:
                return 0
            target = _safe_int(target)
            if target in engine.entities:
                target_cell = engine.entities[target].cell
            else:
                target_cell = target

            max_steps = me.mp if steps is None else min(_safe_int(steps), me.mp)
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
            if cell is None:
                return 0
            cell = _safe_int(cell)
            max_steps = me.mp if steps is None else min(_safe_int(steps), me.mp)
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
            if target is None:
                return 0
            target = _safe_int(target)
            if target in engine.entities:
                target_cell = engine.entities[target].cell
            else:
                target_cell = target

            max_steps = me.mp if steps is None else min(_safe_int(steps), me.mp)
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
            if cell is None:
                return 0
            return moveAwayFrom(_safe_int(cell), steps)

        def say(msg):
            engine._emit(203, me.id, str(msg))
            me.tp_used += 1  # say costs 1 TP
            return None

        # ── Turn / identity ─────────────────────────────────────────

        def getTurn():
            return engine.turn

        def getLeek():
            return me.id

        def getFarmerID(target=None):
            if target is None:
                return me.farmer
            t = engine.entities.get(_safe_int(target))
            return t.farmer if t else 0

        def getFarmerName(target=None):
            if target is None:
                return me.name
            t = engine.entities.get(_safe_int(target))
            return t.name if t else ""

        def getType(target=None):
            if target is None:
                return 2 if me.is_summon else 1  # ENTITY_LEEK=1, ENTITY_BULB=2
            t = engine.entities.get(target if isinstance(target, int) else _safe_int(target))
            if t is None:
                return 0
            return 2 if t.is_summon else 1

        # ── Alive entity queries ────────────────────────────────────

        def getAliveEnemies():
            return getEnemies()

        def getAliveAllies():
            return getAllies()

        def getAliveEnemiesCount():
            return len(getEnemies())

        def getAliveAlliesCount():
            return len(getAllies())

        # ── Grid coordinate helpers ─────────────────────────────────

        def getCellX(cell):
            cell = _safe_int(cell)
            if cell < 0 or cell >= engine.grid.nb_cells:
                return None
            # Java: cell.getX() - map.getWidth() + 1
            return engine.grid._x[cell] - engine.grid.width + 1

        def getCellY(cell):
            cell = _safe_int(cell)
            if cell < 0 or cell >= engine.grid.nb_cells:
                return None
            return engine.grid._y[cell]

        def getCellFromXY(x, y):
            # Java: getCell(x + width - 1, y) — converts user coords to internal
            x_internal = _safe_int(x) + engine.grid.width - 1
            cell = engine.grid._xy_to_cell(x_internal, _safe_int(y))
            return cell  # None if invalid

        def isObstacle(cell):
            cell = _safe_int(cell)
            if cell < 0 or cell >= engine.grid.nb_cells:
                return True
            return cell in engine.grid.obstacles

        def isOnSameLine(c1, c2):
            return engine.grid.is_on_same_line(_safe_int(c1), _safe_int(c2))

        # ── Weapon introspection ────────────────────────────────────

        def getWeaponName(w_id=None):
            w = _find_weapon(w_id)
            return w["name"] if w else ""

        def isInlineWeapon(w_id=None):
            w = _find_weapon(w_id)
            if w is None:
                return False
            return w.get("launch_type", 7) == 1

        def weaponNeedLos(w_id=None):
            w = _find_weapon(w_id)
            if w is None:
                return False
            return w.get("los", True)

        def isWeapon(tool_id):
            """Check if a template ID belongs to a weapon (not a chip)."""
            if tool_id is None:
                return False
            tool_id = _safe_int(tool_id)
            return WEAPON_REGISTRY.by_template(tool_id) is not None

        def getWeaponLaunchType(w_id=None):
            w = _find_weapon(w_id)
            if w is None:
                return None
            return w.get("launch_type", 7)

        # ── Chip introspection ──────────────────────────────────────

        def getChipCooldown(chip_id):
            """Initial cooldown (not current remaining). Matches ChipClass.getChipCooldown."""
            c = _find_chip(chip_id)
            return c["cooldown"] if c else 0

        def chipNeedLos(chip_id):
            c = _find_chip(chip_id)
            if c is None:
                return False
            return c.get("los", True)

        def getChipLaunchType(chip_id):
            c = _find_chip(chip_id)
            if c is None:
                return None
            return c.get("launch_type", 7)

        # ── Composite can-use checks ────────────────────────────────

        def canUseWeapon(value1, value2=None):
            """canUseWeapon(target) or canUseWeapon(weapon, target)."""
            if value2 is None:
                target_id = _safe_int(value1)
                weapon = me.current_weapon
            else:
                weapon = _find_weapon(_safe_int(value1))
                target_id = _safe_int(value2)
            if weapon is None:
                return False
            target = engine.entities.get(target_id)
            if target is None or target.dead:
                return False
            blocking = engine._entity_cells(exclude=me.id) - {target.cell}
            return engine.grid.can_use_attack(
                me.cell, target.cell,
                weapon["min_range"], weapon["max_range"],
                weapon.get("los", True), weapon.get("launch_type", 7),
                blocking,
            )

        def canUseWeaponOnCell(value1, value2=None):
            """canUseWeaponOnCell(cell) or canUseWeaponOnCell(weapon, cell)."""
            if value2 is None:
                target_cell = _safe_int(value1)
                weapon = me.current_weapon
            else:
                weapon = _find_weapon(_safe_int(value1))
                target_cell = _safe_int(value2)
            if weapon is None:
                return False
            if target_cell < 0 or target_cell >= engine.grid.nb_cells:
                return False
            blocking = engine._entity_cells(exclude=me.id) - {target_cell}
            return engine.grid.can_use_attack(
                me.cell, target_cell,
                weapon["min_range"], weapon["max_range"],
                weapon.get("los", True), weapon.get("launch_type", 7),
                blocking,
            )

        def canUseChip(chip_id, target_id):
            c = _find_chip(chip_id)
            if c is None or target_id is None:
                return False
            target = engine.entities.get(_safe_int(target_id))
            if target is None or target.dead:
                return False
            blocking = engine._entity_cells(exclude=me.id) - {target.cell}
            return engine.grid.can_use_attack(
                me.cell, target.cell,
                c["min_range"], c["max_range"],
                c.get("los", True), c.get("launch_type", 7),
                blocking,
            )

        def canUseChipOnCell(chip_id, cell):
            c = _find_chip(chip_id)
            if c is None:
                return False
            cell = _safe_int(cell)
            if cell < 0 or cell >= engine.grid.nb_cells:
                return False
            blocking = engine._entity_cells(exclude=me.id) - {cell}
            return engine.grid.can_use_attack(
                me.cell, cell,
                c["min_range"], c["max_range"],
                c.get("los", True), c.get("launch_type", 7),
                blocking,
            )

        # ── Spatial queries ─────────────────────────────────────────

        def getCellsToUseWeapon(value1, value2=None, value3=None):
            """getCellsToUseWeapon(target) or getCellsToUseWeapon(weapon, target)."""
            if value2 is None:
                target_id = _safe_int(value1)
                weapon = me.current_weapon
            else:
                weapon = _find_weapon(_safe_int(value1))
                target_id = _safe_int(value2)
            if weapon is None:
                return None
            target = engine.entities.get(target_id)
            if target is None or target.dead:
                return None

            ignore = {me.cell}
            if isinstance(value3, list):
                ignore = set(_safe_int(c) for c in value3)

            blocking = engine._entity_cells(exclude=me.id) - {target.cell}
            return engine.grid.get_possible_cast_cells(
                target.cell,
                weapon["min_range"], weapon["max_range"],
                weapon.get("los", True), weapon.get("launch_type", 7),
                ignore, blocking,
            )

        def getCellsToUseWeaponOnCell(value1, value2=None, value3=None):
            if value2 is None:
                target_cell = _safe_int(value1)
                weapon = me.current_weapon
            else:
                weapon = _find_weapon(_safe_int(value1))
                target_cell = _safe_int(value2)
            if weapon is None:
                return None
            if target_cell < 0 or target_cell >= engine.grid.nb_cells:
                return None

            ignore = {me.cell}
            if isinstance(value3, list):
                ignore = set(_safe_int(c) for c in value3)

            blocking = engine._entity_cells(exclude=me.id)
            return engine.grid.get_possible_cast_cells(
                target_cell,
                weapon["min_range"], weapon["max_range"],
                weapon.get("los", True), weapon.get("launch_type", 7),
                ignore, blocking,
            )

        def getCellsToUseChip(chip_id, target_id, value3=None):
            c = _find_chip(chip_id)
            if c is None:
                return None
            target = engine.entities.get(_safe_int(target_id))
            if target is None or target.dead:
                return None

            ignore = {me.cell}
            if isinstance(value3, list):
                ignore = set(_safe_int(v) for v in value3)

            blocking = engine._entity_cells(exclude=me.id) - {target.cell}
            return engine.grid.get_possible_cast_cells(
                target.cell,
                c["min_range"], c["max_range"],
                c.get("los", True), c.get("launch_type", 7),
                ignore, blocking,
            )

        def getCellsToUseChipOnCell(chip_id, cell, value3=None):
            c = _find_chip(chip_id)
            if c is None:
                return None
            cell = _safe_int(cell)
            if cell < 0 or cell >= engine.grid.nb_cells:
                return None

            ignore = {me.cell}
            if isinstance(value3, list):
                ignore = set(_safe_int(v) for v in value3)

            blocking = engine._entity_cells(exclude=me.id)
            return engine.grid.get_possible_cast_cells(
                cell,
                c["min_range"], c["max_range"],
                c.get("los", True), c.get("launch_type", 7),
                ignore, blocking,
            )

        # ── Pathfinding queries ─────────────────────────────────────

        def getPathLength(c1, c2, leeks_to_ignore=None):
            c1, c2 = _safe_int(c1), _safe_int(c2)
            # Dynamic ops: base 100 + distance²×20 (expensive BFS)
            dist = engine.grid.distance(c1, c2)
            interp = engine.interpreters.get(entity_id)
            if interp:
                interp.charge_ops(dist * dist * 20)
            if c1 == c2:
                return 0
            ignore: set[int] = set()
            if isinstance(leeks_to_ignore, list):
                for lid in leeks_to_ignore:
                    e = engine.entities.get(_safe_int(lid))
                    if e and not e.dead:
                        ignore.add(e.cell)
            blocked = engine._entity_cells(exclude=me.id) - ignore
            path = engine.grid.find_path_bfs(c1, c2, blocked)
            if not path:
                return None
            return len(path)

        def getPath(c1, c2, leeks_to_ignore=None):
            c1, c2 = _safe_int(c1), _safe_int(c2)
            dist = engine.grid.distance(c1, c2)
            interp = engine.interpreters.get(entity_id)
            if interp:
                interp.charge_ops(dist * dist * 20)
            if c1 == c2:
                return []
            ignore: set[int] = set()
            if isinstance(leeks_to_ignore, list):
                for lid in leeks_to_ignore:
                    e = engine.entities.get(_safe_int(lid))
                    if e and not e.dead:
                        ignore.add(e.cell)
            blocked = engine._entity_cells(exclude=me.id) - ignore
            path = engine.grid.find_path_bfs(c1, c2, blocked)
            if not path:
                return None
            return path

        def getDistance(c1, c2):
            """Alias for getCellDistance — both are Manhattan distance."""
            return getCellDistance(c1, c2)

        # ── Movement ────────────────────────────────────────────────

        def moveTowardLine(cell1, cell2, steps=None):
            cell1, cell2 = _safe_int(cell1), _safe_int(cell2)
            max_steps = me.mp if steps is None or _safe_int(steps) == -1 else min(_safe_int(steps), me.mp)
            if max_steps <= 0:
                return 0

            path = engine.grid.path_toward_line(me.cell, cell1, cell2)
            path = path[:max_steps]

            if path:
                # Filter out blocked cells (entities)
                blocked = engine._entity_cells(exclude=me.id)
                actual_path: list[int] = []
                for cell in path:
                    if cell in blocked:
                        break
                    actual_path.append(cell)
                if actual_path:
                    me.mp_used += len(actual_path)
                    me.cell = actual_path[-1]
                    engine._emit(10, me.id, actual_path)
                    return len(actual_path)
            return 0

        # ── Effects query ───────────────────────────────────────────

        def getEffects(target=None):
            """Return active effects as array of [type, value, remaining_turns, caster, target]."""
            ent = me
            if target is not None:
                ent = engine.entities.get(_safe_int(target))
                if ent is None:
                    return []
            result = []
            # Map internal effect names → real EFFECT_* constant values (from constants.ts)
            _gc = game_constants.get
            effect_type_map = {
                "abs_shield": _gc("EFFECT_ABSOLUTE_SHIELD"),       # 6
                "rel_shield": _gc("EFFECT_RELATIVE_SHIELD"),       # 5
                "tp_shackle": _gc("EFFECT_SHACKLE_TP"),            # 18
                "tp_buff": _gc("EFFECT_BUFF_TP"),                  # 8
                "str_buff": _gc("EFFECT_BUFF_STRENGTH"),           # 3
                "agi_buff": _gc("EFFECT_BUFF_AGILITY"),            # 4
                "res_buff": _gc("EFFECT_BUFF_RESISTANCE"),         # 21
                "wis_buff": _gc("EFFECT_BUFF_WISDOM"),             # 22
                "mp_buff": _gc("EFFECT_BUFF_MP"),                  # 7
                "poison": _gc("EFFECT_POISON"),                    # 13
                "aftereffect": _gc("EFFECT_AFTEREFFECT"),          # 25
                "str_shackle": _gc("EFFECT_SHACKLE_STRENGTH"),     # 19
                "agi_shackle": _gc("EFFECT_SHACKLE_AGILITY"),      # 47
                "wis_shackle": _gc("EFFECT_SHACKLE_WISDOM"),       # 48
                "mp_shackle": _gc("EFFECT_SHACKLE_MP"),            # 17
                "mag_shackle": _gc("EFFECT_SHACKLE_MAGIC"),        # 24
                "rel_vulnerability": _gc("EFFECT_VULNERABILITY"),  # 26
                "abs_vulnerability": _gc("EFFECT_ABSOLUTE_VULNERABILITY"), # 27
                "damage_return": _gc("EFFECT_DAMAGE_RETURN"),      # 20
            }
            for e in ent.effects:
                etype = effect_type_map.get(e.effect_type, 0)
                result.append([etype, int(e.value), e.remaining_turns, e.source_entity, ent.id])
            return result

        def getEntityTurnOrder(target=None):
            return None  # not critical for AI logic

        # ── Cell content queries ────────────────────────────────────

        def getLeekOnCell(cell):
            cell = _safe_int(cell)
            for e in engine.entities.values():
                if not e.dead and e.cell == cell:
                    return e.id
            return -1

        def getEntityOnCell(cell):
            return getLeekOnCell(cell)

        def isLeek(cell):
            return getLeekOnCell(_safe_int(cell)) != -1

        def isEntity(cell):
            return isLeek(cell)

        # ── Weapon on another entity ────────────────────────────────

        def getWeaponTarget(target_id=None):
            """getWeapon() for another entity — returns their current weapon template."""
            if target_id is None:
                if me.current_weapon is None:
                    return None
                return me.current_weapon.get("template", me.current_weapon.get("id"))
            t = engine.entities.get(_safe_int(target_id))
            if t is None or t.current_weapon is None:
                return None
            return t.current_weapon.get("template", t.current_weapon.get("id"))

        # ── Visual/debug stubs (no-ops in sim) ──────────────────────

        def getColor(r, g, b=None):
            if b is None:
                return _safe_int(r)  # single-arg form: getColor(rgb_int)
            return (_safe_int(r) << 16) | (_safe_int(g) << 8) | _safe_int(b)

        def mark(cell, color=None):
            return None  # visual only

        def markText(cell, text, color=None):
            return None  # visual only

        def unmark(cell):
            return None

        def unmarkAll():
            return None

        # ── Summoning stubs ─────────────────────────────────────────

        def summon(chip_id, cell, ai_id=None):
            return USE_FAILED  # summoning not implemented yet

        def getBulbChips(chip_id):
            return []

        def getMapType():
            return 0  # standard

        # ── yaelMagnier-required API additions ──────────────────────

        def getFightContext():
            return 2  # matchmaking (1=garden, 2=matchmaking, 3=tournament)

        def getFightType():
            return 0  # solo (0=solo, 1=farmer, 2=team)

        def isEnemy(target=None):
            if target is None:
                return False
            tid = _safe_int(target)
            t = engine.entities.get(tid)
            return t is not None and t.team != me.team

        def getLeeks():
            return [eid for eid, e in engine.entities.items() if not e.dead]

        def getLeekID(target=None):
            if target is None:
                return me.id
            return _safe_int(target)  # sim IDs are global IDs

        def getTotalTP(target=None):
            if target is None:
                return me.base_tp
            t = engine.entities.get(_safe_int(target))
            return t.base_tp if t else 0

        def getTotalMP(target=None):
            if target is None:
                return me.base_mp
            t = engine.entities.get(_safe_int(target))
            return t.base_mp if t else 0

        def getScience(target=None):
            # Science maps to strength in sim (same scaling, different name)
            if target is None:
                return me.strength
            t = engine.entities.get(_safe_int(target))
            return t.strength if t else 0

        def getAbsoluteShield(target=None):
            if target is None:
                return me.abs_shield
            t = engine.entities.get(_safe_int(target))
            return t.abs_shield if t else 0

        def getRelativeShield(target=None):
            if target is None:
                return me.rel_shield
            t = engine.entities.get(_safe_int(target))
            return t.rel_shield if t else 0

        def getDamageReturn(target=None):
            # Not implemented yet (task #83), return 0
            return 0

        def getSummoner(target=None):
            return None  # no summoning in sim

        def getTeamID(target=None):
            if target is None:
                return me.team
            t = engine.entities.get(_safe_int(target))
            return t.team if t else 0

        def getTeamName(target=None):
            return ""  # sim doesn't have team names

        def getFarmerCountry(target=None):
            return "fr"  # default

        def isChip(item_id):
            item_id = _safe_int(item_id)
            for c in me.chips:
                if c["template"] == item_id or c["id"] == item_id:
                    return True
            return False

        def isInlineChip(chip_id):
            c = _find_chip(chip_id)
            return (c["launch_type"] & 1) == 1 if c else False

        def getChipArea(chip_id):
            c = _find_chip(chip_id)
            return c.get("area", 0) if c else 0

        def getWeaponArea(w_id=None):
            w = _find_weapon(w_id)
            return w.get("area", 0) if w else 0

        def getChipCooldown_full(chip_id):
            c = _find_chip(chip_id)
            return c["cooldown"] if c else 0

        # getItem* functions — polymorphic (work for both chips and weapons)
        def _find_item(item_id):
            item_id = _safe_int(item_id)
            for c in me.chips:
                if c["template"] == item_id or c["id"] == item_id:
                    return c
            for w in me.weapons:
                if w["template"] == item_id or w["id"] == item_id:
                    return w
            return None

        def getItemMaxRange(item_id):
            item = _find_item(item_id)
            return item["max_range"] if item else 0

        def getItemMinRange(item_id):
            item = _find_item(item_id)
            return item["min_range"] if item else 0

        def getItemArea(item_id):
            item = _find_item(item_id)
            return item.get("area", 0) if item else 0

        def getItemCost(item_id):
            item = _find_item(item_id)
            return item["cost"] if item else 0

        def getItemCooldown(item_id):
            item = _find_item(item_id)
            return item.get("cooldown", 0) if item else 0

        def getItemEffects(item_id):
            item = _find_item(item_id)
            if not item:
                return []
            return [[e["type"], e["value1"], e["value2"], e["turns"], e["targets"], e["modifiers"]]
                    for e in item.get("effects", [])]

        def getGameItems():
            """Return all equipped items (chips + weapons) as template IDs."""
            items = [c["template"] for c in me.chips]
            items.extend(w["template"] for w in me.weapons)
            return items

        def useWeaponOnCell(cell):
            """Use weapon on a cell. Find target on that cell."""
            cell = _safe_int(cell)
            for e in engine.entities.values():
                if not e.dead and e.cell == cell:
                    return useWeapon(e.id)
            return USE_INVALID_TARGET

        def getAccessibleCells(target=None, mp=None):
            """Get cells reachable from a starting cell with given MP.

            LeekScript API: getAccessibleCells(start_cell, max_mp)
            - target is a CELL NUMBER (not an entity ID)
            - mp overrides available MP (defaults to current entity's MP)
            """
            if target is None:
                start = me.cell
                avail_mp = me.mp
            else:
                # target is a cell number per the LeekScript API spec
                start = _safe_int(target)
                avail_mp = me.mp
            if mp is not None:
                avail_mp = _safe_int(mp)
            # BFS from start, up to avail_mp steps
            blocked = engine._entity_cells(exclude=me.id)
            visited = {start}
            frontier = [start]
            for _ in range(avail_mp):
                next_frontier = []
                for cell in frontier:
                    for nb in engine.grid.neighbors(cell):
                        if nb not in visited and nb not in blocked:
                            visited.add(nb)
                            next_frontier.append(nb)
                frontier = next_frontier
            return list(visited)

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
            # Turn / identity
            "getTurn": getTurn,
            "getLeek": getLeek,
            "getFarmerID": getFarmerID,
            "getFarmerName": getFarmerName,
            "getType": getType,
            # Enemy
            "getEnemies": getEnemies,
            "getAllies": getAllies,
            "getNearestEnemy": getNearestEnemy,
            "isSummon": isSummon,
            "isDead": isDead,
            "isAlive": isAlive,
            "isEnemy": isEnemy,
            "getAliveEnemies": getAliveEnemies,
            "getAliveAllies": getAliveAllies,
            "getAliveEnemiesCount": getAliveEnemiesCount,
            "getAliveAlliesCount": getAliveAlliesCount,
            # Weapon queries
            "getWeapon": getWeapon,
            "getWeapons": getWeapons,
            "getWeaponCost": getWeaponCost,
            "getWeaponMinRange": getWeaponMinRange,
            "getWeaponMaxRange": getWeaponMaxRange,
            "getWeaponEffects": getWeaponEffects,
            "getWeaponName": getWeaponName,
            "isInlineWeapon": isInlineWeapon,
            "weaponNeedLos": weaponNeedLos,
            "isWeapon": isWeapon,
            "getWeaponLaunchType": getWeaponLaunchType,
            # Chip queries
            "getChips": getChips,
            "getChipName": getChipName,
            "getChipCost": getChipCost,
            "getCooldown": getCooldown,
            "getChipCooldown": getChipCooldown,
            "getChipMinRange": getChipMinRange,
            "getChipMaxRange": getChipMaxRange,
            "getChipEffects": getChipEffects,
            "chipNeedLos": chipNeedLos,
            "getChipLaunchType": getChipLaunchType,
            "isChip": isChip,
            "isInlineChip": isInlineChip,
            "getChipArea": getChipArea,
            "getWeaponArea": getWeaponArea,
            # Composite can-use checks
            "canUseWeapon": canUseWeapon,
            "canUseWeaponOnCell": canUseWeaponOnCell,
            "canUseChip": canUseChip,
            "canUseChipOnCell": canUseChipOnCell,
            # Spatial queries
            "getCellsToUseWeapon": getCellsToUseWeapon,
            "getCellsToUseWeaponOnCell": getCellsToUseWeaponOnCell,
            "getCellsToUseChip": getCellsToUseChip,
            "getCellsToUseChipOnCell": getCellsToUseChipOnCell,
            # Grid coordinates
            "getCellX": getCellX,
            "getCellY": getCellY,
            "getCellFromXY": getCellFromXY,
            "isObstacle": isObstacle,
            "isOnSameLine": isOnSameLine,
            # Map
            "isEmptyCell": isEmptyCell,
            "getCellContent": getCellContent,
            "lineOfSight": lineOfSight,
            "getLeekOnCell": getLeekOnCell,
            "getEntityOnCell": getEntityOnCell,
            "isLeek": isLeek,
            "isEntity": isEntity,
            # Pathfinding
            "getPathLength": getPathLength,
            "getPath": getPath,
            "getDistance": getDistance,
            # Actions
            "moveToward": moveToward,
            "moveTowardCell": moveTowardCell,
            "moveAwayFrom": moveAwayFrom,
            "moveAwayFromCell": moveAwayFromCell,
            "moveTowardLine": moveTowardLine,
            "setWeapon": setWeapon,
            "useWeapon": useWeapon,
            "useChip": useChip,
            "say": say,
            # Effects
            "getEffects": getEffects,
            "getEntityTurnOrder": getEntityTurnOrder,
            # Visual stubs
            "getColor": getColor,
            "mark": mark,
            "markText": markText,
            "unmark": unmark,
            "unmarkAll": unmarkAll,
            # Chip/weapon extended queries
            "getChipMaxUses": getChipMaxUses,
            "getChipInitialCooldown": getChipInitialCooldown,
            "getWeaponMaxUses": getWeaponMaxUses,
            "getWeaponLaunchType": getWeaponLaunchType,
            "getChipLaunchType": getChipLaunchType,
            "getAllChips": getAllChips,
            "getAllWeapons": getAllWeapons,
            "getCores": getCores,
            "getRAM": getRAM,
            "getStates": getStates,
            # Summon stubs
            "summon": summon,
            "getSummons": getSummons,
            "getBulbChips": getBulbChips,
            "getMapType": getMapType,
            # yaelMagnier additions — entity/stat queries
            "getFightContext": getFightContext,
            "getFightType": getFightType,
            "getLeeks": getLeeks,
            "getLeekID": getLeekID,
            "getTotalTP": getTotalTP,
            "getTotalMP": getTotalMP,
            "getScience": getScience,
            "getAbsoluteShield": getAbsoluteShield,
            "getRelativeShield": getRelativeShield,
            "getDamageReturn": getDamageReturn,
            "getSummoner": getSummoner,
            "getTeamID": getTeamID,
            "getTeamName": getTeamName,
            "getFarmerCountry": getFarmerCountry,
            "isEnemy": isEnemy,
            # yaelMagnier additions — item polymorphic queries
            "getGameItems": getGameItems,
            "getItemMaxRange": getItemMaxRange,
            "getItemMinRange": getItemMinRange,
            "getItemArea": getItemArea,
            "getItemCost": getItemCost,
            "getItemCooldown": getItemCooldown,
            "getItemEffects": getItemEffects,
            # yaelMagnier additions — actions / spatial
            "useWeaponOnCell": useWeaponOnCell,
            "getAccessibleCells": getAccessibleCells,
            # Registers (persistent AI state)
            "getRegister": getRegister,
            "setRegister": setRegister,
            # Resource monitoring
            "getUsedRAM": getUsedRAM,
            "getMaxRAM": getMaxRAM,
            "getMaxOperations": getMaxOperations,
            "getInstructionsCount": getInstructionsCount,
            "pause": pause,
            "getBirthTurn": getBirthTurn,
            "getPower": lambda target=None: 0,  # power stat (not tracked in sim)
            "addOperation": addOperation,
            # USE_* return codes (from FightFunctions.java, not in constants.ts)
            "USE_SUCCESS": USE_SUCCESS,
            "USE_FAILED": USE_FAILED,
            "USE_NOT_ENOUGH_TP": USE_NOT_ENOUGH_TP,
            "USE_INVALID_TARGET": USE_INVALID_TARGET,
            "USE_INVALID_POSITION": USE_INVALID_POSITION,
            "USE_TOO_FAR": USE_TOO_FAR,
            "USE_INVALID_COOLDOWN": USE_INVALID_COOLDOWN,
            # Misc non-constants.ts values (SORT_ASC/DESC are in constants.ts too,
            # but kept here as fallback since they're trivial)
            "SORT_ASC": 0,
            "SORT_DESC": 1,
        }
        # Inject ALL 315 game constants parsed from constants.ts (EFFECT_*, AREA_*,
        # ENTITY_*, COLOR_*, CELL_*, FIGHT_*, LAUNCH_TYPE_*, CHIP_*, WEAPON_*, etc.)
        # This is the single source of truth — never hand-write these values.
        api.update(game_constants.get_all())

        # Wrap callable API functions with ops charging
        interp_ref = engine.interpreters  # will be populated by load_ai
        def _make_ops_wrapper(name, fn, eid=entity_id):
            cost = API_OPS_COSTS.get(name, 15)
            def wrapper(*args, **kwargs):
                interp = interp_ref.get(eid)
                if interp:
                    interp.charge_ops(cost)
                return fn(*args, **kwargs)
            return wrapper

        wrapped_api = {}
        for name, val in api.items():
            if callable(val):
                wrapped_api[name] = _make_ops_wrapper(name, val)
            else:
                wrapped_api[name] = val  # constants pass through

        return wrapped_api

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
        """Apply a single effect from a weapon or chip.

        Uses eff["id"] — the effect type constant matching Effect.TYPE_* (Java)
        and EFFECT_* (constants.ts). NOT eff["type"] which is the chip category.
        """
        eff_id = eff["id"]
        v1 = eff["value1"]
        v2 = eff["value2"]
        turns = eff.get("turns", 0)

        if eff_id == 1:  # EFFECT_DAMAGE
            raw, crit = calc_damage(v1, v2, caster.effective_strength, caster.effective_agility, self.rng)
            actual = target.take_damage(raw)
            self._emit(101, target.id, actual)  # LOST_LIFE
            # Damage return: reflect % of actual damage back to attacker
            dr = target.damage_return
            if dr > 0 and actual > 0:
                reflected = int(actual * dr / 100)
                if reflected > 0:
                    reflected_actual = caster.take_damage(reflected)
                    if reflected_actual > 0:
                        self._emit(101, caster.id, reflected_actual)
            # Life steal: WIS/1000 of damage dealt
            if caster.wisdom > 0 and actual > 0:
                steal = int(actual * caster.wisdom / 1000)
                if steal > 0:
                    healed = caster.heal(steal)
                    if healed > 0:
                        self._emit(103, caster.id, healed)  # HEAL

        elif eff_id == 2:  # EFFECT_HEAL
            raw, crit = calc_heal(v1, v2, caster.wisdom, caster.agility, self.rng)
            actual = target.heal(raw)
            self._emit(103, target.id, actual)  # HEAL

        elif eff_id == 3:  # EFFECT_BUFF_STRENGTH
            val, crit = calc_stat_buff(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("str_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 3, val, turns)

        elif eff_id == 4:  # EFFECT_BUFF_AGILITY
            val, crit = calc_stat_buff(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("agi_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 4, val, turns)

        elif eff_id == 5:  # EFFECT_RELATIVE_SHIELD
            value, crit = calc_rel_shield(v1, v2, caster.resistance, caster.agility, self.rng)
            target.add_effect(ActiveEffect("rel_shield", value, turns, caster.id))
            self._emit(14, target.id, 5, value, turns)

        elif eff_id == 6:  # EFFECT_ABSOLUTE_SHIELD
            value, crit = calc_abs_shield(v1, v2, caster.resistance, caster.agility, self.rng)
            target.add_effect(ActiveEffect("abs_shield", value, turns, caster.id))
            self._emit(14, target.id, 6, value, turns)

        elif eff_id == 7:  # EFFECT_BUFF_MP
            val, crit = calc_stat_buff(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("mp_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 7, val, turns)

        elif eff_id == 8:  # EFFECT_BUFF_TP (Whip = raw TP buff uses id=8 internally)
            tp_gained, crit = calc_raw_tp_buff(v1, v2, target.base_tp, caster.agility, self.rng)
            target.add_effect(ActiveEffect("tp_buff", tp_gained, turns, caster.id))
            self._emit(14, target.id, 8, tp_gained, turns)

        elif eff_id == 9:  # EFFECT_DEBUFF (stat reduction)
            pass  # TODO: implement full debuff

        elif eff_id == 13:  # EFFECT_POISON
            raw, crit = calc_damage(v1, v2, caster.magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("poison", raw, turns, caster.id))
            self._emit(14, target.id, 13, raw, turns)

        elif eff_id == 17:  # EFFECT_SHACKLE_MP
            val, crit = calc_stat_shackle(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("mp_shackle", val, turns, caster.id))
            self._emit(14, target.id, 17, val, turns)

        elif eff_id == 18:  # EFFECT_SHACKLE_TP (Tranquilizer)
            tp_lost, crit = calc_tp_shackle(v1, v2, caster.magic, target.base_tp, caster.agility, self.rng)
            target.add_effect(ActiveEffect("tp_shackle", tp_lost, turns, caster.id))
            self._emit(100, target.id, tp_lost)  # LOST_PT (TP)

        elif eff_id == 19:  # EFFECT_SHACKLE_STRENGTH
            val, crit = calc_stat_shackle(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("str_shackle", val, turns, caster.id))
            self._emit(14, target.id, 19, val, turns)

        elif eff_id == 20:  # EFFECT_DAMAGE_RETURN
            val, crit = calc_damage_return(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("damage_return", val, turns, caster.id))
            self._emit(14, target.id, 20, val, turns)

        elif eff_id == 21:  # EFFECT_BUFF_RESISTANCE
            val, crit = calc_stat_buff(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("res_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 21, val, turns)

        elif eff_id == 22:  # EFFECT_BUFF_WISDOM
            val, crit = calc_stat_buff(v1, v2, caster.agility, self.rng)
            target.add_effect(ActiveEffect("wis_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 22, val, turns)

        elif eff_id == 24:  # EFFECT_SHACKLE_MAGIC
            val, crit = calc_stat_shackle(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("mag_shackle", val, turns, caster.id))
            self._emit(14, target.id, 24, val, turns)

        elif eff_id == 25:  # EFFECT_AFTEREFFECT
            raw, crit = calc_damage(v1, v2, caster.strength, caster.agility, self.rng)
            target.add_effect(ActiveEffect("aftereffect", raw, turns, caster.id))
            self._emit(14, target.id, 25, raw, turns)

        elif eff_id == 26:  # EFFECT_VULNERABILITY
            val, crit = calc_vulnerability(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("rel_vulnerability", val, turns, caster.id))
            self._emit(14, target.id, 26, val, turns)

        elif eff_id == 27:  # EFFECT_ABSOLUTE_VULNERABILITY
            val, crit = calc_vulnerability(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("abs_vulnerability", val, turns, caster.id))
            self._emit(14, target.id, 27, val, turns)

        elif eff_id == 32:  # EFFECT_RAW_BUFF_TP (Whip uses this)
            tp_gained, crit = calc_raw_tp_buff(v1, v2, target.base_tp, caster.agility, self.rng)
            target.add_effect(ActiveEffect("tp_buff", tp_gained, turns, caster.id))
            self._emit(14, target.id, 32, tp_gained, turns)

        elif eff_id == 38:  # EFFECT_RAW_BUFF_STRENGTH (Steroid, Ferocity)
            val = v1  # raw buffs don't scale with stats
            target.add_effect(ActiveEffect("str_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 38, val, turns)

        elif eff_id == 42:  # EFFECT_RAW_BUFF_RESISTANCE (Solidification)
            val = v1
            target.add_effect(ActiveEffect("res_buff", int(val), turns, caster.id))
            self._emit(14, target.id, 42, val, turns)

        elif eff_id == 47:  # EFFECT_SHACKLE_AGILITY
            val, crit = calc_stat_shackle(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("agi_shackle", val, turns, caster.id))
            self._emit(14, target.id, 47, val, turns)

        elif eff_id == 48:  # EFFECT_SHACKLE_WISDOM
            val, crit = calc_stat_shackle(v1, v2, caster.effective_magic, caster.agility, self.rng)
            target.add_effect(ActiveEffect("wis_shackle", val, turns, caster.id))
            self._emit(14, target.id, 48, val, turns)

        elif eff_id == 59:  # EFFECT_ADD_STATE
            state_id = int(v1)
            target.states.add(state_id)
            target.add_effect(ActiveEffect(f"state_{state_id}", state_id, turns, caster.id))
            self._emit(14, target.id, 59, state_id, turns)

    # ── Turn loop ───────────────────────────────────────────────────

    # Action codes that represent meaningful combat progress
    _COMBAT_ACTION_CODES = {16, 12, 101, 110, 11}  # USE_WEAPON, USE_CHIP, LOST_LIFE, POISON_DAMAGE, KILL
    STALE_TURN_LIMIT = 10  # consecutive turns with 0 combat actions → declare draw

    def run(self) -> dict:
        """Execute the full fight. Returns outcome dict.

        Runs in a thread with a large stack to support deep AI recursion
        (e.g. beam search AIs with thousands of nested function calls).
        The real game runs on JVM with ~512KB stack per thread; we match that.
        """
        import sys
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, 10_000))  # enough for legitimate recursion
        try:
            return self._run_inner()
        finally:
            sys.setrecursionlimit(old_limit)

    def _run_inner(self) -> dict:
        """Inner fight loop — called with elevated recursion limit."""
        # Determine turn order by frequency (higher = first)
        # Equal frequency → randomize (matches real game behavior)
        eids = [e.id for e in self.entity_list]
        self.rng.shuffle(eids)  # randomize before stable sort
        turn_order = sorted(
            eids,
            key=lambda eid: -self.entities[eid].frequency,
        )

        self._emit(0)  # START_FIGHT
        stale_turns = 0  # consecutive full turns with no combat actions

        while self.turn < MAX_TURNS:
            self.turn += 1
            self._emit(6, self.turn)  # NEW_TURN
            actions_before = len(self.actions)

            for eid in turn_order:
                entity = self.entities[eid]
                if entity.dead:
                    continue

                entity.start_turn()
                self._current_entity_id = eid
                self._emit(7, eid)  # LEEK_TURN

                # Apply poison/aftereffect damage at turn start
                for eff in entity.effects:
                    if eff.effect_type in ("poison", "aftereffect"):
                        actual = entity.take_damage(eff.value)
                        if actual > 0:
                            self._emit(110, entity.id, actual)  # POISON_DAMAGE
                        if entity.dead:
                            self._emit(11, entity.id)  # KILL
                            break
                        # Poison decays by 10% each turn; aftereffect does NOT decay
                        if eff.effect_type == "poison":
                            eff.value = int(eff.value * 0.9)

                if not entity.dead:
                    # Run the AI
                    interp = self.interpreters.get(eid)
                    program = self.programs.get(eid)
                    if interp and program:
                        try:
                            interp.run(program)
                        except OpsLimitExceeded:
                            # Operations limit reached — turn ends (normal game behavior)
                            self.debug_logs[eid].append(
                                f"[ops] Turn ended: {interp.ops:,} ops (limit {MAX_OPS:,})"
                            )
                        except RecursionError:
                            # Deep recursion in AI — log as stack overflow (like real LS runtime)
                            self.debug_logs[eid].append("AI ERROR: stack overflow (deep recursion)")
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

            # Stale fight detection: check if any combat actions happened this turn
            new_actions = self.actions[actions_before:]
            had_combat = any(a[0] in self._COMBAT_ACTION_CODES for a in new_actions)
            if had_combat:
                stale_turns = 0
            else:
                stale_turns += 1
                if stale_turns >= self.STALE_TURN_LIMIT:
                    for eid in turn_order:
                        self.debug_logs[eid].append(
                            f"[stale] Fight declared stale after {stale_turns} turns with no combat"
                        )
                    break

        winner = self._get_winner()
        self._emit(4, winner)  # END_FIGHT

        return {
            "winner": winner,
            "turns": self.turn,
            "actions": self.actions,
            "debug_logs": self.debug_logs,
        }
