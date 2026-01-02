"""Fight analysis utilities for extracting patterns and insights."""

from typing import Any


def analyze_action_economy(parsed_fight: dict) -> dict:
    """Analyze who got more actions (shots, moves, etc.)."""

    summary = parsed_fight.get("summary", {})
    turns = parsed_fight.get("turns", [])

    # Count actions per entity
    entity_actions = {}

    for turn in turns:
        for action in turn.get("actions", []):
            entity_id = action.get("entity")
            if entity_id is not None:
                if entity_id not in entity_actions:
                    entity_actions[entity_id] = {
                        "moves": 0,
                        "weapon_uses": 0,
                        "chip_uses": 0,
                        "total_actions": 0,
                    }

                action_type = action.get("type")
                if action_type == "move":
                    entity_actions[entity_id]["moves"] += 1
                elif action_type == "weapon":
                    entity_actions[entity_id]["weapon_uses"] += 1
                elif action_type == "chip":
                    entity_actions[entity_id]["chip_uses"] += 1

                entity_actions[entity_id]["total_actions"] += 1

    return entity_actions


def analyze_first_strike(parsed_fight: dict) -> dict:
    """Determine who attacked first and analyze the impact."""

    turns = parsed_fight.get("turns", [])

    first_damage = None
    first_attacker = None

    for turn in turns:
        for action in turn.get("actions", []):
            if action.get("type") == "damage":
                # Found first damage
                # Need to look backwards for who caused it
                first_damage = action
                break
        if first_damage:
            break

    # Find who shot first by looking for weapon/chip use before first damage
    if first_damage:
        for turn in turns:
            for action in turn.get("actions", []):
                if action.get("type") in ["weapon", "chip"]:
                    first_attacker = action.get("entity")
                    break
            if first_attacker is not None:
                break

    return {
        "first_attacker": first_attacker,
        "first_damage_turn": turns[0].get("number") if turns and first_damage else None,
    }


def analyze_damage_efficiency(parsed_fight: dict) -> dict:
    """Calculate damage per shot, damage per TP, etc."""

    summary = parsed_fight.get("summary", {})
    damage_dealt = summary.get("damage_dealt", {})
    weapon_uses = summary.get("weapon_uses", 0)

    entity_efficiency = {}

    # Count weapon uses per entity
    turns = parsed_fight.get("turns", [])
    entity_shots = {}

    for turn in turns:
        for action in turn.get("actions", []):
            if action.get("type") == "weapon":
                entity_id = action.get("entity")
                entity_shots[entity_id] = entity_shots.get(entity_id, 0) + 1

    # Calculate efficiency
    for entity_id, total_damage in damage_dealt.items():
        shots = entity_shots.get(int(entity_id), 0)
        if shots > 0:
            damage_per_shot = total_damage / shots
        else:
            damage_per_shot = 0

        entity_efficiency[entity_id] = {
            "total_damage": total_damage,
            "shots": shots,
            "damage_per_shot": damage_per_shot,
        }

    return entity_efficiency


def analyze_movement_efficiency(parsed_fight: dict) -> dict:
    """Analyze how efficiently entities moved (cells per MP, wasted movement)."""

    turns = parsed_fight.get("turns", [])
    entity_movement = {}

    for turn in turns:
        for action in turn.get("actions", []):
            if action.get("type") == "move":
                entity_id = action.get("entity")
                path = action.get("path", [])
                cells_moved = len(path) - 1 if len(path) > 1 else 0

                if entity_id not in entity_movement:
                    entity_movement[entity_id] = {
                        "total_moves": 0,
                        "total_cells": 0,
                    }

                entity_movement[entity_id]["total_moves"] += 1
                entity_movement[entity_id]["total_cells"] += cells_moved

    # Calculate averages
    for entity_id, stats in entity_movement.items():
        if stats["total_moves"] > 0:
            stats["avg_cells_per_move"] = stats["total_cells"] / stats["total_moves"]

    return entity_movement


def get_fight_insights(parsed_fight: dict, our_entity_id: int = 0) -> dict:
    """Get comprehensive insights about a fight."""

    insights = {
        "basic": {
            "winner": parsed_fight.get("winner"),
            "turns": parsed_fight.get("summary", {}).get("turns", 0),
        },
        "action_economy": analyze_action_economy(parsed_fight),
        "first_strike": analyze_first_strike(parsed_fight),
        "damage_efficiency": analyze_damage_efficiency(parsed_fight),
        "movement_efficiency": analyze_movement_efficiency(parsed_fight),
    }

    # Determine if we won
    our_actions = insights["action_economy"].get(our_entity_id, {})
    insights["we_won"] = parsed_fight.get("winner") == 1  # Assuming we're team 1

    return insights


def print_fight_analysis(insights: dict, our_entity_id: int = 0):
    """Pretty-print fight analysis."""

    print("=== FIGHT ANALYSIS ===")
    print(f"Winner: Team {insights['basic']['winner']}")
    print(f"Duration: {insights['basic']['turns']} turns")

    print("\n--- Action Economy ---")
    for entity_id, actions in insights["action_economy"].items():
        marker = "US" if entity_id == our_entity_id else "THEM"
        print(f"{marker} (Entity {entity_id}):")
        print(f"  Moves: {actions['moves']}")
        print(f"  Shots: {actions['weapon_uses']}")
        print(f"  Total actions: {actions['total_actions']}")

    print("\n--- Damage Efficiency ---")
    for entity_id, efficiency in insights["damage_efficiency"].items():
        marker = "US" if int(entity_id) == our_entity_id else "THEM"
        print(f"{marker} (Entity {entity_id}):")
        print(f"  Total damage: {efficiency['total_damage']}")
        print(f"  Shots fired: {efficiency['shots']}")
        print(f"  Damage/shot: {efficiency['damage_per_shot']:.1f}")

    first_strike = insights["first_strike"]
    print(f"\n--- First Strike ---")
    if first_strike["first_attacker"] is not None:
        marker = "US" if first_strike["first_attacker"] == our_entity_id else "THEM"
        print(f"{marker} (Entity {first_strike['first_attacker']}) attacked first")
        print(f"First damage on turn {first_strike['first_damage_turn']}")
    else:
        print("No combat occurred")
