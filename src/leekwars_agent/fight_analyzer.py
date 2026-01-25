"""Fight analysis utilities for extracting patterns and insights."""

import math
from collections import Counter
from dataclasses import dataclass
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


# =============================================================================
# OPPONENT AI CLASSIFICATION (Tier 2)
# =============================================================================

@dataclass
class AIClassification:
    """Result of AI behavior classification."""
    archetype: str  # "kiter", "aggro", "healer", "balanced"
    confidence: float  # 0.0 to 1.0
    entropy: float  # Decision entropy (higher = more random)
    metrics: dict[str, float]  # Raw metrics used for classification


def decision_entropy(actions: list[dict]) -> float:
    """Calculate Shannon entropy of action type distribution.

    Higher entropy = more varied/random decisions.
    Lower entropy = more predictable/focused behavior.

    Typical values:
    - < 1.0: Very focused (e.g., pure aggro, just attacks)
    - 1.0-2.0: Normal human-like variety
    - > 2.0: High variety or erratic behavior

    Args:
        actions: List of parsed actions from fight_parser

    Returns:
        Shannon entropy in bits
    """
    if not actions:
        return 0.0

    # Count action types
    action_types = [a.get("type", "unknown") for a in actions]
    counts = Counter(action_types)
    total = len(action_types)

    if total == 0:
        return 0.0

    # Shannon entropy: -sum(p * log2(p))
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    return entropy


def _get_entity_actions(parsed_fight: dict, entity_id: int) -> list[dict]:
    """Extract all actions for a specific entity."""
    actions = []
    for turn in parsed_fight.get("turns", []):
        for action in turn.get("actions", []):
            if action.get("entity") == entity_id:
                actions.append(action)
    return actions


def _calculate_move_tendency(parsed_fight: dict, entity_id: int, opponent_id: int) -> float:
    """Calculate if entity moves toward or away from opponent.

    Positive = moving away (kiting)
    Negative = moving toward (aggro)
    Zero = neutral/static

    Note: This is a simplified heuristic based on cell positions.
    """
    # Get leek positions from fight data
    leeks = parsed_fight.get("leeks", [])
    entity_start_pos = None
    opponent_start_pos = None

    for leek in leeks:
        if leek.get("id") == entity_id:
            entity_start_pos = leek.get("cellPos")
        elif leek.get("id") == opponent_id:
            opponent_start_pos = leek.get("cellPos")

    if entity_start_pos is None or opponent_start_pos is None:
        return 0.0

    # Track position changes via move actions
    moves = []
    current_pos = entity_start_pos

    for turn in parsed_fight.get("turns", []):
        for action in turn.get("actions", []):
            if action.get("entity") == entity_id and action.get("type") == "move":
                new_pos = action.get("to")
                if new_pos is not None:
                    # Simple heuristic: compare to opponent start
                    # (Real implementation would track opponent movement too)
                    old_dist = abs(current_pos - opponent_start_pos)
                    new_dist = abs(new_pos - opponent_start_pos)
                    moves.append(new_dist - old_dist)  # Positive = moved away
                    current_pos = new_pos

    if not moves:
        return 0.0

    return sum(moves) / len(moves)


def classify_ai_behavior(parsed_fight: dict, entity_id: int) -> AIClassification:
    """Classify an AI's behavior archetype from fight actions.

    Archetypes:
    - "aggro": High attack rate, moves toward enemy, low healing
    - "kiter": Moves away from enemy, attacks at range
    - "healer": High heal/buff ratio (rare in solo)
    - "balanced": Mix of behaviors

    Args:
        parsed_fight: Output from fight_parser.parse_fight()
        entity_id: The entity to classify

    Returns:
        AIClassification with archetype, confidence, and metrics
    """
    # Get all actions for this entity
    actions = _get_entity_actions(parsed_fight, entity_id)

    if not actions:
        return AIClassification(
            archetype="unknown",
            confidence=0.0,
            entropy=0.0,
            metrics={},
        )

    # Count action types
    moves = [a for a in actions if a.get("type") == "move"]
    attacks = [a for a in actions if a.get("type") in ("weapon", "chip")]
    heals = [a for a in actions if a.get("type") == "heal"]
    weapon_attacks = [a for a in actions if a.get("type") == "weapon"]
    chip_uses = [a for a in actions if a.get("type") == "chip"]

    total_turns = parsed_fight.get("summary", {}).get("turns", 1) or 1
    total_actions = len(actions) or 1

    # Calculate metrics
    attack_rate = len(attacks) / total_turns  # Attacks per turn
    heal_ratio = len(heals) / total_actions if total_actions > 0 else 0
    move_rate = len(moves) / total_turns  # Moves per turn

    # Find opponent ID (the other entity)
    all_entity_ids = set()
    for turn in parsed_fight.get("turns", []):
        for action in turn.get("actions", []):
            eid = action.get("entity")
            if eid is not None:
                all_entity_ids.add(eid)

    opponent_ids = [eid for eid in all_entity_ids if eid != entity_id]
    opponent_id = opponent_ids[0] if opponent_ids else None

    # Calculate move tendency (positive = away, negative = toward)
    # Note: opponent_id can be 0, so check "is not None" not just truthiness
    move_tendency = _calculate_move_tendency(parsed_fight, entity_id, opponent_id) if opponent_id is not None else 0

    # Calculate entropy
    entropy = decision_entropy(actions)

    metrics = {
        "attack_rate": attack_rate,
        "heal_ratio": heal_ratio,
        "move_rate": move_rate,
        "move_tendency": move_tendency,
        "total_actions": len(actions),
        "weapon_attacks": len(weapon_attacks),
        "chip_uses": len(chip_uses),
    }

    # Classification logic
    archetype = "balanced"
    confidence = 0.5

    # Healer: High heal ratio
    if heal_ratio > 0.3:
        archetype = "healer"
        confidence = min(0.9, heal_ratio + 0.3)

    # Kiter: Moves away from enemy, moderate attacks
    elif move_tendency > 2.0 and move_rate > 0.5:
        archetype = "kiter"
        confidence = min(0.9, 0.5 + move_tendency / 10)

    # Aggro: High attack rate, moves toward enemy
    elif attack_rate > 2.0 or (attack_rate > 1.5 and move_tendency < 0):
        archetype = "aggro"
        confidence = min(0.9, 0.4 + attack_rate / 5)

    # Balanced: Mix of behaviors
    else:
        archetype = "balanced"
        confidence = 0.6

    return AIClassification(
        archetype=archetype,
        confidence=confidence,
        entropy=entropy,
        metrics=metrics,
    )


def classify_opponent_from_fight(fight_data: dict, our_entity_id: int = 0) -> AIClassification | None:
    """Convenience function to classify the opponent in a fight.

    Args:
        fight_data: Raw fight data from API
        our_entity_id: Our entity ID (default 0 for team 1)

    Returns:
        AIClassification for the opponent, or None if can't determine
    """
    from leekwars_agent.fight_parser import parse_fight

    parsed = parse_fight(fight_data)

    # Find opponent entity ID
    all_entity_ids = set()
    for turn in parsed.get("turns", []):
        for action in turn.get("actions", []):
            eid = action.get("entity")
            if eid is not None:
                all_entity_ids.add(eid)

    opponent_ids = [eid for eid in all_entity_ids if eid != our_entity_id]
    if not opponent_ids:
        return None

    return classify_ai_behavior(parsed, opponent_ids[0])


# =============================================================================
# ALPHA STRIKE ANALYSIS (Tier 3 - Elite Meta Metrics)
# =============================================================================

from leekwars_agent.alpha_strike import (
    AlphaStrikeMetrics,
    AlphaStrikeFightSummary,
    TPMetrics,
    OpeningBuffs,
    OPENING_BUFF_CHIPS,
    HIGH_WIN_CHIPS,
    TOP_20_ACTIONS,
    is_opening_buff,
    is_high_win_chip,
    is_top_20_action,
    calculate_stat_cv,
    calculate_mobility_ratio,
)


def analyze_tp_efficiency(parsed_fight: dict, entity_id: int) -> dict[str, TPMetrics]:
    """Analyze TP efficiency per phase for an entity.

    Phases:
    - early: turns 0-2 (opening/setup)
    - mid: turns 3-10 (main combat)
    - late: turns 11+ (attrition)

    Returns dict with 'early', 'mid', 'late' TPMetrics.
    """
    tp_early = TPMetrics()
    tp_mid = TPMetrics()
    tp_late = TPMetrics()

    # Get entity's base TP from leeks data
    base_tp = 10  # Default
    for leek in parsed_fight.get("leeks", []):
        if leek.get("id") == entity_id:
            base_tp = leek.get("tp", 10)
            break

    for turn in parsed_fight.get("turns", []):
        turn_num = turn.get("number", 0)

        # Select phase
        if turn_num <= 2:
            phase_tp = tp_early
        elif turn_num <= 10:
            phase_tp = tp_mid
        else:
            phase_tp = tp_late

        # Count actions for this entity in this turn
        entity_actions = 0
        for action in turn.get("actions", []):
            if action.get("entity") == entity_id:
                action_type = action.get("type")
                if action_type in ("weapon", "chip", "move"):
                    entity_actions += 1

        # Estimate TP usage (rough: 1 action ≈ 3 TP average)
        # TODO: Use actual TP costs from GROUND_TRUTH
        estimated_tp_spent = min(entity_actions * 3, base_tp)

        phase_tp.tp_available += base_tp
        phase_tp.tp_spent += estimated_tp_spent

    return {
        "early": tp_early,
        "mid": tp_mid,
        "late": tp_late,
    }


def analyze_opening_buffs(parsed_fight: dict, entity_id: int) -> OpeningBuffs:
    """Analyze opening buff completion for an entity.

    Elite gatekeeper: 5/5 of [knowledge, adrenaline, elevation, armoring, steroid]
    """
    alpha_data = parsed_fight.get("alpha_strike", {})
    entity_opening = alpha_data.get("opening_buffs", {}).get(entity_id, [])

    # Count gatekeeper buffs
    gatekeeper_ids = {
        OPENING_BUFF_CHIPS["knowledge"],
        OPENING_BUFF_CHIPS["adrenaline"],
        OPENING_BUFF_CHIPS["elevation"],
        OPENING_BUFF_CHIPS["armoring"],
        OPENING_BUFF_CHIPS["steroid"],
    }

    gatekeeper_count = sum(1 for chip_id in entity_opening if chip_id in gatekeeper_ids)

    return OpeningBuffs(
        buffs_used=entity_opening,
        gatekeeper_count=gatekeeper_count,
        total_buffs=len(entity_opening),
    )


def analyze_high_win_chips(parsed_fight: dict, entity_id: int) -> list[int]:
    """Get list of high-win chips used by entity."""
    alpha_data = parsed_fight.get("alpha_strike", {})
    entity_chips = alpha_data.get("entity_chips", {}).get(entity_id, [])

    return [chip_id for chip_id in entity_chips if is_high_win_chip(chip_id)]


def analyze_top_20_count(parsed_fight: dict, entity_id: int) -> int:
    """Count how many top-20 quality actions entity used."""
    alpha_data = parsed_fight.get("alpha_strike", {})
    entity_chips = alpha_data.get("entity_chips", {}).get(entity_id, [])
    entity_weapons = alpha_data.get("entity_weapons", {}).get(entity_id, [])

    count = 0
    for chip_id in entity_chips:
        if is_top_20_action(chip_id):
            count += 1
    for weapon_id in entity_weapons:
        if is_top_20_action(weapon_id):
            count += 1

    return count


def estimate_ponr_turn(parsed_fight: dict) -> int | None:
    """Estimate Point of No Return turn.

    PONR = turn when fight outcome became ~80% certain.
    Based on HP advantage crossing threshold.

    Returns turn number or None if can't determine.
    """
    # Get entity IDs by team
    leeks = parsed_fight.get("leeks", [])
    if len(leeks) < 2:
        return None

    # Simple heuristic: find turn where HP ratio exceeds 2:1
    # TODO: More sophisticated PONR estimation

    turns = parsed_fight.get("turns", [])
    winner = parsed_fight.get("winner")

    if winner is None or winner == 0:  # Draw
        return None

    # Track cumulative damage per entity
    entity_damage = {}
    for turn in turns:
        turn_num = turn.get("number", 0)

        for action in turn.get("actions", []):
            if action.get("type") == "damage":
                entity_id = action.get("entity")
                damage = action.get("amount", 0)
                entity_damage[entity_id] = entity_damage.get(entity_id, 0) + damage

        # Check if damage ratio is decisive (2:1 or more)
        damages = list(entity_damage.values())
        if len(damages) >= 2:
            max_dmg = max(damages)
            min_dmg = min(damages) or 1
            if max_dmg / min_dmg >= 2.0:
                return turn_num

    return None


def analyze_alpha_strike(parsed_fight: dict) -> AlphaStrikeFightSummary:
    """Full Alpha Strike analysis for a fight.

    Returns summary with metrics for both teams and deltas.
    """
    fight_id = parsed_fight.get("id", 0)
    winner = parsed_fight.get("winner", 0)
    duration = parsed_fight.get("summary", {}).get("turns", 0)

    # Get entity IDs
    all_entity_ids = set()
    for turn in parsed_fight.get("turns", []):
        for action in turn.get("actions", []):
            eid = action.get("entity")
            if eid is not None:
                all_entity_ids.add(eid)

    entity_ids = sorted(all_entity_ids)
    team1_id = entity_ids[0] if len(entity_ids) > 0 else None
    team2_id = entity_ids[1] if len(entity_ids) > 1 else None

    # Analyze each team
    team1_metrics = None
    team2_metrics = None

    if team1_id is not None:
        tp_phases = analyze_tp_efficiency(parsed_fight, team1_id)
        team1_metrics = AlphaStrikeMetrics(
            entity_id=team1_id,
            tp_early=tp_phases["early"],
            tp_mid=tp_phases["mid"],
            tp_late=tp_phases["late"],
            opening_buffs=analyze_opening_buffs(parsed_fight, team1_id),
            high_win_chips_used=analyze_high_win_chips(parsed_fight, team1_id),
            top_20_actions_count=analyze_top_20_count(parsed_fight, team1_id),
        )

    if team2_id is not None:
        tp_phases = analyze_tp_efficiency(parsed_fight, team2_id)
        team2_metrics = AlphaStrikeMetrics(
            entity_id=team2_id,
            tp_early=tp_phases["early"],
            tp_mid=tp_phases["mid"],
            tp_late=tp_phases["late"],
            opening_buffs=analyze_opening_buffs(parsed_fight, team2_id),
            high_win_chips_used=analyze_high_win_chips(parsed_fight, team2_id),
            top_20_actions_count=analyze_top_20_count(parsed_fight, team2_id),
        )

    # Calculate deltas
    opening_buff_delta = 0
    tp_efficiency_delta = 0.0
    high_win_delta = 0

    if team1_metrics and team2_metrics:
        opening_buff_delta = (
            team1_metrics.opening_buffs.gatekeeper_count -
            team2_metrics.opening_buffs.gatekeeper_count
        )
        tp_efficiency_delta = (
            team1_metrics.overall_tp_efficiency -
            team2_metrics.overall_tp_efficiency
        )
        high_win_delta = (
            len(team1_metrics.high_win_chips_used) -
            len(team2_metrics.high_win_chips_used)
        )

    ponr = estimate_ponr_turn(parsed_fight)

    return AlphaStrikeFightSummary(
        fight_id=fight_id,
        winner=winner,
        duration=duration,
        team1_metrics=team1_metrics,
        team2_metrics=team2_metrics,
        opening_buff_delta=opening_buff_delta,
        tp_efficiency_delta=tp_efficiency_delta,
        high_win_chip_delta=high_win_delta,
        ponr_turn=ponr,
    )


def print_alpha_strike_analysis(summary: AlphaStrikeFightSummary):
    """Pretty-print Alpha Strike analysis."""
    print("=== ALPHA STRIKE ANALYSIS ===")
    print(f"Fight #{summary.fight_id}")
    print(f"Winner: Team {summary.winner} | Duration: {summary.duration} turns")

    if summary.ponr_turn:
        print(f"PONR: Turn {summary.ponr_turn} (fight decided early)")

    print("\n--- Opening Buffs (Gatekeeper: 5/5) ---")
    if summary.team1_metrics:
        t1_ob = summary.team1_metrics.opening_buffs
        print(f"  Team 1: {t1_ob.gatekeeper_count}/5 gatekeeper, {t1_ob.total_buffs} total")
    if summary.team2_metrics:
        t2_ob = summary.team2_metrics.opening_buffs
        print(f"  Team 2: {t2_ob.gatekeeper_count}/5 gatekeeper, {t2_ob.total_buffs} total")
    print(f"  Delta: {summary.opening_buff_delta:+d}")

    print("\n--- TP Efficiency (Target: ≥0.9) ---")
    if summary.team1_metrics:
        eff = summary.team1_metrics.overall_tp_efficiency
        status = "✓" if eff >= 0.9 else "⚠"
        print(f"  Team 1: {eff:.2f} {status}")
    if summary.team2_metrics:
        eff = summary.team2_metrics.overall_tp_efficiency
        status = "✓" if eff >= 0.9 else "⚠"
        print(f"  Team 2: {eff:.2f} {status}")

    print("\n--- High-Win Chips ---")
    if summary.team1_metrics:
        hwc = summary.team1_metrics.high_win_chips_used
        print(f"  Team 1: {len(hwc)}/5 ({hwc})")
    if summary.team2_metrics:
        hwc = summary.team2_metrics.high_win_chips_used
        print(f"  Team 2: {len(hwc)}/5 ({hwc})")
    print(f"  Delta: {summary.high_win_chip_delta:+d}")
