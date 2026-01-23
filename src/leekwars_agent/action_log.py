"""Full action log reconstruction from fight data.

Produces human-readable turn-by-turn action logs like:
    Turn 1
    Zigotos's turn
    Zigotos uses Adrenaline (1 TP)
    Zigotos gains 5 TP (1 turns)
    ...
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from enum import IntEnum


# Load chip/weapon data for name lookups
DATA_DIR = Path(__file__).parent.parent.parent / "data"

_CHIPS: dict[int, dict] = {}
_WEAPONS: dict[int, dict] = {}


def _load_items():
    global _CHIPS, _WEAPONS
    if not _CHIPS:
        chips_file = DATA_DIR / "chips.json"
        if chips_file.exists():
            data = json.loads(chips_file.read_text())
            # Handle both formats: {"chips": [...]} or [...]
            chips = data.get("chips", data) if isinstance(data, dict) else data
            if isinstance(chips, list):
                _CHIPS = {c["id"]: c for c in chips}
            else:
                _CHIPS = {int(k): v for k, v in chips.items()}
    if not _WEAPONS:
        weapons_file = DATA_DIR / "weapons.json"
        if weapons_file.exists():
            data = json.loads(weapons_file.read_text())
            weapons = data.get("weapons", data) if isinstance(data, dict) else data
            if isinstance(weapons, list):
                _WEAPONS = {w["id"]: w for w in weapons}
            else:
                _WEAPONS = {int(k): v for k, v in weapons.items()}


def get_chip_name(chip_id: int) -> str:
    _load_items()
    return _CHIPS.get(chip_id, {}).get("name", f"Chip#{chip_id}")


def get_weapon_name(weapon_id: int) -> str:
    _load_items()
    return _WEAPONS.get(weapon_id, {}).get("name", f"Weapon#{weapon_id}")


class ActionCode(IntEnum):
    """Action codes from fight replay data."""
    START_FIGHT = 0
    END_FIGHT = 4
    PLAYER_DEAD = 5
    NEW_TURN = 6
    LEEK_TURN = 7
    END_TURN = 8
    SUMMON = 9
    MOVE_TO = 10
    KILL = 11
    USE_CHIP = 12
    SET_WEAPON = 13
    STACK_EFFECT = 14
    CHEST_OPENED = 15
    USE_WEAPON = 16

    # Resource changes
    LOST_TP = 100
    LOST_LIFE = 101
    LOST_MP = 102
    HEAL = 103
    VITALITY = 104
    RESURRECT = 105
    LOSE_STRENGTH = 106
    NOVA_DAMAGE = 107
    DAMAGE_RETURN = 108
    LIFE_DAMAGE = 109
    POISON_DAMAGE = 110
    AFTEREFFECT = 111
    NOVA_VITALITY = 112

    # Chat/Display
    LAMA = 201
    SAY = 203
    SHOW_CELL = 205

    # Effects
    ADD_WEAPON_EFFECT = 301
    ADD_CHIP_EFFECT = 302
    REMOVE_EFFECT = 303
    UPDATE_EFFECT = 304
    REDUCE_EFFECTS = 306
    REMOVE_POISONS = 307
    REMOVE_SHACKLES = 308

    # Errors
    ERROR = 1000
    MAP = 1001
    AI_ERROR = 1002


@dataclass
class LeekInfo:
    """Leek information from fight data."""
    entity_id: int
    leek_id: int
    name: str
    team: int
    level: int
    farmer_id: int
    stats: dict = field(default_factory=dict)


@dataclass
class ActionLogEntry:
    """Single action in the log."""
    turn: int
    entity_id: int
    entity_name: str
    action_type: str
    description: str
    details: dict = field(default_factory=dict)


def extract_leeks(fight_data: dict) -> dict[int, LeekInfo]:
    """Extract leek info mapping entity_id -> LeekInfo."""
    leeks = {}
    data = fight_data.get("data", {})

    # From data.leeks (entity info with stats)
    for leek in data.get("leeks", []):
        entity_id = leek.get("id", 0)
        leeks[entity_id] = LeekInfo(
            entity_id=entity_id,
            leek_id=0,  # Will fill from leeks1/leeks2
            name=leek.get("name", f"Entity{entity_id}"),
            team=leek.get("team", 0),
            level=leek.get("level", 0),
            farmer_id=leek.get("farmer", 0),
            stats={
                "life": leek.get("life", 0),
                "strength": leek.get("strength", 0),
                "agility": leek.get("agility", 0),
                "wisdom": leek.get("wisdom", 0),
                "resistance": leek.get("resistance", 0),
                "magic": leek.get("magic", 0),
                "science": leek.get("science", 0),
                "frequency": leek.get("frequency", 0),
                "tp": leek.get("tp", 0),
                "mp": leek.get("mp", 0),
            }
        )

    # Map entity_id to actual leek_id from leeks1/leeks2
    for i, leek in enumerate(fight_data.get("leeks1", [])):
        if i in leeks:
            leeks[i].leek_id = leek.get("id", 0)
    for i, leek in enumerate(fight_data.get("leeks2", [])):
        entity_id = len(fight_data.get("leeks1", [])) + i
        if entity_id in leeks:
            leeks[entity_id].leek_id = leek.get("id", 0)

    return leeks


def reconstruct_action_log(fight_data: dict) -> list[ActionLogEntry]:
    """Reconstruct full action log from fight data."""
    leeks = extract_leeks(fight_data)
    actions = fight_data.get("data", {}).get("actions", [])

    log: list[ActionLogEntry] = []
    current_turn = 0
    current_entity = -1

    def get_name(entity_id: int) -> str:
        if entity_id in leeks:
            return leeks[entity_id].name
        return f"Entity{entity_id}"

    for action in actions:
        if not action:
            continue

        code = action[0]

        try:
            action_type = ActionCode(code)
        except ValueError:
            action_type = None

        if code == ActionCode.NEW_TURN:
            current_turn = action[1] if len(action) > 1 else current_turn + 1
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=-1,
                entity_name="",
                action_type="turn",
                description=f"Turn {current_turn}",
            ))

        elif code == ActionCode.LEEK_TURN:
            entity_id = action[1] if len(action) > 1 else 0
            current_entity = entity_id
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="leek_turn",
                description=f"{name}'s turn",
            ))

        elif code == ActionCode.END_TURN:
            entity_id = action[1] if len(action) > 1 else current_entity
            # End turn has [8, entity_id, remaining_tp, remaining_mp]

        elif code == ActionCode.MOVE_TO:
            entity_id = action[1] if len(action) > 1 else current_entity
            dest_cell = action[2] if len(action) > 2 else 0
            path = action[3] if len(action) > 3 else []
            cells_moved = len(path) if path else 1
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="move",
                description=f"{name} moves ({cells_moved} MP)",
                details={"to": dest_cell, "path": path, "cells": cells_moved}
            ))

        elif code == ActionCode.USE_CHIP:
            chip_id = action[1] if len(action) > 1 else 0
            target_cell = action[2] if len(action) > 2 else 0
            target_entity = action[3] if len(action) > 3 else current_entity
            chip_name = get_chip_name(chip_id)
            name = get_name(current_entity)
            # TP cost would need chip data lookup
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=current_entity,
                entity_name=name,
                action_type="chip",
                description=f"{name} uses {chip_name}",
                details={"chip_id": chip_id, "target": target_entity}
            ))

        elif code == ActionCode.USE_WEAPON:
            target_cell = action[1] if len(action) > 1 else 0
            target_entity = action[2] if len(action) > 2 else 0
            name = get_name(current_entity)
            target_name = get_name(target_entity)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=current_entity,
                entity_name=name,
                action_type="weapon",
                description=f"{name} attacks {target_name}",
                details={"target": target_entity, "cell": target_cell}
            ))

        elif code == ActionCode.SET_WEAPON:
            entity_id = action[1] if len(action) > 1 else current_entity
            # Weapon ID is not in this action, it's implicit
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="set_weapon",
                description=f"{name} takes weapon (1 TP)",
            ))

        elif code == ActionCode.LOST_LIFE:
            entity_id = action[1] if len(action) > 1 else 0
            damage = action[2] if len(action) > 2 else 0
            source = action[3] if len(action) > 3 else 0
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="damage",
                description=f"{name} loses {damage} life",
                details={"damage": damage, "source": source}
            ))

        elif code == ActionCode.HEAL:
            entity_id = action[1] if len(action) > 1 else 0
            amount = action[2] if len(action) > 2 else 0
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="heal",
                description=f"{name} heals {amount} life",
                details={"amount": amount}
            ))

        elif code == ActionCode.VITALITY:
            entity_id = action[1] if len(action) > 1 else 0
            amount = action[2] if len(action) > 2 else 0
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="vitality",
                description=f"{name} gains {amount} total health",
                details={"amount": amount}
            ))

        elif code == ActionCode.ADD_CHIP_EFFECT:
            # [302, effect_id, target, caster, turns, value, ...]
            effect_id = action[1] if len(action) > 1 else 0
            target = action[2] if len(action) > 2 else 0
            caster = action[3] if len(action) > 3 else 0
            turns = action[4] if len(action) > 4 else 0
            value = action[5] if len(action) > 5 else 0
            name = get_name(target)
            # Effect types: strength, agility, wisdom, resistance, etc.
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=target,
                entity_name=name,
                action_type="buff",
                description=f"{name} gains {value} (effect {effect_id}, {turns} turns)",
                details={"effect_id": effect_id, "value": value, "turns": turns}
            ))

        elif code == ActionCode.SAY:
            message = action[1] if len(action) > 1 else ""
            name = get_name(current_entity)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=current_entity,
                entity_name=name,
                action_type="say",
                description=f'{name} says: "{message}" (1 TP)',
                details={"message": message}
            ))

        elif code == ActionCode.PLAYER_DEAD:
            entity_id = action[1] if len(action) > 1 else 0
            killer = action[2] if len(action) > 2 else -1
            name = get_name(entity_id)
            log.append(ActionLogEntry(
                turn=current_turn,
                entity_id=entity_id,
                entity_name=name,
                action_type="death",
                description=f"{name} dies",
                details={"killer": killer}
            ))

        elif code == ActionCode.SUMMON:
            # Summon actions
            pass

    return log


def format_action_log(fight_data: dict) -> str:
    """Format fight as human-readable action log."""
    log = reconstruct_action_log(fight_data)

    lines = [f"Fight #{fight_data.get('id', '?')}"]
    lines.append(f"Winner: Team {fight_data.get('winner', '?')}")
    lines.append("")
    lines.append("Actions")

    current_turn = 0
    for entry in log:
        if entry.action_type == "turn":
            lines.append(entry.description)
        elif entry.action_type == "leek_turn":
            lines.append(entry.description)
        else:
            lines.append(f"  {entry.description}")

    return "\n".join(lines)


@dataclass
class FightMetadata:
    """Extracted metadata for storage (matches tagadai schema)."""
    fight_id: int
    leek_id: int
    entity_id: int
    level: int = 0
    strength: int = 0
    agility: int = 0
    magic: int = 0
    resistance: int = 0
    wisdom: int = 0
    science: int = 0
    frequency: int = 0
    life: int = 0
    tp: int = 0
    mp: int = 0
    weapon_actions: int = 0
    chip_actions: int = 0
    move_actions: int = 0
    summon_actions: int = 0
    physical_damage: int = 0
    magic_damage: int = 0
    poison_damage: int = 0
    heal_done: int = 0
    total_tp_spent: int = 0
    total_mp_spent: int = 0
    total_cells_moved: int = 0
    turns_alive: int = 0
    weapons_used: list[int] = field(default_factory=list)
    chips_used: list[int] = field(default_factory=list)


def extract_metadata(fight_data: dict) -> list[FightMetadata]:
    """Extract per-leek metadata from fight (for fight_leek_metadata table)."""
    fight_id = fight_data.get("id", 0)
    leeks = extract_leeks(fight_data)
    actions = fight_data.get("data", {}).get("actions", [])

    # Initialize metadata for each leek
    metadata: dict[int, FightMetadata] = {}
    for entity_id, leek in leeks.items():
        metadata[entity_id] = FightMetadata(
            fight_id=fight_id,
            leek_id=leek.leek_id,
            entity_id=entity_id,
            level=leek.level,
            strength=leek.stats.get("strength", 0),
            agility=leek.stats.get("agility", 0),
            magic=leek.stats.get("magic", 0),
            resistance=leek.stats.get("resistance", 0),
            wisdom=leek.stats.get("wisdom", 0),
            science=leek.stats.get("science", 0),
            frequency=leek.stats.get("frequency", 0),
            life=leek.stats.get("life", 0),
            tp=leek.stats.get("tp", 0),
            mp=leek.stats.get("mp", 0),
        )

    current_entity = -1

    for action in actions:
        if not action:
            continue
        code = action[0]

        if code == ActionCode.LEEK_TURN:
            current_entity = action[1] if len(action) > 1 else current_entity
            if current_entity in metadata:
                metadata[current_entity].turns_alive += 1

        elif code == ActionCode.MOVE_TO:
            entity_id = action[1] if len(action) > 1 else current_entity
            path = action[3] if len(action) > 3 else []
            cells = len(path) if path else 1
            if entity_id in metadata:
                metadata[entity_id].move_actions += 1
                metadata[entity_id].total_cells_moved += cells
                metadata[entity_id].total_mp_spent += cells

        elif code == ActionCode.USE_CHIP:
            chip_id = action[1] if len(action) > 1 else 0
            if current_entity in metadata:
                metadata[current_entity].chip_actions += 1
                if chip_id not in metadata[current_entity].chips_used:
                    metadata[current_entity].chips_used.append(chip_id)

        elif code == ActionCode.USE_WEAPON:
            if current_entity in metadata:
                metadata[current_entity].weapon_actions += 1

        elif code == ActionCode.SET_WEAPON:
            entity_id = action[1] if len(action) > 1 else current_entity
            if entity_id in metadata:
                metadata[entity_id].total_tp_spent += 1

        elif code == ActionCode.LOST_LIFE:
            entity_id = action[1] if len(action) > 1 else 0
            damage = action[2] if len(action) > 2 else 0
            source_type = action[3] if len(action) > 3 else 0
            # Source type: 1=physical, 2=magic, etc.
            # The damage was DEALT by someone else
            # Find who dealt it (current_entity usually)
            if current_entity in metadata and entity_id != current_entity:
                if source_type == 2:
                    metadata[current_entity].magic_damage += damage
                else:
                    metadata[current_entity].physical_damage += damage

        elif code == ActionCode.HEAL:
            entity_id = action[1] if len(action) > 1 else 0
            amount = action[2] if len(action) > 2 else 0
            if current_entity in metadata:
                metadata[current_entity].heal_done += amount

    return list(metadata.values())
