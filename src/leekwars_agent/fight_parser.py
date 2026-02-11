"""Fight action parser for LeekWars replays.

Extended with Alpha Strike metrics (TP efficiency, opening buffs, chip tracking).
See docs/project_alpha_strike_integration.md for research background.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Any


class ActionType(IntEnum):
    """Fight action types from leek-wars-generator."""
    # Combat Actions
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

    # Damage/Heal
    LOST_PT = 100  # Lost TP
    LOST_LIFE = 101
    LOST_PM = 102  # Lost MP
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

    # Misc
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

    # System
    ERROR = 1000
    MAP = 1001
    AI_ERROR = 1002


@dataclass
class ParsedAction:
    """Parsed fight action."""
    type: ActionType
    entity_id: int | None
    params: list[Any]
    raw: list[Any]


def parse_action(raw: list) -> ParsedAction:
    """Parse a raw action array into structured data."""
    if not raw:
        return ParsedAction(ActionType.ERROR, None, [], raw)

    action_code = raw[0]
    try:
        action_type = ActionType(action_code)
    except ValueError:
        action_type = ActionType.ERROR

    entity_id = raw[1] if len(raw) > 1 else None
    params = raw[2:] if len(raw) > 2 else []

    return ParsedAction(action_type, entity_id, params, raw)


def parse_fight(fight_data: dict) -> dict:
    """Parse full fight data into structured format.

    Extended with Alpha Strike metrics:
    - Per-entity chip/weapon IDs (not just counts)
    - Opening buff tracking (turns 0-1)
    - TP usage estimation per turn
    """
    data = fight_data.get("data", {})

    result = {
        "id": fight_data.get("id"),
        "winner": fight_data.get("winner"),
        "status": fight_data.get("status"),
        "leeks": data.get("leeks", []),
        "map": data.get("map", {}),
        "turns": [],
        "summary": {
            "total_actions": 0,
            "turns": 0,
            "moves": 0,
            "weapon_uses": 0,
            "chip_uses": 0,
            "damage_dealt": {},
            "healing_done": {},
        },
        # Alpha Strike extensions
        "alpha_strike": {
            "entity_chips": {},      # entity_id -> list of chip IDs used
            "entity_weapons": {},    # entity_id -> list of weapon IDs used
            "opening_buffs": {},     # entity_id -> list of chip IDs used in turns 0-1
            "per_turn_actions": {},  # entity_id -> {turn: action_count}
            "hp_by_turn": {},        # entity_id -> {turn: hp}
        }
    }

    current_turn = {"number": 0, "actions": []}
    current_entity = None  # Track whose turn it is (from LEEK_TURN)
    actions = data.get("actions", [])
    result["summary"]["total_actions"] = len(actions)

    for raw_action in actions:
        action = parse_action(raw_action)

        if action.type == ActionType.NEW_TURN:
            if current_turn["actions"]:
                result["turns"].append(current_turn)
            current_turn = {"number": action.entity_id or 0, "actions": []}
            result["summary"]["turns"] += 1

        elif action.type == ActionType.LEEK_TURN:
            # Track whose turn it is for weapon/chip attribution
            current_entity = action.entity_id
            current_turn["actions"].append({
                "type": "leek_turn",
                "entity": action.entity_id,
                "params": action.params,
            })

        elif action.type == ActionType.MOVE_TO:
            current_turn["actions"].append({
                "type": "move",
                "entity": action.entity_id,
                "to": action.params[0] if action.params else None,
                "path": action.params[1] if len(action.params) > 1 else [],
            })
            result["summary"]["moves"] += 1

        elif action.type == ActionType.USE_WEAPON:
            # USE_WEAPON format: [16, cell?, target_entity]
            # The acting entity comes from LEEK_TURN, not from this action
            weapon_id = action.entity_id  # The weapon ID
            current_turn["actions"].append({
                "type": "weapon",
                "entity": current_entity,  # Use tracked entity, not action.entity_id
                "target": action.params[0] if action.params else None,
                "weapon_id": weapon_id,
                "raw_action": action.entity_id,  # Keep original for debugging
            })
            result["summary"]["weapon_uses"] += 1

            # Alpha Strike: Track weapon IDs per entity
            if current_entity is not None:
                if current_entity not in result["alpha_strike"]["entity_weapons"]:
                    result["alpha_strike"]["entity_weapons"][current_entity] = []
                if weapon_id not in result["alpha_strike"]["entity_weapons"][current_entity]:
                    result["alpha_strike"]["entity_weapons"][current_entity].append(weapon_id)

        elif action.type == ActionType.USE_CHIP:
            # Same pattern as USE_WEAPON
            chip_id = action.entity_id  # The chip ID
            current_turn["actions"].append({
                "type": "chip",
                "entity": current_entity,  # Use tracked entity
                "target": action.params[0] if action.params else None,
                "chip_id": chip_id,
                "raw_action": action.entity_id,
            })
            result["summary"]["chip_uses"] += 1

            # Alpha Strike: Track chip IDs per entity
            if current_entity is not None:
                if current_entity not in result["alpha_strike"]["entity_chips"]:
                    result["alpha_strike"]["entity_chips"][current_entity] = []
                if chip_id not in result["alpha_strike"]["entity_chips"][current_entity]:
                    result["alpha_strike"]["entity_chips"][current_entity].append(chip_id)

                # Track opening buffs (turns 0-1)
                turn_num = current_turn.get("number", 0)
                if turn_num <= 1:
                    if current_entity not in result["alpha_strike"]["opening_buffs"]:
                        result["alpha_strike"]["opening_buffs"][current_entity] = []
                    result["alpha_strike"]["opening_buffs"][current_entity].append(chip_id)

        elif action.type == ActionType.LOST_LIFE:
            entity = str(action.entity_id)
            damage = action.params[0] if action.params else 0
            result["summary"]["damage_dealt"][entity] = (
                result["summary"]["damage_dealt"].get(entity, 0) + damage
            )
            current_turn["actions"].append({
                "type": "damage",
                "entity": action.entity_id,
                "amount": damage,
            })

        elif action.type == ActionType.HEAL:
            entity = str(action.entity_id)
            heal = action.params[0] if action.params else 0
            result["summary"]["healing_done"][entity] = (
                result["summary"]["healing_done"].get(entity, 0) + heal
            )
            current_turn["actions"].append({
                "type": "heal",
                "entity": action.entity_id,
                "amount": heal,
            })

        elif action.type == ActionType.END_TURN:
            current_turn["actions"].append({
                "type": "end_turn",
                "entity": action.entity_id,
                "params": action.params,
            })

    # Add last turn
    if current_turn["actions"]:
        result["turns"].append(current_turn)

    return result


def extract_combat_stats(fight_json: dict) -> dict[int, dict]:
    """Extract per-leek combat stats from stored fight JSON.

    Parses the full action log in a single pass to compute:
    - damage_dealt/received, healing_done
    - weapons_used, chips_used (template IDs)
    - cells_moved, turns_alive, death_turn
    - ai_errors count

    Returns: {leek_id: {stat_name: value, ...}}
    Entity IDs (0,1,...) in actions are mapped back to real leek IDs
    via (team, farmer) matching between data.leeks and leeks1/leeks2.
    """
    fight = fight_json.get("fight", fight_json)
    data = fight.get("data", {})
    actions = data.get("actions", [])

    if not actions:
        return {}

    # Build entity_id → leek_id mapping
    entity_to_leek: dict[int, int] = {}
    for entity in data.get("leeks", []):
        if entity.get("summon"):
            continue
        eid = entity.get("id")
        team = entity.get("team")
        farmer = entity.get("farmer")
        if eid is None or team is None:
            continue
        team_leeks = fight.get(f"leeks{team}", [])
        for leek in team_leeks:
            if leek.get("farmer") == farmer:
                entity_to_leek[eid] = leek.get("id")
                break

    if not entity_to_leek:
        return {}

    # Initialize per-leek stats
    stats: dict[int, dict] = {}
    for leek_id in entity_to_leek.values():
        stats[leek_id] = {
            "damage_dealt": 0,
            "damage_received": 0,
            "healing_done": 0,
            "weapons_used": set(),
            "chips_used": set(),
            "cells_moved": 0,
            "turns_alive": 0,
            "death_turn": 0,  # 0 = survived
            "ai_errors": 0,
        }

    current_entity_id = None  # Track whose turn it is
    current_turn_num = 0

    for action in actions:
        if not action:
            continue
        code = action[0]

        if code == 6:  # NEW_TURN
            current_turn_num = action[1] if len(action) > 1 else current_turn_num + 1

        elif code == 7:  # LEEK_TURN
            current_entity_id = action[1] if len(action) > 1 else None
            leek_id = entity_to_leek.get(current_entity_id)
            if leek_id and leek_id in stats:
                stats[leek_id]["turns_alive"] += 1

        elif code == 10:  # MOVE_TO — [10, entity, target_cell, path_list]
            eid = action[1] if len(action) > 1 else None
            leek_id = entity_to_leek.get(eid)
            if leek_id and leek_id in stats:
                path = action[3] if len(action) > 3 and isinstance(action[3], list) else []
                stats[leek_id]["cells_moved"] += len(path) if path else 1

        elif code == 12:  # USE_CHIP — [12, chip_template_id, ...]
            chip_id = action[1] if len(action) > 1 else None
            leek_id = entity_to_leek.get(current_entity_id)
            if leek_id and leek_id in stats and chip_id is not None:
                stats[leek_id]["chips_used"].add(chip_id)

        elif code == 16:  # USE_WEAPON — [16, weapon_template_id, ...]
            weapon_id = action[1] if len(action) > 1 else None
            leek_id = entity_to_leek.get(current_entity_id)
            if leek_id and leek_id in stats and weapon_id is not None:
                stats[leek_id]["weapons_used"].add(weapon_id)

        elif code == 101:  # LOST_LIFE — [101, target_entity, amount, ...]
            eid = action[1] if len(action) > 1 else None
            damage = action[2] if len(action) > 2 else 0
            # Damage received by target
            target_leek = entity_to_leek.get(eid)
            if target_leek and target_leek in stats:
                stats[target_leek]["damage_received"] += damage
            # Damage dealt by active entity
            dealer_leek = entity_to_leek.get(current_entity_id)
            if dealer_leek and dealer_leek in stats and dealer_leek != target_leek:
                stats[dealer_leek]["damage_dealt"] += damage

        elif code == 103:  # HEAL — [103, entity, amount]
            eid = action[1] if len(action) > 1 else None
            heal = action[2] if len(action) > 2 else 0
            # Healing attributed to the caster (active entity), not target
            healer_leek = entity_to_leek.get(current_entity_id)
            if healer_leek and healer_leek in stats:
                stats[healer_leek]["healing_done"] += heal

        elif code == 110:  # POISON_DAMAGE — [110, entity, amount, ...]
            eid = action[1] if len(action) > 1 else None
            damage = action[2] if len(action) > 2 else 0
            target_leek = entity_to_leek.get(eid)
            if target_leek and target_leek in stats:
                stats[target_leek]["damage_received"] += damage

        elif code == 5:  # PLAYER_DEAD — [5, entity]
            eid = action[1] if len(action) > 1 else None
            leek_id = entity_to_leek.get(eid)
            if leek_id and leek_id in stats:
                stats[leek_id]["death_turn"] = current_turn_num

        elif code in (1000, 1002):  # ERROR / AI_ERROR
            leek_id = entity_to_leek.get(current_entity_id)
            if leek_id and leek_id in stats:
                stats[leek_id]["ai_errors"] += 1

    # Convert sets to sorted lists for JSON serialization
    for leek_id in stats:
        stats[leek_id]["weapons_used"] = sorted(stats[leek_id]["weapons_used"])
        stats[leek_id]["chips_used"] = sorted(stats[leek_id]["chips_used"])

    return stats


def summarize_fight(fight_data: dict) -> str:
    """Generate human-readable fight summary."""
    parsed = parse_fight(fight_data)

    lines = [
        f"Fight #{parsed['id']}",
        f"Winner: Team {parsed['winner']}",
        f"Duration: {parsed['summary']['turns']} turns",
        f"Actions: {parsed['summary']['total_actions']}",
        f"Moves: {parsed['summary']['moves']}",
        f"Weapon uses: {parsed['summary']['weapon_uses']}",
        f"Chip uses: {parsed['summary']['chip_uses']}",
    ]

    if parsed["summary"]["damage_dealt"]:
        lines.append("Damage dealt:")
        for entity, dmg in parsed["summary"]["damage_dealt"].items():
            lines.append(f"  Entity {entity}: {dmg}")

    return "\n".join(lines)
