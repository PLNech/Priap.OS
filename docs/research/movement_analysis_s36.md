# Movement Analysis — v14 Phalanx Baseline (S36)

**Fights analyzed**: 50 (IAdonis matchmaking, context=2)
**Win rate**: 27/50 (54%)
**Total IAdonis turns**: 398
**Avg turns/fight**: 8.0

---

## Key Metrics

| Metric | Value | Detail |
|--------|-------|--------|
| **Shield waste rate** | 66.8% | 157/235 turns shields cast at dist > 10 |
| **Weapon miss rate** | 97.7% | 125/128 turns in weapon range but 0 attacks |
| **Weapon fire rate** | 3.5% | 14/398 turns with weapon attack |
| **Avg approach turns** | 4.3 | Turns at dist > weapon range before first weapon fire |

## TP Budget (per turn average)

Total TP spent: 2043 over 398 turns = **5.1 TP/turn**

| Category | Total TP | % of Budget |
|----------|----------|-------------|
| Shields | 797 | **39.0%** |
| Weapons | 132 | 6.5% |
| Damage chips (Flame) | 846 | 41.4% |
| Buffs (Motivation) | 200 | 9.8% |
| Debuffs (Tranq) | 0 | 0.0% |
| Heals | 68 | 3.3% |

## Turn Type Breakdown

| Turn Type | Count | % |
|-----------|-------|---|
| Move-only (no attack, no shield) | 86 | 21.6% |
| Chip-only (no weapon) | 43 | 10.8% |
| Weapon turn | 14 | 3.5% |
| Mixed/Other | 255 | 64.1% |

## Approach Turns Distribution

| Approach turns | Fights |
|----------------|--------|
| 2 | 1 |
| 3 | 3 |
| 4 | 5 |
| 6 | 1 |
| 7 | 1 |
| 8 | 1 |

---

## Implications for #0209 Movement Rework

1. **Shield waste is HIGH** (67%): Distance gate on shields will save significant TP

2. **Weapon fires in only 4% of turns**: Critical: weapon almost never fires. TP reservation + Move→Attack→Defend will fix this

3. **TP budget dominated by shields (39%)**: Shields take significant budget share

4. **22% turns are move-only**: High approach overhead — faster positioning would help