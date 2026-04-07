# PySim Missing Game Mechanics — Java Source Audit

**Date**: 2026-04-07 (S42)
**Source**: `tools/leek-wars-generator/src/main/java/com/leekwars/generator/`
**Method**: Subagent exhaustive scan of effects/, Entity.java, Attack.java, State.java, Map.java

## Summary

27 missing mechanics identified. PySim currently implements 8 of ~35 effect types.

| Implemented | Missing HIGH | Missing MEDIUM | Missing LOW |
|-------------|-------------|----------------|-------------|
| Damage, Heal, Abs Shield, Rel Shield, TP Shackle, TP Buff, STR Buff, Poison | 6 | 13 | 8 |

## HIGH Priority (affects 1v1 outcomes directly)

### 1. Entity States (crowd control)
- **Java**: `EffectAddState.java`, `EntityState.java`
- **Effect type**: 59 (ADD_STATE)
- **States**: INVINCIBLE(3), UNHEALABLE(2), PACIFIST(4), ROOTED(9), PETRIFIED(10), HEAVY(5), CHAINED(8)
- **Impact**: Fundamental CC — a petrified entity can't act, invincible takes no damage
- **Used by**: Awakening (L200, resurrect + 3t invincible), various high-level chips

### 2. Vulnerability / Absolute Vulnerability
- **Java**: `EffectVulnerability.java` (type 26), `EffectAbsoluteVulnerability.java` (type 27)
- **Description**: Reduces target's relative/absolute shield effectiveness
- **Impact**: Direct counter to shield-heavy builds (our meta is shield-dominant)
- **Used by**: Broadsword passive, Axe, Katana, various debuff chips

### 3. Damage Return
- **Java**: `EffectDamageReturn.java` (type 20)
- **Formula**: `(v1 + jet*v2) * (1 + AGI/100) * aoe * critPower`
- **Impact**: Reflects % of damage back to attacker. Defensive mechanic.
- **Used by**: Some shield/armor chips at higher levels

### 4. Stat Shackles (STR/AGI/WIS)
- **Java**: `EffectShackleStrength.java` (type 19), `EffectShackleAgility.java` (type 47), `EffectShackleWisdom.java` (type 48)
- **Currently**: Only TP shackle (type 15) implemented
- **Formula**: Same as TP shackle — `(v1 + jet*v2) * (1 + MAG/100)`
- **Impact**: Reduces opponent's damage output (STR), crit chance (AGI), healing (WIS)

### 5. Aftereffect (persistent damage)
- **Java**: `EffectAftereffect.java` (type 25)
- **Description**: Like poison but does NOT decay. Applies at creation AND at start of each turn.
- **Scales with**: Science stat (which we map to STR in sim)
- **Used by**: Venom-class chips, some weapon effects

### 6. Initial Chip Cooldown
- **Java**: `Chip.java` lines 11, 34
- **Description**: Some chips start the fight on cooldown (can't use turn 1)
- **Our data**: `initial_cooldown` field exists in Chip dataclass but NOT enforced in engine
- **Fix**: In entity init, pre-populate cooldown map with `initial_cooldown` values

## MEDIUM Priority (positioning/resource management)

### 7. MP Buff (type 7) / MP Shackle (type 17)
- **Java**: `EffectBuffMP.java`, `EffectShackleMP.java`
- **Used by**: Leather Boots, Seven League Boots, movement control chips
- **Impact**: Affects MP available for positioning. Entity.mp needs MP buff/shackle tracking.

### 8. Area of Effect (AOE) Patterns
- **Java**: `attack/areas/Area*.java`, `MaskAreaCell.java`
- **Patterns**: AreaCircle(1-3), AreaPlus(2-3), AreaX(1-3), AreaLaserLine, AreaSquare
- **Falloff formula**: `1 - dist * 0.2` (center = 100%, border = reduced)
- **Currently**: All attacks are single-target. AOE chips/weapons hit one entity only.
- **Impact**: Area chips (Flash, Drip, Grenade Launcher) should hit multiple targets

### 9. Movement Effects
- **Attract** (type 46): Pull target toward caster — `Map.getAttractLastAvailableCell()`
- **Push** (type 51): Push target away from target cell
- **Repel** (type 53): Push target away from caster
- **Teleport** (type 10): Move caster to target cell
- **Permutation** (type 11): Swap positions of two entities

### 10. Magic Shackle (type 24)
- **Java**: `EffectShackleMagic.java`
- **Impact**: Reduces magic stat → weaker chip effects (shackles, poisons)

### 11. Wisdom Buff (type 22) / Resistance Buff (type 21)
- **Java**: `EffectBuffWisdom.java`, `EffectBuffResistance.java`
- **Impact**: Scaling healing/shields. Team-fight oriented but affects 1v1.

### 12. Nova Damage (type 30)
- **Java**: `EffectNovaDamage.java`
- **Description**: Direct damage ignoring shields. Scales with science + power.
- **Impact**: Bypasses defensive mechanics entirely.

### 13. Steal Life (type 61) / Steal Shield (type 29)
- **Java**: `EffectStealLife.java`, `EffectStealAbsoluteShield.java`
- **Description**: Chained effects — convert previous effect's value into healing/shield
- **Impact**: Combo mechanics for sustainability

### 14. Antidote (type 23) / Remove Shackles (type 49)
- **Java**: `EffectAntidote.java`, `EffectRemoveShackles.java`
- **Description**: Remove all poison effects / all shackle effects from target

### 15. Debuff (type 9) / Total Debuff (type 60)
- **Java**: `EffectDebuff.java`, `EffectTotalDebuff.java`
- **Description**: Reduces ALL active buffs on target by X%. Counter to buff stacking.

### 16. Nova Vitality (type 45)
- **Java**: `EffectNovaVitality.java`
- **Description**: Permanently increases max HP by science-scaled amount

## LOW Priority (team/rare/specialized)

### 17-23. Team/Advanced Mechanics
- **Summon** (type 14): Creates bulb entity — `State.summonEntity()`
- **Resurrect** (type 15): Revives dead entity with specified HP
- **Kill** (type 16): Instant death (respects INVINCIBLE)
- **Ally Killed To Agility** (type 55): Team synergy buff
- **Power stat**: Multiplier for poison/aftereffect/nova (`1 + power/100`)
- **Passive weapon effects**: Triggered by events (poison damage, crits)
- **Weapon uses per turn**: Most are unlimited, some have per-turn caps

## Implementation Plan

**Phase 1** (task #82): Realistic ops costing — prerequisite for all AI testing
**Phase 2** (task #83): 
1. Initial cooldown enforcement (trivial — 5 lines)
2. Entity states (INVINCIBLE, ROOTED, PETRIFIED) — core CC
3. Stat shackles (STR/AGI/WIS) — same pattern as TP shackle
4. MP buff/shackle — extends Entity.mp property
5. Vulnerability — modifies shield calculations
6. AOE patterns — most impactful for multi-target weapons

**Phase 3** (future):
- Movement effects (attract/push/teleport)
- Chained effects (steal life/shield)
- Utility counters (antidote, remove shackles, debuff)
- Summoning (if we ever sim team fights)
