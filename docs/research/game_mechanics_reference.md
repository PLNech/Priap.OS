# LeekWars Game Mechanics Reference

> Source of truth: `tools/leek-wars-generator/src/` (Java fight engine).
> All formulas extracted directly from the game server code.
> Written S40, 2026-04-06.

---

## 1. Map & Grid System

### Grid Type: Rotated Square Grid (Diamond/Isometric)

**NOT hex.** The grid is a **rotated square** (diamond) layout. Each cell has 4 neighbors (N/E/S/W), not 6.

**Coordinate System:**
- Cells are numbered linearly: `0` to `nb_cells - 1`
- `nb_cells = (width * 2 - 1) * height - (width - 1)`
- Default map: width=18, height=18 -> `(18*2-1)*18 - 17 = 35*18-17 = 613` cells
- Cell ID to grid coords (from `Cell.java`):
  ```
  raw_x = id % (width * 2 - 1)
  raw_y = id / (width * 2 - 1)
  y = raw_y - raw_x % width
  x = (id - (width - 1) * y) / width
  ```

**Directions** (diamond-rotated, so N/E/S/W are diagonal in screen space):
- NORTH (NE on screen): `cell_id - width + 1`
- EAST (SE on screen): `cell_id + width`
- SOUTH (SW on screen): `cell_id + width - 1`
- WEST (NW on screen): `cell_id - width`

**Distance** (Manhattan on rotated grid):
```python
def cell_distance(c1, c2):
    return abs(c1.x - c2.x) + abs(c1.y - c2.y)
```

### Obstacles
- Size 1: single cell blocked
- Size 2: 2x2 diamond (cell + EAST + SOUTH + SOUTH-EAST)
- Size 3: 3x3 square around center
- Random generation: `obstacles_count` random cells, random size 1-2

### Entity Placement
- Team 1: quadrant 1 (left side), Team 2: quadrant 4 (right side)
- Map validated by connected component check (both teams reachable)
- Map types: 0-4 random, -1 = Nexus (test), 5 = Arena (tournament)
- 10 named map themes: Nexus, Factory, Desert, Forest, Glacier, Beach, Temple, Teien, Castle, Cemetery

---

## 2. Damage Formula (THE CORE)

### Direct Damage (`EffectDamage.java`, type=1)

```python
def calculate_damage(value1, value2, jet, caster, target, aoe, critical, target_count):
    # Base damage: random between value1 and value1+value2
    base = (value1 + jet * value2)  # jet = random(0, 1)

    # Stat scaling: STRENGTH
    scaled = base * (1 + max(0, caster.strength) / 100.0)

    # AoE attenuation, critical, target count, power
    raw = scaled * aoe * critical_power * target_count * (1 + caster.power / 100.0)

    # critical_power = 1.3 if critical, else 1.0

    # Return damage (before shields!)
    if target != caster:
        return_damage = round(raw * target.damage_return / 100.0)

    # Shield reduction
    after_shields = raw - raw * (target.relative_shield / 100.0) - target.absolute_shield
    after_shields = max(0, after_shields)

    # Invincible state
    if target.has_state(INVINCIBLE):
        after_shields = 0

    damage = round(after_shields)
    damage = min(damage, target.life)  # Can't overkill

    # Erosion: permanent max_life reduction
    erosion = round(damage * erosion_rate)
    # erosion_rate = 0.05 (normal), 0.10 (poison), +0.10 if critical

    # Life steal (WISDOM-based)
    if target != caster:
        life_steal = round(damage * caster.wisdom / 1000.0)

    return damage, erosion, life_steal, return_damage
```

**Key constants:**
- `CRITICAL_FACTOR = 1.3` (30% bonus, NOT 40% as wiki says)
- `erosion_rate = 0.05` (normal damage), `0.10` (poison), `+0.10` if critical
- Life steal = `wisdom / 1000` of damage dealt (100 wisdom = 10% steal)
- Damage return calculated BEFORE shields, applied to attacker

### Shield Reduction Order
```
final_damage = max(0, raw_damage * (1 - relative_shield/100) - absolute_shield)
```
**Relative shield applies first (multiplicative), then absolute shield subtracts.**

### Poison Damage (`EffectPoison.java`, type=13)

```python
def calculate_poison(value1, value2, jet, caster, aoe, critical):
    base = (value1 + jet * value2)
    scaled = base * (1 + max(0, caster.magic) / 100.0)  # MAGIC, not STR
    return round(scaled * aoe * critical_power * (1 + caster.power / 100.0))
```
- Applied at **start of target's turn** (not immediately)
- **Ignores shields** (applies directly to life)
- Erosion rate: 0.10 (double normal)

### Nova Damage (`EffectNovaDamage.java`, type=30)

```python
def calculate_nova(value1, value2, jet, caster, aoe, critical):
    base = (value1 + jet * value2)
    scaled = base * (1 + max(0, caster.science) / 100.0)  # SCIENCE
    raw = round(scaled * aoe * critical_power * (1 + caster.power / 100.0))
    # Capped by missing max_life (erosion already done)
    return min(raw, target.total_life - target.life)
```
- Damages max_life directly (pure erosion), NOT current life

### Life Damage (`EffectLifeDamage.java`, type=28)

```python
def calculate_life_damage(value1, value2, jet, caster, aoe, critical):
    base = ((value1 + jet * value2) / 100) * caster.life  # % of CASTER's life
    raw = base * aoe * critical_power * (1 + caster.power / 100.0)
    # Shields apply normally
    after_shields = max(0, raw * (1 - target.relative_shield/100) - target.absolute_shield)
    return round(after_shields)
```

### Aftereffect Damage (`EffectAftereffect.java`, type=25)

```python
def calculate_aftereffect(value1, value2, jet, caster, aoe, critical):
    base = (value1 + value2 * jet)
    scaled = base * (1 + caster.science / 100.0)  # SCIENCE
    return max(0, round(scaled * aoe * critical_power))
```
- Applied at start of target's turn AND on initial cast
- **Ignores shields**

---

## 3. Healing Formula

### Heal (`EffectHeal.java`, type=2)

```python
def calculate_heal(value1, value2, jet, caster, aoe, critical, target_count):
    base = (value1 + jet * value2)
    scaled = base * (1 + caster.wisdom / 100.0)  # WISDOM
    heal = max(0, round(scaled * aoe * critical_power * target_count))
    # Capped at max_life
    return min(heal, target.total_life - target.life)
```

### Raw Heal (`EffectRawHeal.java`, type=57)
- Same as heal but **no stat scaling** (flat value)

---

## 4. Shield Formulas

### Absolute Shield (`EffectAbsoluteShield.java`, type=6)
```python
value = round((value1 + jet * value2) * (1 + caster.resistance / 100.0) * aoe * critical_power)
# Adds to target's absolute_shield stat (flat damage reduction)
```

### Relative Shield (`EffectRelativeShield.java`, type=5)
```python
value = round((value1 + jet * value2) * (1 + caster.resistance / 100.0) * aoe * critical_power)
# Adds to target's relative_shield stat (% damage reduction)
```

**Both scale with RESISTANCE.**

---

## 5. Buff/Debuff System

### Stat Buffs (Strength, Agility, TP, MP, Resistance, Wisdom)

All stat buffs follow the same pattern:
```python
value = round((value1 + value2 * jet) * (1 + caster.science / 100.0) * aoe * critical_power)
# Added to target's buff_stats[stat_type]
```
**All stat buffs scale with SCIENCE.**

### Raw Buffs (e.g., Whip = raw TP buff)
```python
value = round(value1)  # Flat value, no stat scaling
```
- `RAW_BUFF_TP` (type=32): Adds flat TP (like Whip chip)
- `RAW_BUFF_MP` (type=31): Adds flat MP
- `RAW_BUFF_STRENGTH` (type=38), etc.

### Shackles (Debuffs)

All shackles scale with **MAGIC**:
```python
# TP shackle, MP shackle, Strength shackle, Magic shackle, etc.
value = round((value1 + jet * value2) * (1 + max(0, caster.magic) / 100.0) * aoe * critical_power)
# Subtracted from target's buff_stats[stat_type]
```

### Vulnerability
- **Relative Vulnerability** (type=26): Negative relative shield (no stat scaling)
- **Absolute Vulnerability** (type=27): Negative absolute shield (no stat scaling)
```python
value = round((value1 + value2 * jet) * aoe * critical_power)
# Subtracts from shield stats
```

### Debuff (type=9)
```python
value = int((value1 + jet * value2) * aoe * critical_power * target_count)
# Reduces ALL active buff effects on target by value%
```

### Total Debuff (type=60)
- Removes ALL effects from target (complete purge)

---

## 6. Stat-to-Effect Mapping (Which stat scales what)

| Effect Type | Scaling Stat | Formula Multiplier |
|---|---|---|
| **Damage** (1) | STRENGTH | `(1 + STR/100)` |
| **Heal** (2) | WISDOM | `(1 + WIS/100)` |
| **Buff STR/AGI/TP/MP/RES/WIS** (3,4,7,8,21,22) | SCIENCE | `(1 + SCI/100)` |
| **Relative Shield** (5) | RESISTANCE | `(1 + RES/100)` |
| **Absolute Shield** (6) | RESISTANCE | `(1 + RES/100)` |
| **Poison** (13) | MAGIC | `(1 + MAG/100)` |
| **Shackles** (17,18,19,24,47,48) | MAGIC | `(1 + MAG/100)` |
| **Damage Return** (20) | AGILITY | `(1 + AGI/100)` |
| **Aftereffect** (25) | SCIENCE | `(1 + SCI/100)` |
| **Life Damage** (28) | (% of life) | No stat scaling |
| **Nova Damage** (30) | SCIENCE | `(1 + SCI/100)` |
| **Vitality** (12) | WISDOM | `(1 + WIS/100)` |
| **Vulnerability** (26, 27) | (none) | No stat scaling |
| **Debuff** (9) | (none) | No stat scaling |
| **Raw buffs** (31,32,37,38,...) | (none) | Flat values |

Additionally, **all effects** are multiplied by:
- `aoe` (area attenuation factor, 0.2-1.0)
- `critical_power` (1.0 normal, 1.3 critical)
- `(1 + power/100)` for damage and poison only

---

## 7. Critical Hit System

### Critical Chance
```python
critical_chance = caster.agility / 1000.0
# 100 agility = 10% crit, 500 agility = 50% crit
```
Source: `State.java:870` - `getRandom().getDouble() < ((double) caster.getAgility() / 1000)`

### Critical Effects
- Damage multiplied by `CRITICAL_FACTOR = 1.3`
- Erosion rate increased by +0.10 (0.05 -> 0.15 for damage, 0.10 -> 0.20 for poison)
- **All effect types** get the 1.3x multiplier (shields, heals, buffs, shackles)
- Triggers passive weapon effects (e.g., CRITICAL_TO_HEAL)

---

## 8. Erosion System

Erosion permanently reduces `total_life` (max HP):
```python
erosion = round(damage * erosion_rate)
target.total_life -= erosion
if target.total_life < 1:
    target.total_life = 1  # Can't go below 1
```

| Damage Type | Base Erosion Rate | + Critical |
|---|---|---|
| Direct damage | 0.05 (5%) | 0.15 |
| Poison | 0.10 (10%) | 0.20 |
| Aftereffect | 0.05 (5%) | 0.15 |
| Return damage | same as source | same |
| Nova | N/A (IS erosion) | N/A |

---

## 9. Turn Order System

### Initial Order (`StartOrder.java`)

1. **Sort within teams** by frequency (highest first)
2. **Team order** determined probabilistically by frequency:
   ```python
   probability(team_i) = 1 / (1 + 10^((sum_freq - freq_i) / 100))
   # Normalized so all probabilities sum to 1
   ```
3. **Interleave**: Alternate teams round-robin, picking highest-frequency first within each team

### Turn Flow (`Fight.java`, `Entity.java`)

1. **MAX_TURNS = 64** (draw if both alive after 64 full rounds)
2. Each entity's turn:
   - **Start turn**: Decrease cooldowns, apply start-of-turn effects (poison, aftereffect, heal-over-time)
   - **AI execution**: Entity runs its LeekScript AI code
   - **End turn**: Reset TP/MP to full, clear say/show counters, propagate effects

### Cooldown Mechanics
- `cooldown`: Number of turns before chip can be reused (0 = no cooldown)
- `initial_cooldown`: Turns before chip can be used at fight start
- `team_cooldown`: If true, cooldown applies to all team members
- `max_uses`: Maximum times chip can be used per fight (-1 = unlimited)
- Cooldowns decrease by 1 at **start of owner's turn**

---

## 10. Line of Sight (LOS)

### LOS Algorithm (`Map.java:verifyLoS`)

**Bresenham-style line rasterization** on the rotated grid:

```python
def verify_los(start, end, ignored_cells):
    dx = abs(start.x - end.x)
    dy = abs(start.y - end.y)
    sx = -1 if start.x > end.x else 1
    sy = 1 if start.y < end.y else -1

    # Build path segments
    if dx == 0:
        path = [(0, dy + 1)]
    else:
        d = dy / dx / 2.0
        h = 0
        path = []
        for i in range(dx):
            y = 0.5 + (i * 2 + 1) * d
            path.append((h, ceil(y - 0.00001) - h))
            h = floor(y + 0.00001)
        path.append((h, dy + 1 - h))

    # Check each cell in path
    for segment in path:
        for each cell in segment:
            if not walkable: return False
            if occupied and not in ignored_cells:
                if cell == start: continue
                if cell == end: return True
                return False  # Blocked by entity
    return True
```

**Key rules:**
- Obstacles **always** block LOS
- Entities block LOS **unless** they are the caster, target, or in the ignore list
- Some attacks have `los=false` (no LOS check needed)
- `AREA_FIRST_IN_LINE`: The first entity in the line is ignored for LOS

### Range Verification (`Map.java:verifyRange`)

```python
def verify_range(caster, target, attack):
    dx = caster.x - target.x
    dy = caster.y - target.y
    distance = abs(dx) + abs(dy)  # Manhattan distance

    if distance > attack.max_range or distance < attack.min_range:
        return False

    if caster == target:
        return True

    # Launch type bit flags:
    # bit 0 (1): Line (dx==0 or dy==0)
    # bit 1 (2): Diagonal (|dx|==|dy|)
    # bit 2 (4): Other (everything else)
    if (launch_type & 1) == 0 and (dx == 0 or dy == 0): return False
    if (launch_type & 2) == 0 and abs(dx) == abs(dy): return False
    if (launch_type & 4) == 0 and abs(dx) != abs(dy) and dx != 0 and dy != 0: return False

    return True
```

**Launch types:**
| Value | Name | Allowed Directions |
|---|---|---|
| 1 | LINE | Horizontal + Vertical only |
| 2 | DIAGONAL | Diagonal only |
| 3 | STAR | Line + Diagonal |
| 4 | STAR_INVERTED | Everything except Line & Diagonal |
| 5 | DIAGONAL_INVERTED | Everything except Diagonal |
| 6 | LINE_INVERTED | Everything except Line |
| 7 | CIRCLE | All directions |

---

## 11. Area of Effect

### AoE Attenuation
```python
def get_power_for_cell(target_cell, current_cell):
    # LaserLine, FirstInLine, Allies, Enemies: no attenuation
    if area_type in (LASER_LINE, FIRST_IN_LINE, ALLIES, ENEMIES):
        return 1.0
    dist = cell_distance(target_cell, current_cell)
    return 1 - dist * 0.2
    # Center = 100%, dist 1 = 80%, dist 2 = 60%, dist 3 = 40%, dist 4 = 20%, dist 5 = 0%
```

### Area Types
| ID | Name | Shape |
|---|---|---|
| 1 | POINT | Single cell |
| 2 | LASER_LINE | Line from caster through target |
| 3 | CIRCLE_1 / PLUS_1 | Target + 4 adjacent cells (radius 1) |
| 4 | CIRCLE_2 | Radius 2 circle |
| 5 | CIRCLE_3 | Radius 3 circle |
| 6 | PLUS_2 | Plus shape radius 2 |
| 7 | PLUS_3 | Plus shape radius 3 |
| 8 | X_1 | X shape radius 1 |
| 9 | X_2 | X shape radius 2 |
| 10 | X_3 | X shape radius 3 |
| 11 | SQUARE_1 | 3x3 square |
| 12 | SQUARE_2 | 5x5 square |
| 13 | FIRST_IN_LINE | First entity in line from caster |
| 14 | ENEMIES | All enemies (global) |
| 15 | ALLIES | All allies (global) |

---

## 12. Entity Stats

### Characteristics (from `Entity.java`)

| ID | Name | Effect |
|---|---|---|
| 0 | LIFE | Hit points |
| 1 | TP | Turn Points (action resource) |
| 2 | MP | Movement Points |
| 3 | STRENGTH | Scales direct damage `(1+STR/100)` |
| 4 | AGILITY | Critical chance `AGI/1000`, damage return scaling |
| 5 | FREQUENCY | Turn order priority |
| 6 | WISDOM | Heals `(1+WIS/100)`, life steal `WIS/1000` |
| 9 | ABSOLUTE_SHIELD | Flat damage reduction |
| 10 | RELATIVE_SHIELD | % damage reduction |
| 11 | RESISTANCE | Shield scaling `(1+RES/100)` |
| 12 | SCIENCE | Buff scaling, aftereffect, nova `(1+SCI/100)` |
| 13 | MAGIC | Poison, shackle scaling `(1+MAG/100)` |
| 14 | DAMAGE_RETURN | % of pre-shield damage reflected |
| 15 | POWER | Universal damage multiplier `(1+POW/100)` |
| 16 | CORES | Operations budget per turn |
| 17 | RAM | Max chips equippable |

### Stat Composition
```python
effective_stat = base_stat + buff_stat
# base_stat = allocated from capital
# buff_stat = sum of all active buff effects on this entity
```

### Entity States
- `UNHEALABLE` (0): Cannot receive healing
- `INVINCIBLE` (1): Cannot take damage

---

## 13. Effect Modifiers (Bit Flags)

| Flag | Value | Meaning |
|---|---|---|
| STACKABLE | 1 | Effect stacks with existing (doesn't replace) |
| MULTIPLIED_BY_TARGETS | 2 | Effect value multiplied by number of targets hit |
| ON_CASTER | 4 | Effect applied to caster, not target |
| NOT_REPLACEABLE | 8 | Won't replace existing effect of same type |
| IRREDUCTIBLE | 16 | Cannot be reduced by EFFECT_DEBUFF |

---

## 14. Target Filters (Bit Flags)

| Flag | Value | Meaning |
|---|---|---|
| TARGET_ENEMIES | 1 | Affects enemies |
| TARGET_ALLIES | 2 | Affects allies |
| TARGET_CASTER | 4 | Affects the caster |
| TARGET_NON_SUMMONS | 8 | Affects non-summons |
| TARGET_SUMMONS | 16 | Affects summons |

Common: `targets=31` = all flags (enemies + allies + caster + non-summons + summons)

---

## 15. Effect Duration & Stacking

- `turns=0`: Instant effect (applied once, no duration)
- `turns=N` (N>0): Lasts N turns, decremented at caster's start-of-turn
- `turns=-1`: Permanent (never expires)
- **Non-stackable effects** (default): If same attack applies same effect type to same target, **replaces** old effect
- **Stackable effects**: New effect value added to existing effect's value (merged via `ActionStackEffect`)

---

## 16. Passive Weapon Effects

Weapons can have passive effects triggered by events:
- **DAMAGE_TO_ABSOLUTE_SHIELD** (34): On taking damage, gain % as absolute shield
- **DAMAGE_TO_STRENGTH** (35): On taking damage, gain % as strength buff
- **NOVA_DAMAGE_TO_MAGIC** (36): On taking nova damage, gain % as magic buff
- **POISON_TO_SCIENCE** (33): On taking poison damage, gain % as science buff
- **MOVED_TO_MP** (50): On being moved, gain MP
- **ALLY_KILLED_TO_AGILITY** (55): On ally dying, gain agility
- **KILL_TO_TP** (56): On killing, gain TP
- **CRITICAL_TO_HEAL** (58): On landing critical, heal self

---

## 17. Fight Action Codes (for replay parsing)

| Code | Action | Payload |
|---|---|---|
| 1 | START_FIGHT | `[entities, map]` |
| 2 | NEW_TURN | `[turn_number]` |
| 3 | ENTITY_TURN | `[entity_id]` |
| 4 | END_TURN | `[entity_id]` |
| 5 | MOVE | `[cell_path...]` |
| 6 | KILL | `[entity_id, killer_id]` |
| 7 | USE_CHIP | `[template, cell, [targets...], result]` |
| 8 | USE_WEAPON | `[cell, [targets...], result]` |
| 10 | SET_WEAPON | `[template]` |
| 11 | ADD_EFFECT | `[effect_type, entity, value, turns...]` |
| 12 | DAMAGE | `[entity, damage, erosion]` |
| 13 | HEAL | `[entity, amount]` |

---

## 18. Summary: What a Python Simulator Needs

### Core Systems to Implement
1. **Grid**: Rotated square grid, cell numbering, distance, pathfinding, LOS
2. **Entity**: Stats (base + buff), life, TP/MP tracking, cooldowns, effects list
3. **Damage pipeline**: Base -> stat scaling -> power -> critical -> AoE -> shields -> erosion -> life steal -> damage return
4. **Effect system**: 61 effect types, duration management, start-of-turn triggers, stacking rules
5. **Turn order**: Frequency-based probabilistic team ordering, round-robin interleave
6. **Attack resolution**: Range check -> launch type check -> LOS check -> critical roll -> apply effects to area
7. **Cooldown tracking**: Per-chip, per-entity, decrease at start-of-turn, max_uses

### Can Skip (for MVP)
- Summons/bulbs (complex AI)
- Resurrect mechanics
- Passive weapon effects (rare at our level)
- Custom maps (just generate random)
- Entity propagation effects
- Team cooldowns

### Key Numerical Constants
```python
CRITICAL_FACTOR = 1.3
MAX_TURNS = 64
SUMMON_LIMIT = 8
EROSION_NORMAL = 0.05
EROSION_POISON = 0.10
EROSION_CRITICAL_BONUS = 0.10
SAY_LIMIT_TURN = 2
SHOW_LIMIT_TURN = 5
SAY_COST = 1  # TP
SET_WEAPON_COST = 1  # TP
```
