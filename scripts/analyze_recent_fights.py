#!/usr/bin/env python3
"""Analyze recent online fights — reusable post-fight intelligence tool.

Usage:
    poetry run python scripts/analyze_recent_fights.py                  # last 5 garden fights
    poetry run python scripts/analyze_recent_fights.py -n 10            # last 10
    poetry run python scripts/analyze_recent_fights.py --ids 123 456    # specific fight IDs
    poetry run python scripts/analyze_recent_fights.py --all-contexts   # include test/tourney

Outputs per-fight breakdown (opponent stats, damage dealt/taken, chips used, duration)
and an aggregate summary. Designed to be run after every fight batch to validate AI changes.
"""

import argparse
import json
import sys
import os
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from leekwars_agent.auth import login_api

OUR_LEEK = "IAdonis"

# Chip name lookup by TEMPLATE ID (fight actions use template IDs, not chip IDs)
# Source: tools/leek-wars/src/model/chips.ts
CHIP_NAMES = {
    1: "Bandage", 2: "Cure", 3: "Drip", 4: "Regeneration", 5: "Vaccine",
    6: "Shock", 7: "Flash", 8: "Lightning", 9: "Spark", 10: "Flame",
    11: "Meteorite", 12: "Pebble", 13: "Rock", 14: "Rockfall", 15: "Ice",
    16: "Stalactite", 17: "Iceberg", 18: "Shield", 19: "Helmet", 20: "Armor",
    21: "Wall", 22: "Rampart", 23: "Fortress", 24: "Protein", 25: "Steroid",
    26: "Doping", 27: "Stretching", 28: "WarmUp", 29: "Reflexes",
    30: "LeatherBoots", 31: "WingedBoots", 33: "Motivation", 34: "Adrenaline",
    35: "Rage", 36: "Liberation", 37: "Teleportation", 38: "Armoring",
    40: "PunyBulb", 41: "FireBulb", 42: "HealerBulb", 43: "RockyBulb",
    44: "IcedBulb", 45: "LightningBulb", 46: "MetallicBulb",
    47: "Remission", 48: "Carapace", 49: "Resurrection", 50: "DevilStrike",
    51: "Whip", 54: "Acceleration", 55: "SlowDown", 56: "BallAndChain",
    57: "Tranquilizer", 58: "Soporific", 59: "Fracture", 60: "Solidification",
    61: "Venom", 62: "Toxin", 63: "Plague", 64: "Thorn", 65: "Mirror",
    66: "Ferocity", 67: "Collar", 68: "Bark", 69: "Burning", 70: "Antidote",
    71: "Punishment", 72: "Covetousness", 73: "Vampirization",
    80: "Elevation", 81: "Knowledge", 88: "Grapple", 89: "BoxingGlove",
    97: "Arsenic", 98: "Bramble", 99: "Dome", 109: "Awakening",
}


def chip_name(cid):
    return CHIP_NAMES.get(cid, f"chip#{cid}")


def analyze_fight(api, fid):
    """Analyze a single fight. Returns a summary dict."""
    raw = api.get_fight(fid)
    fight = raw.get("fight", raw)
    data = fight.get("data", {})
    leeks = data.get("leeks", [])
    actions = data.get("actions", [])
    winner = fight.get("winner", "?")
    duration = fight.get("report", {}).get("duration", "?")
    context = fight.get("context", 0)

    us = None
    them = None
    bulbs = []
    our_farmer = None
    for l in leeks:
        if l.get("name") == OUR_LEEK:
            us = l
            our_farmer = l.get("farmer")

    # Collect all enemies, pick highest-level as main opponent
    enemies = []
    for l in leeks:
        if l.get("name") == OUR_LEEK:
            continue
        if us and l.get("team") != us.get("team"):
            enemies.append(l)
        elif not us:
            enemies.append(l)

    if enemies:
        # Main opponent = highest level enemy (bulbs are lower level)
        enemies.sort(key=lambda x: x.get("level", 0), reverse=True)
        them = enemies[0]
        bulbs = enemies[1:]

    if them is None:
        others = [l for l in leeks if l.get("name") != OUR_LEEK]
        them = others[0] if others else {}

    our_team = us.get("team", 2) if us else 2
    won = winner == our_team
    our_id = us.get("id", 1) if us else 1

    our_dmg = their_dmg = our_heals = their_heals = 0
    our_chips = []
    their_chips = []
    our_weapons_used = 0
    their_weapons_used = 0
    cur_entity = None

    for a in actions:
        code = a[0]
        if code == 7:  # ENTITY_TURN
            cur_entity = a[1]
        elif code == 101:  # DAMAGE
            target, dmg = a[1], a[2]
            if target == our_id:
                their_dmg += dmg
            else:
                our_dmg += dmg
        elif code == 102:  # HEAL
            target, amt = a[1], a[2]
            if target == our_id:
                our_heals += amt
            else:
                their_heals += amt
        elif code == 12:  # USE_CHIP
            chip_id = a[1]
            if cur_entity == our_id:
                our_chips.append(chip_id)
            else:
                their_chips.append(chip_id)
        elif code == 16:  # USE_WEAPON
            if cur_entity == our_id:
                our_weapons_used += 1
            else:
                their_weapons_used += 1

    return {
        "id": fid,
        "won": won,
        "duration": duration,
        "context": {1: "garden", 2: "test", 3: "tourney"}.get(context, f"ctx{context}"),
        "opp_name": them.get("name"),
        "opp_level": them.get("level"),
        "opp_hp": them.get("life"),
        "opp_str": them.get("strength"),
        "opp_agi": them.get("agility"),
        "opp_res": them.get("resistance"),
        "opp_wis": them.get("wisdom"),
        "opp_tp": them.get("tp"),
        "opp_mp": them.get("mp"),
        "our_dmg": our_dmg,
        "their_dmg": their_dmg,
        "our_heals": our_heals,
        "their_heals": their_heals,
        "our_chips": dict(Counter(our_chips)),
        "their_chips": dict(Counter(their_chips)),
        "our_weapons_used": our_weapons_used,
        "their_weapons_used": their_weapons_used,
        "has_bulb": len(bulbs) > 0,
        "bulb_names": [b.get("name", "?") for b in bulbs],
    }


def print_fight(s):
    """Print a single fight summary."""
    result = "\033[32mWIN\033[0m" if s["won"] else "\033[31mLOSS\033[0m"
    print(f"Fight {s['id']} | {result} in {s['duration']}t | vs {s['opp_name']} L{s['opp_level']} [{s['context']}]")
    print(f"  THEM: HP={s['opp_hp']:>4} STR={s['opp_str']:>3} AGI={s['opp_agi']:>3} RES={s['opp_res']:>3} WIS={s['opp_wis']:>3} TP={s['opp_tp']:>2} MP={s['opp_mp']:>2}")
    print(f"  Dmg dealt: {s['our_dmg']:>4} | Dmg taken: {s['their_dmg']:>4} | Our heals: {s['our_heals']:>4} | Their heals: {s['their_heals']:>4}")
    print(f"  Our weapons: {s['our_weapons_used']}x | Their weapons: {s['their_weapons_used']}x")

    our_chips_str = ", ".join(f"{chip_name(k)}x{v}" for k, v in sorted(s["our_chips"].items()))
    their_chips_str = ", ".join(f"{chip_name(k)}x{v}" for k, v in sorted(s["their_chips"].items()))
    print(f"  Our chips: {our_chips_str or 'none'}")
    print(f"  Their chips: {their_chips_str or 'none'}")

    if s["has_bulb"]:
        print(f"  Bulb(s): {', '.join(s['bulb_names'])}")
    print()


def print_summary(fights):
    """Print aggregate summary."""
    wins = sum(1 for s in fights if s["won"])
    losses = len(fights) - wins
    print("=" * 65)
    print(f"TOTAL: {wins}W-{losses}L ({100 * wins / len(fights):.0f}% WR) over {len(fights)} fights")

    durations = [s["duration"] for s in fights if isinstance(s["duration"], int)]
    if durations:
        print(f"Duration: avg {sum(durations)/len(durations):.1f}t (min {min(durations)}, max {max(durations)})")

    avg_dmg = sum(s["our_dmg"] for s in fights) / len(fights)
    avg_taken = sum(s["their_dmg"] for s in fights) / len(fights)
    avg_heal = sum(s["our_heals"] for s in fights) / len(fights)
    print(f"Avg damage dealt: {avg_dmg:.0f} | Avg taken: {avg_taken:.0f} | Avg heals: {avg_heal:.0f}")

    opp_levels = [s["opp_level"] for s in fights if s["opp_level"]]
    if opp_levels:
        print(f"Opponent levels: L{min(opp_levels)}-L{max(opp_levels)} (avg L{sum(opp_levels)/len(opp_levels):.0f})")

    # Win/loss by opponent level bracket
    brackets = {"<L100": [], "L100-120": [], "L120-140": [], "L140+": []}
    for s in fights:
        lvl = s.get("opp_level", 0)
        if lvl < 100:
            brackets["<L100"].append(s)
        elif lvl < 120:
            brackets["L100-120"].append(s)
        elif lvl < 140:
            brackets["L120-140"].append(s)
        else:
            brackets["L140+"].append(s)
    print("\nWR by opponent level:")
    for bracket, bfights in brackets.items():
        if bfights:
            bwins = sum(1 for f in bfights if f["won"])
            print(f"  {bracket:10s}: {bwins}W-{len(bfights)-bwins}L ({100*bwins/len(bfights):.0f}%)")

    # Bulb impact
    bulb_fights = [s for s in fights if s["has_bulb"]]
    no_bulb = [s for s in fights if not s["has_bulb"]]
    if bulb_fights and no_bulb:
        bwr = 100 * sum(1 for f in bulb_fights if f["won"]) / len(bulb_fights)
        nbwr = 100 * sum(1 for f in no_bulb if f["won"]) / len(no_bulb)
        print(f"\nBulb impact: vs bulb {bwr:.0f}% WR ({len(bulb_fights)}f) | no bulb {nbwr:.0f}% WR ({len(no_bulb)}f)")


def main():
    parser = argparse.ArgumentParser(description="Analyze recent online fights")
    parser.add_argument("-n", type=int, default=5, help="Number of recent fights to analyze")
    parser.add_argument("--ids", nargs="+", type=int, help="Specific fight IDs to analyze")
    parser.add_argument("--all-contexts", action="store_true", help="Include test and tournament fights")
    args = parser.parse_args()

    api = login_api()
    try:
        if args.ids:
            fight_ids = args.ids
        else:
            LEEK_ID = 131321
            data = api.get_leek_history(LEEK_ID)
            history = data.get("fights", [])
            if not args.all_contexts:
                history = [f for f in history if f.get("context") == 1]
            fight_ids = [f["id"] for f in history[:args.n]]

        if not fight_ids:
            print("No fights found. Run some fights first!")
            return

        print(f"Analyzing {len(fight_ids)} fights...\n")
        results = []
        for fid in fight_ids:
            s = analyze_fight(api, fid)
            print_fight(s)
            results.append(s)

        print_summary(results)

    finally:
        api.close()


if __name__ == "__main__":
    main()
