# Nemesis Analysis - Counter-Intelligence Report

> **STRAND 3**: Understanding WHY we lose to our hardest opponents → counter-strategies
> **Status**: Complete | **Date**: 2026-01-25

---

## Executive Summary

**Critical Finding**: 7 of our "hardest opponents" (0% WR) are **L301** - these are expected losses from level disparity, NOT AI failures. True same-level nemeses are different.

### True Same-Level Nemeses (L28-42)

| Opponent | Fights | Record | WR% | Level | Key Pattern |
|----------|--------|--------|-----|-------|-------------|
| LeeK #131493 | 69 | 21W-48L | 30% | L38 | Dies in 5-6 turns |
| LeeK #130532 | 38 | 15W-23L | 40% | L34 | Mid-game attrition |
| LeeK #45200 | 8 | 0W-8L | 0% | L32 | **0% WR at same level!** |
| LeeK #78884 | 8 | 0W-8L | 0% | L32 | **0% WR at same level!** |
| LeeK #107421 | 6 | 0W-6L | 0% | L37 | **0% WR at same level!** |

---

## Level Disparity Analysis

### Fake Nemeses (L301, ignore)

```
LeeK #51136: 10 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #51314: 10 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #40016:  7 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #41328:  7 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #42580:  7 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #22484:  6 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #29802:  5 fights, 0% WR, L301 - EXPECTED LOSS
LeeK #32417:  5 fights, 0% WR, L301 - EXPECTED LOSS
```

**Total**: 63 fights against L301 opponents = expected 0% WR
**Recommendation**: These are NOT real nemeses. Remove from nemesis tracking or flag as "level gap".

---

## True Nemesis: LeeK #131493 Deep Dive

### Profile
- **Name**: PercevalLeGallois
- **Fights vs us**: 69 total (21W-48L, 30% WR)
- **Level**: L38 (we're L37-38)
- **Archetype**: balanced
- **Fight duration pattern**:
  - Wins: avg 1.4 turns (we die fast)
  - Losses: avg 1.7 turns (also fast)

### Loss Pattern Analysis

**Critical**: 86% of losses end in ≤5 turns.

```
Losses by Duration:
  Early (1-5 turns):  24 losses (86%)
  Mid (6-15 turns):    3 losses (11%)
  Late (16+ turns):    1 loss   ( 4%)
```

**Hypothesis**: We're losing the opening engagement. Either:
1. They strike first (first-mover advantage)
2. Their opening burst is stronger than ours
3. We misposition on turn 1

---

## Zero-WR Opponents (Same Level)

These 4 opponents have **0% WR against us at similar levels**:

### LeeK #45200 (L32)
- 8 fights, 0W-8L
- We level up between fights (we're now L38)
- Pattern: They consistently out-trade us

### LeeK #78884 (L32)
- 8 fights, 0W-8L
- Same pattern as #45200

### LeeK #107421 (L37)
- 6 fights, 0W-6L
- **Concerning**: Same level, still 0% WR

### LeeK #107429 (L41)
- 6 fights, 0W-6L
- Slightly higher level (4 level gap)

---

## Counter-Strategies

### Counter-Strategy 1: Opening Burst Optimization

**Problem**: Losses end in 5-6 turns → we're dying in opening.

**Current v11 opening**:
```leekscript
// v11 "Hydra" - Turn 1
useChip(CHIP_PROTEIN, self)  // +80 STR x2
useChip(CHIP_MOTIVATION, self)  // +2 TP x3
useChip(CHIP_BOOTS, self)  // +2 MP x2
```

**Analysis**: 3 chips = 10 TP spent opening. Then we need 3 more TP to attack.

**Hypothesis**: We're TP-starved on turn 1. We need 6-7 TP to:
- Use 2-3 buffs
- Attack once (3-5 TP weapon)

**Counter-proposal**:
```leekscript
// Turn 1: Aggressive burst
// Goal: Kill or severely damage before they act
if (getTP() >= 8) {
    useChip(CHIP_PROTEIN, self);
    useChip(CHIP_FLASH, nearest_enemy);  // 32 dmg, range 1-10
    useWeapon(nearest_enemy);
} else {
    // Conservative opening
    useChip(CHIP_BOOTS, self);
    useChip(CHIP_PROTEIN, self);
    moveToward(nearest_enemy, 2);
}
```

**Expected outcome**: Increase first-turn damage from ~37 (pistol) to ~70 (flash + pistol).

---

### Counter-Strategy 2: Position Denial

**Problem**: "Balanced" archetype opponents may have better positioning logic.

**Current v11 positioning**: 
- Uses `getBestRetreatCell()` from danger map
- Retreats after shooting

**Counter-proposal**:
```leekscript
// Don't retreat - push forward after shooting
// If enemy in range and alive, move toward them not away
if (enemy_in_range && enemy_alive) {
    // Stay aggressive - move toward, not away
    moveToward(nearest_enemy);
}
```

**Expected outcome**: Prevent enemies from safely positioning for counter-attacks.

---

### Counter-Strategy 3: Target Prioritization

**Problem**: Balanced opponents may be tanks (high HP). We should focus fire on weakest.

**Current**: `getNearestEnemy()` = attacks whoever is closest

**Counter-proposal**:
```leekscript
// Target lowest HP enemy, not just nearest
var target = getNearestEnemy();
var min_hp = getLife(target);
var enemies = getEnemies();
for (var e in enemies) {
    if (getLife(e) < min_hp) {
        target = e;
        min_hp = getLife(e);
    }
}
```

**Expected outcome**: Eliminate low-HP enemies before they can act, reducing total incoming damage.

---

### Counter-Strategy 4: Early Force-Engage

**Problem**: 5-6 turn losses suggest we should force engagement earlier.

**Current v11**: Force engage on turn 30 (stalemate prevention)

**Counter-proposal**:
```leekscript
// Earlier force-engage for balanced opponents
var force_engage_turn = 15;  // Was 30
if (turn >= force_engage_turn && fight_phase == "kite") {
    fight_phase = "force_engage";
    debug("Early force-engage at turn " + turn);
}
```

**Expected outcome**: Avoid prolonged kiting that gives balanced opponents time to out-sustain us.

---

## Case Study: Fight #51234329 - The Sustain Problem

**Date**: 2026-01-26
**Result**: LOSS (6 turns)
**Opponent**: Jermaine (L48, Jackson)

### The Stat Comparison

| Stat | IAdonis | Jermaine | Ratio |
|------|---------|----------|-------|
| Level | 38 | 48 | -10 |
| HP | **211** | 741 | 3.5x disadvantage |
| STR | 310 | 20 | 15x advantage |
| WIS | 0 | **300** | ∞ disadvantage |
| AGI | 10 | 40 | 4x disadvantage |
| MP | 3 | **4** | Can't catch |
| FREQ | 100 | 140 | Less TP regen |

### The Fight Timeline

| Turn | Our Action | Our DMG | Their DMG | Our HP | Their HP |
|------|-----------|---------|-----------|--------|----------|
| 1 | Move only | 0 | 0 | 211 | 741 |
| 2 | Move only | 0 | 0 | 211 | 741 |
| 3 | Move only | 0 | 0 | 211 | 741 |
| 4 | Attack | 149 | 45 | 166 | 592 |
| 5 | Attack | 250 | 95+130 heal | 71 | 472→602 |
| 6 | - | - | 29 | **DEAD** | 579 |

**Total damage dealt**: 399
**Total damage taken**: 169
**Total enemy healing**: 237 (MORE than our max HP!)

### The Core Problem

> **We dealt 2.4x more damage than we took, but still lost.**

WIS=300 enables:
1. **Chip 1** (CURE?) heals 99-101 HP per use
2. **Chip 39** (VAMPIRISM?) heals 8-16 per hit
3. Net healing > our damage output per turn

### Why v14's FLASH Doesn't Solve This

v14 adds ~32 damage turn 1 via FLASH. But:
- They have 741 HP (we need 4-5 FLASHes worth to kill)
- They heal 100+ HP/turn (FLASH barely dents sustain)
- We still die before our STR=310 advantage materializes

### The True Counter-Strategy

This isn't an "opening" problem. It's a **build matchup** problem:

| Our Build | Their Build | Outcome |
|-----------|-------------|---------|
| Glass cannon (211 HP, 310 STR) | Sustain tank (741 HP, 300 WIS) | We lose |

**Required solutions** (any of):
1. **More HP** - Respec some STR → HP to survive long enough
2. **Anti-heal** - Does LeekWars have heal reduction chips?
3. **Faster closing** - 4 MP to match their kiting (BOOTS chip?)
4. **Burst multiplier** - DOUBLE chip (2x damage) to overwhelm healing

### Strategic Recommendation

At L40, we should consider:
1. **Scouting phase**: If enemy WIS > 200, switch to kite/sustain mode ourselves
2. **Equipment**: DOUBLE chip → burst 620 damage in one turn to overwhelm heals
3. **Build**: Consider 50-100 HP allocation (sacrifice ~50 STR)

---

## Equipment Gap Analysis

### Our Current Setup (L38)
- **Weapons**: Pistol (3 TP), Magnum (5 TP)
- **Chips**: PROTEIN (3 TP), MOTIVATION (4 TP), CURE (4 TP), BOOTS (3 TP), FLASH (3 TP), FLAME (4 TP)

### Potential Counter-Gaps
| Item | TP Cost | Benefit | Priority |
|------|---------|---------|----------|
| DOUBLE | 6 TP | 2x damage | HIGH |
| TORNADO | 5 TP | AOE, pushes | MEDIUM |
| HEAL | 6 TP | 60 HP heal | MEDIUM |

**Missing**: DOUBLE (2x next attack) could double our burst potential.

---

## Action Items

### Immediate (can implement now)
1. **Prioritize FLASH in opening** - 32 damage, 3 TP, range 1-10
2. **Target lowest HP enemy** - not just nearest
3. **Reduce force-engage threshold** from 30 → 15

### Short-term (need data)
4. **Analyze LeeK #45200 replays** - why 0% WR at same level?
5. **Test DOUBLE chip** - purchase recommendation

### Long-term (strategic)
6. **Track "balanced" win rates separately** - different counters than kiters

---

## Appendix: Query Commands

```bash
# Find same-level nemeses
python3 -c "
import sqlite3
conn = sqlite3.connect('data/fights_meta.db')
results = conn.execute('''
    SELECT leek_name, leek_id, total_fights, wins, losses, 
           ROUND(win_rate * 100, 1), level_last_seen
    FROM opponents
    WHERE level_last_seen BETWEEN 28 AND 42
      AND total_fights >= 5
      AND win_rate < 0.4
    ORDER BY losses DESC
''').fetchall()
for r in results:
    print(f'{r[0]}: {r[2]} fights, {r[3]}W-{r[4]}L, {r[5]}% WR, L{r[6]}')
"

# Track specific nemesis
leek opponent stats --leek-id 131493

# Get recent losses
sqlite3 data/fights_meta.db "SELECT f.fight_id, f.duration FROM fights f JOIN leek_observations lo ON f.fight_id = lo.fight_id WHERE lo.leek_id = 131493 AND f.winner = 2 ORDER BY f.fight_id DESC LIMIT 10"
```