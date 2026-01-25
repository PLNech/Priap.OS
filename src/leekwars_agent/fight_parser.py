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
