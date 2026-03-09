# v14 Phalanx Online Evaluation — Session 29

**Date**: 2026-03-09
**Fights**: 12 (10 matchmade + 2 garden)
**AI**: fighter_v14_flat (AI #460953, 806 lines)
**Build**: L112, TP 14, MP 4, HP 777, STR 452, RES 0

## Results

| Metric | Value |
|--------|-------|
| Overall WR | **50%** (6W-6L) |
| At-level WR (L100-120) | **60%** (6W-4L) |
| vs L120+ | 0% (0W-2L) |
| Avg damage dealt | 984 |
| Avg damage taken | 670 |
| Avg duration | 7.5 turns |
| Cure activations | 0 effective heals across 12 fights |
| vs Bulb users | 40% WR (2W-3L) |
| vs No-bulb | 57% WR (4W-3L) |

## Opponent Breakdown

| Fight | Opponent | Level | HP | STR | RES | Result | Our Dmg | Key Factor |
|-------|----------|-------|----|-----|-----|--------|---------|------------|
| 51742803 | laoka | 112 | 837 | 403 | 0 | **WIN** | 1232 | Punished glass cannon |
| 51742804 | SIGKILL | 112 | 853 | 200 | 200 | **WIN** | 1166 | Attrition win, 12 turns |
| 51742805 | Benji | 113 | 1168 | 262 | 146 | **WIN** | 1736 | 8 Flames, overwhelming |
| 51742806 | Keewica | 113 | 1112 | 380 | 4 | **WIN** | 1114 | Fast kill, 5 turns |
| 51742898 | Amoki | 113 | 668 | 461 | 0 | **WIN** | 668 | Low HP, easy target |
| 51742904 | vroum | 113 | 1096 | 300 | 40 | **WIN** | 1096 | Solid attrition |
| 51742801 | demontepneu | 112 | 1133 | 200 | 0 | LOSS | 1127 | Lost by 6 HP! |
| 51742900 | PoireauLiddle | 113 | 1024 | 344 | 247 | LOSS | 918 | 3 bulbs + RES 247 |
| 51742901 | HyppoFarm | 113 | 848 | 393 | 68 | LOSS | 709 | Burst kill turn 5 |
| 51742903 | Stanami | 113 | 792 | 512 | 10 | LOSS | 170 | **Kite death** |
| 51742356 | lipitipoireau | 132 | 903 | 222 | 76 | LOSS | 647 | L132 + bulb (2v1) |
| 51742346 | lipitipoireau | 132 | 903 | 222 | 76 | LOSS | 1226 | L132 + bulb (2v1) |

## Loss Pattern Analysis

### Pattern A: Kite Death (Stanami)
- Enemy has MP 4+ and ranged chips (Spark, range 0-6)
- We spend turns 1-2 buffing (Motivation+Armor+Shield+Helmet = 14 TP)
- Turns 3-4: just moving, 0 damage dealt
- Enemy does 400+ chip damage while we chase
- Only 1 Flame lands (turn 5) before death
- **Root cause**: defensive-first strategy wastes 2 turns vs kiters who match our MP

### Pattern B: Near-Miss (demontepneu)
- Dealt 1127 dmg vs 1133 HP — lost by 6 HP
- Opponent has high HP (1133) + 16 weapon attacks
- We actually outplayed them on damage-per-turn
- **Root cause**: just needed ~1 more Flame or slightly less time chasing

### Pattern C: Burst Death (HyppoFarm)
- Getting hit for 281+112 = 393 dmg in one turn
- High-STR opponent + Protein buff + weapon
- We dealt 709 (needed 890 to kill)
- **Root cause**: no way to survive 400+ burst with 777 HP and no RES

### Pattern D: Swarm (PoireauLiddle)
- 3 puny bulbs + RES 247 + Bandagex15
- Extreme attrition build we can't outdamage
- **Root cause**: we lack the sustained DPS to out-heal their recovery

## Key Findings

### 1. Cure is Dead Weight
Zero effective heals in 12 fights. The 40% HP threshold is never reached gradually — we either win comfortably or get burst from >40% to dead in one turn. The 4 TP cost of Cure could be Flame damage instead.

### 2. Defensive Buff Timing is Wrong vs Kiters
Spending turns 1-2 on Motivation+Armor+Shield+Helmet (14 TP total) is optimal vs melee/close-range opponents but catastrophic vs ranged kiters. Those 2 wasted turns = 0 damage while eating 300-500 HP of chip spam.

### 3. Flame Output Correlates Directly with Wins
- **Wins**: avg 5.8 Flames per fight
- **Losses**: avg 2.3 Flames per fight
- Getting more Flames off = winning. Anything that reduces time-to-first-Flame improves WR.

### 4. RES Opponents Are Manageable
SIGKILL had RES 200 and we still won (1166 dmg, 12 turns). Armor stacking extends fights long enough for our damage to accumulate. This is the attrition thesis working as designed.

## Bugs Found & Fixed

### Critical: Chip Name Display (fight.py line 327)
The `-v` verbose fight display had a completely wrong chip ID → name mapping:
- Template 10 (Flame) was displayed as "FLASH"
- Template 9 (Spark) was displayed as "FLAME"
- Template 1 (Bandage) was displayed as "CURE"
- Template 8 (Lightning) was displayed as "SHIELD"

This means **every fight log we've ever read had wrong chip names**. Fixed with correct template-based mapping from `chips.ts`.

### Verified: Chip ID Layers
- **chip_id** (chips.ts key): Used by API inventory, sim_defaults
- **template** (chips.ts template field): Used by fight actions, LeekScript constants
- Flame = chip_id 5 = template 10. These are NOT interchangeable.

## Recommendations for v15

1. **Replace Cure** with Tranquilizer (task #113): 3 TP, 50% TP shackle, 0 cooldown, 4 uses. Cripples enemy action economy instead of hoping we survive to 40% HP.
2. **Anti-kite opening**: If dist > range, skip buffs, close first, buff when in Flame range.
3. **Adaptive buff priority**: Only full-buff if enemy is melee/closing. Partial buff if ranged.
4. **Ferocity** (task #115): +50% STR = +226 damage. Would turn the demontepneu loss into a win.
