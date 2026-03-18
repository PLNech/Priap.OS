#!/usr/bin/env python3
"""Movement analysis for #0209: Quantify wasted shields and missed weapon opportunities.

Parses fight replays from fights_meta.db to compute per-turn position tracking,
resource usage, and shield/weapon efficiency metrics.

Metrics:
    - shield_waste_rate: % turns shields cast when dist > 10
    - weapon_miss_rate: % turns in weapon range but 0 weapon attacks (TP exhausted)
    - avg_approach_turns: turns spent with dist > weapon max range before first weapon attack
    - tp_budget: avg TP split per turn (shields/weapon/chips/unspent)
    - weapon_fire_rate: % turns with at least 1 USE_WEAPON action
"""

import json
import sqlite3
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY

# Constants
IADONIS_LEEK_ID = 131321
IADONIS_FARMER_ID = 124831
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fights_meta.db"

# Action codes (from fight_parser.py / fight.py)
NEW_TURN = 6
ENTITY_TURN = 7
END_TURN = 8
MOVE_TO = 10
USE_CHIP = 12
SET_WEAPON = 13
USE_WEAPON = 16
LOST_LIFE = 101
HEAL = 103

# Cell distance (from Pathfinding.java:26-28, leek-wars-generator)
# The map uses a stride of (width * 2 - 1) = 35 for an 18-wide map.
MAP_WIDTH = 18
STRIDE = MAP_WIDTH * 2 - 1  # 35


def cell_distance(c1: int, c2: int) -> int:
    """Manhattan distance on the LeekWars hex-like grid.

    Source: tools/leek-wars-generator/.../Pathfinding.java:26-28
    getCaseDistance uses |x1-x2| + |y1-y2| on the stride-35 grid.
    """
    x1, y1 = c1 % STRIDE, c1 // STRIDE
    x2, y2 = c2 % STRIDE, c2 // STRIDE
    return abs(x1 - x2) + abs(y1 - y2)


# Chip classification by template ID
def classify_chip(template_id: int) -> str:
    """Classify a chip template as shield/damage/buff/debuff/heal."""
    chip = CHIP_REGISTRY.by_template(template_id)
    if chip is None:
        return "unknown"
    name = chip.name.lower()
    if name in ("helmet", "shield", "armor", "carapace", "rampart", "fortress"):
        return "shield"
    if name in ("flame", "flash", "spark", "rock", "ice", "shock"):
        return "damage"
    if name in ("motivation", "ferocity", "rage", "protein", "steroid"):
        return "buff"
    if name in ("tranquilizer", "slow_down", "ball_and_chain"):
        return "debuff"
    if name in ("cure", "bandage", "drip", "regeneration", "remission"):
        return "heal"
    # Fallback: check effects
    for eff in chip.effects:
        if eff.type == 4:  # shield
            return "shield"
        if eff.type == 1:  # damage
            return "damage"
        if eff.type == 2:  # heal
            return "heal"
    return "other"


@dataclass
class TurnData:
    """Per-turn data for one entity."""
    turn_num: int
    entity_id: int
    cell_start: int = -1
    cell_end: int = -1
    enemy_cell: int = -1
    dist_start: int = -1
    dist_end: int = -1
    tp_on_shields: int = 0
    tp_on_weapons: int = 0
    tp_on_damage_chips: int = 0
    tp_on_buffs: int = 0
    tp_on_debuffs: int = 0
    tp_on_heals: int = 0
    mp_spent: int = 0
    weapon_attacks: int = 0
    chip_attacks: int = 0
    shield_casts: int = 0
    damage_dealt: int = 0
    healing_received: int = 0
    in_weapon_range: bool = False
    weapon_max_range: int = 8  # b_laser default


@dataclass
class FightAnalysis:
    """Analysis results for one fight."""
    fight_id: int
    won: bool
    total_turns: int = 0
    iadonis_turns: list = field(default_factory=list)
    first_weapon_turn: int = -1  # turn number of first weapon attack


def find_iadonis_entity(fight_data: dict) -> int | None:
    """Find IAdonis entity ID in fight replay."""
    fight = fight_data.get("fight", fight_data)
    data = fight.get("data", {})
    leeks = data.get("leeks", [])
    for entity in leeks:
        if entity.get("name") == "IAdonis":
            return entity.get("id")
    return None


def find_enemy_entity(fight_data: dict, iadonis_eid: int) -> int | None:
    """Find the main enemy entity (non-summon, different team)."""
    fight = fight_data.get("fight", fight_data)
    data = fight.get("data", {})
    leeks = data.get("leeks", [])
    iadonis_team = None
    for entity in leeks:
        if entity.get("id") == iadonis_eid:
            iadonis_team = entity.get("team")
            break
    if iadonis_team is None:
        return None
    for entity in leeks:
        if entity.get("team") != iadonis_team and not entity.get("summon"):
            return entity.get("id")
    return None


def get_entity_cell_pos(fight_data: dict) -> dict[int, int]:
    """Extract initial cell positions from fight data."""
    fight = fight_data.get("fight", fight_data)
    data = fight.get("data", {})
    positions = {}
    for entity in data.get("leeks", []):
        eid = entity.get("id")
        cell = entity.get("cellPos")
        if eid is not None and cell is not None:
            positions[eid] = cell
    return positions


def get_weapon_max_range(fight_data: dict, iadonis_eid: int) -> int:
    """Get IAdonis max weapon range from equipped weapons."""
    fight = fight_data.get("fight", fight_data)
    data = fight.get("data", {})
    for entity in data.get("leeks", []):
        if entity.get("id") == iadonis_eid:
            weapons = entity.get("weapons", [])
            max_r = 0
            for wid in weapons:
                w = WEAPON_REGISTRY.by_id(wid)
                if w and w.max_range > max_r:
                    max_r = w.max_range
            return max_r if max_r > 0 else 8
    return 8


def analyze_fight(fight_data: dict) -> FightAnalysis | None:
    """Analyze a single fight for movement/resource metrics."""
    fight = fight_data.get("fight", fight_data)
    data = fight.get("data", {})
    actions = data.get("actions", [])
    if not actions:
        return None

    iadonis_eid = find_iadonis_entity(fight_data)
    if iadonis_eid is None:
        return None

    enemy_eid = find_enemy_entity(fight_data, iadonis_eid)
    if enemy_eid is None:
        return None

    # Did IAdonis win?
    winner = fight.get("winner", 0)
    iadonis_team = None
    for entity in data.get("leeks", []):
        if entity.get("id") == iadonis_eid:
            iadonis_team = entity.get("team")
            break
    won = (winner == iadonis_team)

    # Initial positions
    positions = get_entity_cell_pos(fight_data)
    current_pos = dict(positions)

    weapon_max_range = get_weapon_max_range(fight_data, iadonis_eid)

    analysis = FightAnalysis(fight_id=fight.get("id", 0), won=won)

    current_entity = None
    current_turn_num = 0
    current_turn_data = None

    for action in actions:
        if not action:
            continue
        code = action[0]

        if code == NEW_TURN:
            current_turn_num = action[1] if len(action) > 1 else current_turn_num + 1
            analysis.total_turns = current_turn_num

        elif code == ENTITY_TURN:
            # Save previous turn data
            if current_turn_data and current_turn_data.entity_id == iadonis_eid:
                current_turn_data.cell_end = current_pos.get(iadonis_eid, -1)
                enemy_cell = current_pos.get(enemy_eid, -1)
                if current_turn_data.cell_end >= 0 and enemy_cell >= 0:
                    current_turn_data.dist_end = cell_distance(current_turn_data.cell_end, enemy_cell)
                analysis.iadonis_turns.append(current_turn_data)

            current_entity = action[1] if len(action) > 1 else None

            if current_entity == iadonis_eid:
                my_cell = current_pos.get(iadonis_eid, -1)
                enemy_cell = current_pos.get(enemy_eid, -1)
                dist = cell_distance(my_cell, enemy_cell) if my_cell >= 0 and enemy_cell >= 0 else -1

                current_turn_data = TurnData(
                    turn_num=current_turn_num,
                    entity_id=iadonis_eid,
                    cell_start=my_cell,
                    enemy_cell=enemy_cell,
                    dist_start=dist,
                    weapon_max_range=weapon_max_range,
                    in_weapon_range=(0 < dist <= weapon_max_range) if dist > 0 else False,
                )
            else:
                current_turn_data = None

        elif code == MOVE_TO:
            eid = action[1] if len(action) > 1 else None
            target_cell = action[2] if len(action) > 2 else None
            path = action[3] if len(action) > 3 and isinstance(action[3], list) else []

            if target_cell is not None and eid is not None:
                current_pos[eid] = target_cell

            if eid == iadonis_eid and current_turn_data:
                current_turn_data.mp_spent += len(path) if path else 1

        elif code == USE_CHIP:
            chip_template = action[1] if len(action) > 1 else None
            if current_entity == iadonis_eid and current_turn_data and chip_template is not None:
                chip = CHIP_REGISTRY.by_template(chip_template)
                tp_cost = chip.cost if chip else 0
                category = classify_chip(chip_template)

                if category == "shield":
                    current_turn_data.tp_on_shields += tp_cost
                    current_turn_data.shield_casts += 1
                elif category == "damage":
                    current_turn_data.tp_on_damage_chips += tp_cost
                    current_turn_data.chip_attacks += 1
                elif category == "buff":
                    current_turn_data.tp_on_buffs += tp_cost
                elif category == "debuff":
                    current_turn_data.tp_on_debuffs += tp_cost
                elif category == "heal":
                    current_turn_data.tp_on_heals += tp_cost

        elif code == SET_WEAPON:
            # setWeapon costs 1 TP
            if current_entity == iadonis_eid and current_turn_data:
                current_turn_data.tp_on_weapons += 1

        elif code == USE_WEAPON:
            if current_entity == iadonis_eid and current_turn_data:
                weapon_template = action[1] if len(action) > 1 else None
                weapon = WEAPON_REGISTRY.by_template(weapon_template) if weapon_template else None
                tp_cost = weapon.cost if weapon else 5
                current_turn_data.tp_on_weapons += tp_cost
                current_turn_data.weapon_attacks += 1

                if analysis.first_weapon_turn < 0:
                    analysis.first_weapon_turn = current_turn_num

        elif code == LOST_LIFE:
            eid = action[1] if len(action) > 1 else None
            damage = action[2] if len(action) > 2 else 0
            if current_entity == iadonis_eid and eid != iadonis_eid and current_turn_data:
                current_turn_data.damage_dealt += damage

        elif code == HEAL:
            eid = action[1] if len(action) > 1 else None
            amount = action[2] if len(action) > 2 else 0
            if eid == iadonis_eid and current_turn_data:
                current_turn_data.healing_received += amount

    # Save last turn
    if current_turn_data and current_turn_data.entity_id == iadonis_eid:
        current_turn_data.cell_end = current_pos.get(iadonis_eid, -1)
        enemy_cell = current_pos.get(enemy_eid, -1)
        if current_turn_data.cell_end >= 0 and enemy_cell >= 0:
            current_turn_data.dist_end = cell_distance(current_turn_data.cell_end, enemy_cell)
        analysis.iadonis_turns.append(current_turn_data)

    return analysis


def compute_metrics(analyses: list[FightAnalysis]) -> dict:
    """Compute aggregate metrics across all fights."""
    total_turns = 0
    shield_at_distance = 0  # turns where shields cast and dist > 10
    shield_total = 0        # turns where shields cast
    weapon_miss = 0         # turns in weapon range but 0 weapon attacks
    in_range_turns = 0      # turns where in weapon range
    weapon_fire_turns = 0   # turns with at least 1 weapon attack
    approach_turns_list = []  # per-fight approach turns before first weapon

    # TP budget accumulators
    tp_shields_total = 0
    tp_weapons_total = 0
    tp_damage_chips_total = 0
    tp_buffs_total = 0
    tp_debuffs_total = 0
    tp_heals_total = 0

    # Per-turn type counters
    move_only_turns = 0
    chip_only_turns = 0
    weapon_turns = 0
    mixed_turns = 0

    for analysis in analyses:
        for t in analysis.iadonis_turns:
            total_turns += 1

            # Shield waste: cast at distance > 10
            if t.shield_casts > 0:
                shield_total += 1
                if t.dist_start > 10:
                    shield_at_distance += 1

            # Weapon miss: in range but no weapon attack
            if t.in_weapon_range:
                in_range_turns += 1
                if t.weapon_attacks == 0:
                    weapon_miss += 1

            if t.weapon_attacks > 0:
                weapon_fire_turns += 1

            # TP budget
            tp_shields_total += t.tp_on_shields
            tp_weapons_total += t.tp_on_weapons
            tp_damage_chips_total += t.tp_on_damage_chips
            tp_buffs_total += t.tp_on_buffs
            tp_debuffs_total += t.tp_on_debuffs
            tp_heals_total += t.tp_on_heals

            # Turn type classification
            has_attack = (t.weapon_attacks > 0 or t.chip_attacks > 0)
            has_move = (t.mp_spent > 0)
            has_chip_only = (t.chip_attacks > 0 and t.weapon_attacks == 0)

            if has_move and not has_attack and t.shield_casts == 0:
                move_only_turns += 1
            elif has_chip_only and not has_move and t.weapon_attacks == 0:
                chip_only_turns += 1
            elif t.weapon_attacks > 0:
                weapon_turns += 1
            else:
                mixed_turns += 1

        # Approach turns: turns before first weapon attack
        if analysis.first_weapon_turn >= 0:
            approach = 0
            for t in analysis.iadonis_turns:
                if t.turn_num < analysis.first_weapon_turn:
                    if t.dist_start > t.weapon_max_range:
                        approach += 1
            approach_turns_list.append(approach)

    # Compute rates
    shield_waste_rate = (shield_at_distance / shield_total * 100) if shield_total > 0 else 0
    weapon_miss_rate = (weapon_miss / in_range_turns * 100) if in_range_turns > 0 else 0
    weapon_fire_rate = (weapon_fire_turns / total_turns * 100) if total_turns > 0 else 0
    avg_approach = sum(approach_turns_list) / len(approach_turns_list) if approach_turns_list else 0

    # TP budget per turn
    tp_total_spent = (tp_shields_total + tp_weapons_total + tp_damage_chips_total +
                      tp_buffs_total + tp_debuffs_total + tp_heals_total)
    tp_per_turn = tp_total_spent / total_turns if total_turns > 0 else 0

    return {
        "fights_analyzed": len(analyses),
        "wins": sum(1 for a in analyses if a.won),
        "total_iadonis_turns": total_turns,
        "shield_waste_rate": shield_waste_rate,
        "shield_at_distance": shield_at_distance,
        "shield_total_turns": shield_total,
        "weapon_miss_rate": weapon_miss_rate,
        "weapon_miss_turns": weapon_miss,
        "in_range_turns": in_range_turns,
        "weapon_fire_rate": weapon_fire_rate,
        "weapon_fire_turns": weapon_fire_turns,
        "avg_approach_turns": avg_approach,
        "approach_turns_list": approach_turns_list,
        "tp_budget": {
            "shields": tp_shields_total,
            "weapons": tp_weapons_total,
            "damage_chips": tp_damage_chips_total,
            "buffs": tp_buffs_total,
            "debuffs": tp_debuffs_total,
            "heals": tp_heals_total,
            "total_spent": tp_total_spent,
            "per_turn_avg": tp_per_turn,
        },
        "tp_pct": {
            "shields": (tp_shields_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
            "weapons": (tp_weapons_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
            "damage_chips": (tp_damage_chips_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
            "buffs": (tp_buffs_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
            "debuffs": (tp_debuffs_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
            "heals": (tp_heals_total / tp_total_spent * 100) if tp_total_spent > 0 else 0,
        },
        "turn_types": {
            "move_only": move_only_turns,
            "chip_only": chip_only_turns,
            "weapon": weapon_turns,
            "mixed": mixed_turns,
            "move_only_pct": (move_only_turns / total_turns * 100) if total_turns > 0 else 0,
            "chip_only_pct": (chip_only_turns / total_turns * 100) if total_turns > 0 else 0,
            "weapon_pct": (weapon_turns / total_turns * 100) if total_turns > 0 else 0,
        },
    }


def format_report(metrics: dict) -> str:
    """Format metrics into a readable report."""
    m = metrics
    tp = m["tp_budget"]
    pct = m["tp_pct"]
    tt = m["turn_types"]

    lines = [
        "# Movement Analysis — v14 Phalanx Baseline (S36)",
        "",
        f"**Fights analyzed**: {m['fights_analyzed']} (IAdonis matchmaking, context=2)",
        f"**Win rate**: {m['wins']}/{m['fights_analyzed']} ({m['wins']/m['fights_analyzed']*100:.0f}%)" if m['fights_analyzed'] > 0 else "",
        f"**Total IAdonis turns**: {m['total_iadonis_turns']}",
        f"**Avg turns/fight**: {m['total_iadonis_turns']/m['fights_analyzed']:.1f}" if m['fights_analyzed'] > 0 else "",
        "",
        "---",
        "",
        "## Key Metrics",
        "",
        "| Metric | Value | Detail |",
        "|--------|-------|--------|",
        f"| **Shield waste rate** | {m['shield_waste_rate']:.1f}% | {m['shield_at_distance']}/{m['shield_total_turns']} turns shields cast at dist > 10 |",
        f"| **Weapon miss rate** | {m['weapon_miss_rate']:.1f}% | {m['weapon_miss_turns']}/{m['in_range_turns']} turns in weapon range but 0 attacks |",
        f"| **Weapon fire rate** | {m['weapon_fire_rate']:.1f}% | {m['weapon_fire_turns']}/{m['total_iadonis_turns']} turns with weapon attack |",
        f"| **Avg approach turns** | {m['avg_approach_turns']:.1f} | Turns at dist > weapon range before first weapon fire |",
        "",
        "## TP Budget (per turn average)",
        "",
        f"Total TP spent: {tp['total_spent']} over {m['total_iadonis_turns']} turns = **{tp['per_turn_avg']:.1f} TP/turn**",
        "",
        "| Category | Total TP | % of Budget |",
        "|----------|----------|-------------|",
        f"| Shields | {tp['shields']} | **{pct['shields']:.1f}%** |",
        f"| Weapons | {tp['weapons']} | {pct['weapons']:.1f}% |",
        f"| Damage chips (Flame) | {tp['damage_chips']} | {pct['damage_chips']:.1f}% |",
        f"| Buffs (Motivation) | {tp['buffs']} | {pct['buffs']:.1f}% |",
        f"| Debuffs (Tranq) | {tp['debuffs']} | {pct['debuffs']:.1f}% |",
        f"| Heals | {tp['heals']} | {pct.get('heals', 0):.1f}% |",
        "",
        "## Turn Type Breakdown",
        "",
        "| Turn Type | Count | % |",
        "|-----------|-------|---|",
        f"| Move-only (no attack, no shield) | {tt['move_only']} | {tt['move_only_pct']:.1f}% |",
        f"| Chip-only (no weapon) | {tt['chip_only']} | {tt['chip_only_pct']:.1f}% |",
        f"| Weapon turn | {tt['weapon']} | {tt['weapon_pct']:.1f}% |",
        f"| Mixed/Other | {tt['mixed']} | {(100 - tt['move_only_pct'] - tt['chip_only_pct'] - tt['weapon_pct']):.1f}% |",
        "",
        "## Approach Turns Distribution",
        "",
    ]

    if m["approach_turns_list"]:
        from collections import Counter
        dist = Counter(m["approach_turns_list"])
        lines.append("| Approach turns | Fights |")
        lines.append("|----------------|--------|")
        for k in sorted(dist.keys()):
            lines.append(f"| {k} | {dist[k]} |")

    lines.extend([
        "",
        "---",
        "",
        "## Implications for #0209 Movement Rework",
        "",
        f"1. **Shield waste is {'HIGH' if m['shield_waste_rate'] > 20 else 'moderate' if m['shield_waste_rate'] > 10 else 'low'}** "
        f"({m['shield_waste_rate']:.0f}%): "
        f"{'Distance gate on shields will save significant TP' if m['shield_waste_rate'] > 20 else 'Some savings possible from distance gating'}",
        "",
        f"2. **Weapon fires in only {m['weapon_fire_rate']:.0f}% of turns**: "
        f"{'Critical: weapon almost never fires. TP reservation + Move→Attack→Defend will fix this' if m['weapon_fire_rate'] < 25 else 'Moderate weapon usage — still room for improvement'}",
        "",
        f"3. **TP budget dominated by shields ({pct['shields']:.0f}%)**: "
        f"{'Confirms hypothesis: shields eat TP before weapon gets a chance' if pct['shields'] > 40 else 'Shields take significant budget share'}",
        "",
        f"4. **{tt['move_only_pct']:.0f}% turns are move-only**: "
        f"{'High approach overhead — faster positioning would help' if tt['move_only_pct'] > 15 else 'Approach overhead is manageable'}",
    ])

    return "\n".join(lines)


def main():
    n_fights = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Get N most recent IAdonis matchmaking fights
    cursor.execute("""
        SELECT fight_id, json_data FROM fights
        WHERE json_data LIKE '%IAdonis%' AND context = 2
        ORDER BY fight_date DESC
        LIMIT ?
    """, (n_fights,))

    analyses = []
    errors = 0

    for fight_id, json_str in cursor.fetchall():
        try:
            fight_data = json.loads(json_str)
            result = analyze_fight(fight_data)
            if result:
                analyses.append(result)
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  Error parsing fight {fight_id}: {e}", file=sys.stderr)

    conn.close()

    if not analyses:
        print("No fights analyzed!", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzed {len(analyses)} fights ({errors} errors)")

    metrics = compute_metrics(analyses)

    # Print summary to stdout
    report = format_report(metrics)
    print(report)

    # Save to research file
    output_path = Path(__file__).resolve().parent.parent / "docs" / "research" / "movement_analysis_s36.md"
    output_path.write_text(report)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
