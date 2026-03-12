# v14 Phalanx + Tranquilizer — 3-Day Overnight Results (S30)

**Date**: 2026-03-12 | **AI**: v14_flat "Phalanx" (Flame-first + Tranq-last rotation)
**Period**: March 10-12, 2026 (GH Actions daemon, 3x/day schedule)

## Summary

| Metric | Value |
|--------|-------|
| Total fights analyzed | 50 |
| Win rate | 52% (26W-24L) |
| March 10 batch (22f) | 45% (10W-12L) |
| March 12 batch (22f) | 55% (12W-10L) |
| Avg damage dealt | 912 |
| Avg damage taken | 630 |
| Avg fight duration | 8.7 turns |
| Heals | 0 (no heal chip equipped) |

## Level/Talent Progression

| Metric | S29 Start | S30 Current | Delta |
|--------|-----------|-------------|-------|
| Level | 112 | 117 | +5 |
| Talent | 264 | 333 | +69 |
| Capital | 5 | 35 | +30 |
| HP (base) | 677 | 692 | +15 |

## WR by Opponent Level

| Bracket | W-L | WR |
|---------|-----|-----|
| L100-120 | 25W-24L | 51% |
| L140+ | 1W-0L | 100% (1 fight, anomaly) |

## Bulb Impact (Surprising!)

| Opponent | W-L | WR |
|----------|-----|-----|
| Has bulb(s) | 9W-5L | 64% |
| No bulb | 17W-19L | 47% |

Hypothesis: Bulb summoners waste TP on summoning instead of damage/defense. The TP tax of summoning puny_bulbs actually helps us.

## Critical Bug: 0-Damage Fight

**Fight #51787170 vs LeConquerant (L116, MP 4, HP 865, STR 407)**

Our AI spent 9 turns only using defensive chips and moving. Zero Flame casts, zero weapon attacks. Action trace shows oscillating movement (cells 184↔258). The enemy with 2 puny_bulbs kited us: equal MP means we can never close the gap if they move away first.

Root cause: AI engages Flame only when in range (2-7 cells), but never reaches that range against a kiting MP 4 opponent. No fallback strategy exists for "can't close distance."

**Fix needed (v15)**: Use Laser (range 2-7) or Tranquilizer (range 1-8) at distance, weapon fallback, or detect kiting pattern and switch strategy.

## Loss Pattern Analysis

### High-RES Opponents (main weakness)

| Opponent | RES | Dmg Dealt | Result |
|----------|-----|-----------|--------|
| ElLucio | 303 | 232 | LOSS |
| Bredzil | 200 | 65 | LOSS |
| Pasdbol | 235 | 386 | LOSS |
| LeekThatLeek | 158 | 285 | LOSS |
| cocobellehuitre | 156 | 448 | LOSS |
| MarsChaxor | 150 | 150 | LOSS |

Our STR 452 with Flame (~29 base dmg) gets heavily reduced by RES. Against RES 200+, we deal <400 total damage across 8+ turns.

### HP Tank Opponents

| Opponent | HP | Dmg Dealt | Result |
|----------|-----|-----------|--------|
| leekeurDePoireaux | 1412 | 464 | LOSS |
| veggas | 1349 | 1179 | LOSS |
| Jackleekolson | 1301 | 999 | LOSS |

Even when we deal decent damage, 1300+ HP opponents simply outlast us.

## Tranquilizer Usage

Tranquilizer appears in 42/50 fights (84%). Avg uses per fight: ~2.3.
In 8 fights, Tranq was never used — these tend to be shorter fights (5-6 turns) where all TP went to Flame.

## Key Conclusions

1. **52% WR is our ceiling with current build** — STR-heavy glass cannon hits diminishing returns against balanced builds
2. **RES is our kryptonite** — need Ferocity (+50% STR buff) or magic damage to bypass
3. **0-damage kiting bug is a priority fix** — guaranteed loss when enemy MP >= ours and they choose to kite
4. **Bulbs help us** — bulb summoners waste TP on summons, reducing their effective damage output
5. **Capital 35 should go to TP or MP** — more actions or movement flexibility
6. **b_laser (attacks + heals)** would add sustain we desperately lack (0 heals in 50 fights)
