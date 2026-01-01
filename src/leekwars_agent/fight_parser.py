"""Fight action parser for LeekWars replays."""

from enum import IntEnum
from dataclasses import dataclass
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
    """Parse full fight data into structured format."""
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
        }
    }

    current_turn = {"number": 0, "actions": []}
    actions = data.get("actions", [])
    result["summary"]["total_actions"] = len(actions)

    for raw_action in actions:
        action = parse_action(raw_action)

        if action.type == ActionType.NEW_TURN:
            if current_turn["actions"]:
                result["turns"].append(current_turn)
            current_turn = {"number": action.entity_id or 0, "actions": []}
            result["summary"]["turns"] += 1

        elif action.type == ActionType.MOVE_TO:
            current_turn["actions"].append({
                "type": "move",
                "entity": action.entity_id,
                "to": action.params[0] if action.params else None,
                "path": action.params[1] if len(action.params) > 1 else [],
            })
            result["summary"]["moves"] += 1

        elif action.type == ActionType.USE_WEAPON:
            current_turn["actions"].append({
                "type": "weapon",
                "entity": action.entity_id,
                "params": action.params,
            })
            result["summary"]["weapon_uses"] += 1

        elif action.type == ActionType.USE_CHIP:
            current_turn["actions"].append({
                "type": "chip",
                "entity": action.entity_id,
                "params": action.params,
            })
            result["summary"]["chip_uses"] += 1

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

        elif action.type in (ActionType.LEEK_TURN, ActionType.END_TURN):
            current_turn["actions"].append({
                "type": action.type.name.lower(),
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
