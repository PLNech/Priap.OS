# AI Optimization Analysis - v11 "Hydra"

**Date**: 2026-01-25  
**Analyst**: Stratego  
**Target**: WR 43.6% → 55%+

---

## Current Performance (Offline Testing)

| Matchup | Win Rate | Assessment |
|---------|----------|------------|
| v11 vs rusher | TBD% | Critical |
| v11 vs kiter | TBD% | Critical |
| v11 vs balanced | TBD% | Should dominate |
| v11 vs tank | TBD% | Should dominate |
| v11 vs burst | TBD% | Should survive |

---

## Code Review: v11 Architecture

### Module Overview
| Module | Lines | Purpose | Assessment |
|--------|-------|---------|------------|
| v8_state | 196 | HP tracking, phase detection, TTK | ✅ Robust |
| v8_accessible_cells | 216 | BFS reachability | ✅ Optimized |
| v8_danger_map | 196 | Cell danger scoring | ✅ Sophisticated |
| v8_hide_seek | 205 | Safe cell selection | ✅ Complete |
| v8_combat | 267 | Weapon rotation | ⚠️ Rough damage est |
| v11_chips | 210 | Conditional chip usage | ⚠️ Timing issues |

---

## Identified Issues

### Issue #1: Retreat Overuse in Midgame

**Location**: `fighter_v11.leek:136-145`

```leekscript
if (!winning_race && fight_phase == "midgame" && cached_danger_map != null) {
    var safe_cell = getSafestCell(cached_danger_map)
    if (safe_cell != null) {
        var current_danger = getDangerAt(cached_danger_map, getCell())
        var safe_danger = getDangerAt(cached_danger_map, safe_cell)
        if (safe_danger < current_danger - 2) {
            strategy = "retreat"
        }
    }
}
```

**Problem**: When losing damage race (winning_race=false), we retreat to safety. But:
- This admits defeat in the damage trade
- Against rushers, retreating just delays the inevitable
- We're not maximizing chip damage before retreating

**Fix Idea**: Retreat should only happen if we can still win. If we're clearly losing, we should ALL-IN with chips.

---

### Issue #2: PROTEIN Chip Timing

**Location**: `v11_chips.leek:150-157`

```leekscript
if (canUseChip(chip_protein) && getTP() >= 7) {  // 3 for protein + 4 for attack
    var result = useChip(chip_protein, getEntity())
```

**Problem**: We require 7 TP (3 protein + 1 attack), but protein boosts ALL attacks that turn. 
- If we have 6 TP and use protein + 1 attack = 5 TP spent, 1 leftover = inefficient
- We should use protein earlier (turn 2) when we have full TP

**Fix**: Move protein to `applyBuffsSafe()` when shouldBuff() is true. It's a buff, not a combat chip.

---

### Issue #3: Kiter Counter - Gap Closing

**Problem**: Kiter stays at distance 5+, retreats when we approach.
- Our strategy: close → chip → attack → close more
- Kiter: retreat → shoot → retreat
- We never get multiple attacks in a row

**Current Code** (lines 166-188):
```leekscript
// Phase 1: Close to attack range
while (dist > w_max && getMP() > 0) {
    moveToward(enemy)
    dist = getCellDistance(getCell(), getCell(enemy))
}

// Phase 2: Chip damage
useChipDamage(enemy)

// Phase 3: Weapon attacks
executeAttacks(enemy)

// Phase 4: Use remaining MP to close further
while (getMP() > 0) {
    moveToward(enemy)
}
```

**Issue**: MP spent in Phase 1 reduces what's available in Phase 4.

**Fix**: Reserve 1 MP for extra closing after attacks. Chips (FLASH/FLAME) don't need us to be as close.

---

### Issue #4: Damage Estimation is Rough

**Location**: `v8_combat.leek:55-58`

```leekscript
var damage_estimate = cost * 10  // Rough estimate
```

**Problem**: Different weapons have different damage multipliers:
- Pistol: 1.0x (cost 3 → 30 dmg)
- Magnum: 1.25x (cost 4 → 50 dmg, not 40)
- Shotgun: 2x at close range

**Fix**: Use actual damage calculation:
```leekscript
// Better estimation
var base_damage = getWeaponEffects(w)
var damage_estimate = base_damage * 10  // More accurate
```

---

## Optimization Priorities

### Priority 1: Kiter Counter (Highest Impact)

**Hypothesis**: v11 loses to kiter because we spend all MP approaching, then have none left for extra attacks.

**Test**: Compare current v11 vs kiter offline.

**Fix Approach**:
1. Reserve 1 MP after initial approach
2. Use FLASH (range 10) before closing fully
3. After attacks, use reserved MP to close + attack again

### Priority 2: Protein Timing

**Hypothesis**: Protein applied on turn 2-3 is more efficient than mid-fight.

**Fix**: Move protein to `shouldBuff()` phase, not combat phase.

### Priority 3: Midgame Aggression

**Hypothesis**: We retreat too easily when losing the damage race.

**Fix**: When losing midgame, either:
- ALL-IN with remaining chips (aggressive)
- OR accept we lost and minimize damage taken (defensive)

Currently we're in neither - we retreat but don't maximize chip output.

---

## Testing Plan

### Offline Validation
```bash
poetry run python scripts/test_v11_matchups.py -n 100 --level 36
```

### Key Metrics to Track
1. Win rate by matchup (should be >60% vs balanced, >50% vs others)
2. Average fight duration (target: <10 turns)
3. Damage dealt per fight (measure efficiency)
4. Chip usage frequency

### Expected Results After Fixes
| Matchup | Current | Target |
|---------|---------|--------|
| vs rusher | ? | 55%+ |
| vs kiter | ? | 55%+ |
| vs balanced | ? | 70%+ |
| vs tank | ? | 60%+ |
| vs burst | ? | 55%+ |

**Overall Target**: >55% WR across all archetypes.

---

## Implementation Tasks

### Task 1: Kiter Counter
- [ ] Modify `fighter_v11.leek` to reserve 1 MP for post-attack closing
- [ ] Prioritize FLASH (range 10) before full approach
- [ ] Test: v11 vs kiter 100 rounds

### Task 2: Protein Timing
- [ ] Move protein to `shouldBuff()` in v11_chips.leek
- [ ] Remove TP check (buffs don't compete with attacks)
- [ ] Test: Verify protein still applies turn 2-3

### Task 3: Midgame Decision
- [ ] When !winning_race AND fight_phase == "midgame":
  - If we have 2+ unused chips → ALL-IN
  - Otherwise → retreat as before
- [ ] Test: Verify we don't retreat from winnable fights

### Task 4: Damage Estimation
- [ ] Fix v8_combat.leek to use actual weapon damage
- [ ] Test: Verify weapon selection optimizes damage

---

## Notes

- All changes should be A/B tested offline before online deployment
- Keep force_engage stalemate fix (v11 already has this)
- Don't break the chip cooldowns logic