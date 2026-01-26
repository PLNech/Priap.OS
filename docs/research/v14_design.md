# v14 Opening Burst Design

> **STRAND 5**: v14 Opening Burst AI Design
> **Status**: Draft | **Date**: 2026-01-26
> **Author**: Worker 2

---

## Problem Statement

**Data Reality**:
- 41% WR in ≤5 turn fights (our weakness)
- 60% WR in 6-15 turn fights (our strength)
- 86% of losses end in ≤5 turns

**Root Cause**: v11's opening is **defensive** (buff-first) when it should be **aggressive** (damage-first).

Current v11 opening in `v11_chips.leek:101-122`:
```leekscript
function shouldBuff() {
    if (enemy_ttk >= 999) {
        debug("  Skip buffs: TTK unknown (turn 1)")
        return false  // ⚠️ No buffs OR attacks on turn 1!
    }
    // ...
}

function applyBuffsSafe() {
    // MOTIVATION first (+2 TP)
    // BOOTS second (+2 MP)
    // PROTEIN last (+80 STR, only if TP >= 7)
    // ⚠️ NO ATTACKS in opening!
}
```

**The Issue**: We spend turn 1 buffing while enemies attack. This gives up first-mover advantage.

---

## Design Principles

### Principle 1: Damage > Buffs in Opening
Buffs are for extending advantages, not creating them. In the opening, we need to:
1. Deal damage immediately
2. Apply pressure
3. Force enemies to react to us

### Principle 2: First 5 Turns = Survival + Damage
If we deal ~40 damage/turn for 5 turns = ~200 damage. Most leeks die in 5 turns.

### Principle 3: Position for Continuous Damage
Don't waste MP retreating. Use MP to stay in attack range.

---

## Turn-by-Turn Sequence

### Turn 1: Opening Burst
**TP Budget**: 10 TP (level 34)

```
Priority 1: FLASH chip (3 TP) → 32±3 damage, range 1-10
Priority 2: Weapon attack (3 TP pistol) → ~15 damage
Priority 3: MOTIVATION chip (4 TP) → +2 TP for next turn
```

**Sequence**:
1. `useChip(CHIP_FLASH, enemy)` - 3 TP, guaranteed 32 damage
2. `useWeapon(enemy)` - 3 TP, ~15 damage
3. `useChip(CHIP_MOTIVATION, self)` - 4 TP, +2 TP next turn
4. Move toward enemy (reserve 1 MP)

**Damage**: ~47 damage turn 1
**TP Remaining**: 0

**Why FLASH first?** (vs PROTEIN)
- FLASH: 32 damage guaranteed
- PROTEIN: +80 STR for 2 turns (variable weapon damage boost)
- At L38 with 310 STR: weapon damage is ~15±5
- FLASH provides more reliable opening damage

### Turn 2: Sustain Pressure
**TP Available**: 2 (from MOTIVATION) + 10 (base) = 12 TP

```
If in range (≤7):
  - 2x Weapon attack (3+3=6 TP) → ~30 damage
  - 1x FLAME chip (4 TP) → 29 damage
  - Total: ~59 damage

If out of range (>7):
  - Move toward enemy
  - 1x Weapon attack (3 TP) → ~15 damage
  - 1x FLASH chip (3 TP) → 32 damage
  - Total: ~47 damage + closed gap
```

### Turn 3: Mid-Opening Swing
**TP Available**: 10 base (+2 if MOTIVATION used turn 1)

**Decision Tree**:
```
If enemy HP < 30%:
  - FLAME spam (3x, 29 each) → ~87 damage, finisher
Else if losing race (enemy_ttk <= my_ttk):
  - PROTEIN chip (+80 STR) → higher weapon damage
  - 2x Weapon attack → ~30-40 damage
Else:
  - 2x Weapon attack → ~30 damage
  - 1x FLAME chip (4 TP) → 29 damage
```

### Turn 4-5: Transition to Mid-Game
At this point, we're either:
1. **Winning**: Enemy HP low, continue aggression
2. **Neutral**: Continue pressure, prepare mid-game buffs
3. **Losing**: Activate mid-game recovery (v12 logic)

---

## Anti-Archetype Tactics

### vs Rusher (Aggressive Opponent)
**Behavior**: Closes to range immediately, shoots

**Counter**:
- Turn 1: FLASH first (they're already close)
- Don't retreat after shooting - stand your ground
- Out-trade them in the damage race

```
// Don't do this:
// moveAwayFrom(enemy)  // ❌ Gives them initiative

// Do this instead:
// moveToward(enemy)    // ✅ Maintain pressure
```

### vs Kiter (Retreat Opponent)
**Behavior**: Shoots, then retreats to maintain distance

**Counter**:
- Turn 1: FLASH chip (long range 10 catches them)
- Chase aggressively (reserve MP for pursuit)
- Close gap before they can escape

```
dist = getCellDistance(getCell(), getCell(enemy))
if (dist > 7) {
    // Move toward, don't retreat
    while (getMP() > 1) {
        moveToward(enemy)
    }
}
```

### vs Balanced (Unknown Opponent)
**Behavior**: Adapts to situation

**Default**: Aggressive opening works against all archetypes.

---

## TP Math Reference

### Turn 1 (10 TP)
| Action | TP | Damage | Notes |
|--------|-----|--------|-------|
| FLASH | 3 | 32±3 | Guaranteed chip damage |
| Pistol attack | 3 | ~15 | Primary weapon |
| MOTIVATION | 4 | 0 | +2 TP next turn |
| Move | MP | - | Reserve 1 MP |
| **TOTAL** | **10** | **~47** | Full utilization |

### Turn 2 (12 TP with MOTIVATION)
| Action | TP | Damage | Notes |
|--------|-----|--------|-------|
| Pistol x2 | 6 | ~30 | Double tap |
| FLAME | 4 | 29 | Chip damage |
| Move | MP | - | Close or pursue |
| **TOTAL** | **10** | **~59** | Sustained pressure |

### Alternative: Magnum Opening
| Action | TP | Damage | Notes |
|--------|-----|--------|-------|
| Magnum (equip + attack) | 6 | ~30 | Higher base damage |
| FLASH | 3 | 32±3 | Chip damage |
| MOTIVATION | 4 | 0 | +2 TP next turn |
| **TOTAL** | **13** | **~62** | Higher damage, 1 TP deficit |

**Recommendation**: Stick with Pistol. Magnum costs 1 extra TP and doesn't proportionally increase damage.

---

## Module Changes Required

### v14_opening.leek (New Module)

```leekscript
// v14_opening.leek - Opening Burst Module
// Fighter v14 "Burst" - Maximum damage in turns 1-5

// =============================================================================
// TURN 1: OPENING BURST
// =============================================================================
function executeOpeningBurst(enemy) {
    var dist = getCellDistance(getCell(), getCell(enemy))

    // Priority 1: FLASH chip (guaranteed 32 damage, range 1-10)
    if (canUseChip(chip_flash) && dist <= 10) {
        var result = useChip(chip_flash, enemy)
        if (result == USE_SUCCESS) {
            markChipUsed(chip_flash)
            debug("    ⚡ FLASH opener!")
        }
    }

    // Priority 2: Weapon attack (3 TP pistol = ~15 damage)
    attackOnce(enemy)

    // Priority 3: MOTIVATION (+2 TP for next turn)
    if (canUseChip(chip_motivation)) {
        var result = useChip(chip_motivation, getEntity())
        if (result == USE_SUCCESS) {
            markChipUsed(chip_motivation)
            debug("    +2 TP for turn 2!")
        }
    }

    // Move toward enemy, but reserve 1 MP
    // Don't get stuck in corner
    while (getMP() > 1) {
        var moved = moveToward(enemy)
        if (moved == 0) break
    }
}

// =============================================================================
// TURN 2-3: SUSTAINED PRESSURE
// =============================================================================
function executeSustainedPressure(enemy) {
    var dist = getCellDistance(getCell(), getCell(enemy))
    var total_damage = 0

    // If in range: weapon + FLAME spam
    if (dist <= 7) {
        while (canUseChip(chip_flame) && getTP() >= 4) {
            var result = useChip(chip_flame, enemy)
            if (result == USE_SUCCESS) {
                markChipUsed(chip_flame)
                total_damage = total_damage + 29
            } else {
                break
            }
        }
        attackOnce(enemy)
        attackOnce(enemy)
    }
    // If out of range: move + FLASH
    else {
        while (getMP() > 1) {
            moveToward(enemy)
        }
        if (canUseChip(chip_flash) && dist <= 10) {
            useChip(chip_flash, enemy)
        }
        attackOnce(enemy)
    }
}

// =============================================================================
// TURN 4-5: TRANSITION
// =============================================================================
function executeTransition(enemy) {
    var enemy_hp_pct = getLife(enemy) * 100 / enemy_start_hp

    // If enemy low: FLAME spam finisher
    if (enemy_hp_pct < 30) {
        while (canUseChip(chip_flame) && getTP() >= 4) {
            useChip(chip_flame, enemy)
        }
        while (getTP() >= 3) {
            attackOnce(enemy)
        }
    }
    // If losing race: PROTEIN + attacks
    else if (!winning_race && enemy_ttk <= 3) {
        if (canUseChip(chip_protein)) {
            useChip(chip_protein, getEntity())
        }
        while (getTP() >= 3) {
            attackOnce(enemy)
        }
    }
    // Default: continued pressure
    else {
        while (getTP() >= 3) {
            attackOnce(enemy)
        }
        if (getTP() >= 4 && canUseChip(chip_flame)) {
            useChip(chip_flame, enemy)
        }
    }
}
```

### Changes to fighter_v14.leek

Replace the opening logic in the main file:

```leekscript
// OLD (v11):
if (turn_count <= 4) {
    var buffs = applyBuffsSafe()
    if (buffs > 0) {
        debug("  Applied " + buffs + " early buffs")
    }
}

// NEW (v14):
if (turn_count == 1) {
    executeOpeningBurst(enemy)
} else if (turn_count <= 3) {
    executeSustainedPressure(enemy)
} else if (turn_count <= 5) {
    executeTransition(enemy)
}
```

---

## Expected Results

### Performance vs Archetypes (Predicted)

| Opponent | v11 WR | v14 WR | Change |
|----------|--------|--------|--------|
| Rusher | 50% | 55% | +5% |
| Kiter | 45% | 52% | +7% |
| Balanced | 50% | 52% | +2% |
| **Overall (≤5 turns)** | **41%** | **50%** | **+9%** |

### Metrics to Track
- Damage in turn 1 (should increase from ~0 to ~47)
- Win rate in ≤5 turn fights (target: 50%+)
- Average damage per fight (should increase)
- Opponent HP at turn 5 (should be lower)

---

## Offline Test Plan

### Test: v14 vs archetype_rusher (n=50)

```bash
poetry run python scripts/compare_ais.py \
  ais/fighter_v14.leek \
  ais/archetype_rusher.leek \
  -n 50 \
  --output v14_vs_rusher.json
```

**Success Criteria**:
- [ ] v14 win rate > 55%
- [ ] Average fight duration < 6 turns
- [ ] Turn 1 damage > 40 on average

### Test: v14 vs archetype_kiter (n=50)

```bash
poetry run python scripts/compare_ais.py \
  ais/fighter_v14.leek \
  ais/archetype_kiter.leek \
  -n 50 \
  --output v14_vs_kiter.json
```

**Success Criteria**:
- [ ] v14 win rate > 50%
- [ ] Chases effectively (distance closes over time)

---

## Open Questions

1. **Should we equip Magnum turn 1?**
   - Magnum: 5 TP, ~30 damage
   - Pistol: 3 TP, ~15 damage
   - Magnum costs 2 more TP for 15 more damage = 7.5 TP/damage (worse efficiency)
   - **Answer**: No, stick with Pistol for opening

2. **What if enemy is out of FLASH range (dist > 10)?**
   - Move first, then FLASH
   - This costs MP but guarantees chip damage
   - **Answer**: Move toward, try FLASH when in range

3. **Do we need PROTECT chip?**
   - Not in opening - PROTECT is for mid-game sustain
   - **Answer**: No, focus on damage

---

## Implementation Tasks

- [ ] Create `ais/v14_opening.leek` module
- [ ] Create `ais/fighter_v14.leek` with v14 opening logic
- [ ] Run offline tests vs archetypes (n=50 each)
- [ ] If WR improvement confirmed → deploy
- [ ] Monitor online WR in ≤5 turn fights

---

## Related Documents

- `docs/GROUND_TRUTH.md` - TP costs, chip stats
- `docs/research/nemesis_analysis.md` - Counter-strategy ideas
- `ais/v11_chips.leek` - Current chip logic (for reference)
- `ais/v12_midgame.leek` - Mid-game recovery logic (reuse)

---

*Document version: 1.0*
*Last updated: 2026-01-26*