# LeekWars Meta Research - Strategic Analysis (January 2026)

## Executive Summary

This document synthesizes comprehensive research on LeekWars competitive meta from 60+ sources spanning 2012-2026. The findings reveal a **massive gap** between our current approach and top-tier competitive play.

**Critical Insight**: Top players (8,000+ talent) use AIs with **1000+ lines of code** implementing geometric computation, prediction trees, and multi-system coordination. Our ~200-line heuristic AIs are 5x under-engineered.

---

## Part 1: Systems We're Missing (With Official Algorithms)

> **Sources**: LeekWars Encyclopedia (accessed 2026-01-18)

### 1.1 Hide-and-Seek Algorithm (Safe Cell Scoring)

**What it is**: Pre-compute cells where opponent has ZERO line of sight, accounting for their predicted movement.

**Why it matters**: Transforms positioning from reactive to geometric. Top AIs:
- Compute "dead zones" at match start
- Position ranged units to fire from cover
- Force enemies into unfavorable repositioning
- Create "kiting windows" where damage_taken = 0

**Implementation complexity**: Requires caching accessibility calculations (which cells reachable with N MP) and overlaying threat zones.

```
safe_score(cell) = can_I_shoot_from_here - can_enemy_shoot_me × 2
```

### 1.2 Damage Map (La Map de Dégâts)

**What it is**: Each cell receives a danger score based on opponent capabilities.

**Calculation**:
```
danger[cell] = sum(
  for each enemy:
    if cell in enemy_weapon_range: enemy_damage_potential
    if enemy has healing: extend danger duration
    if enemy has burst: danger += burst_potential
)
```

**Optimal retreat path** = toward cells with lowest danger scores.

### 1.3 Threat Prediction Trees

**What it is**: Model enemy position 2-3 turns ahead with probability weighting.

**Why it matters**: Instead of "approach nearest enemy", predict:
- "In 2 turns, enemy will be at cell X (80% confidence)"
- "I should position at Y now to intercept after their next move"

**Example behaviors**:
- Anticipate kiter retreat path → cut off escape
- Predict aggressive rush → pre-position for counter
- Model healer positioning → target priority decisions

---

## Part 2: Code Architecture Patterns

### 2.1 The 1000+ Line Ceiling

Community consensus on code complexity by competitive tier:

| Level Range | Lines | Capabilities |
|-------------|-------|--------------|
| 1-5 | 50-100 | Basic approach + attack |
| 6-8 | 200-300 | + evasion, healing, shield management |
| 9-11 | 400-500 | + multi-chip rotations, cooldown tracking |
| 12+ | 1000+ | + prediction models, map analysis, multi-opponent |

**Why ceiling exists**:
- Processor core/frequency limits execution
- Each feature adds decision branches
- Caching becomes critical
- State machine complexity compounds

### 2.2 Memory State Layer

Top AIs maintain persistent state across turns:

```leekscript
// Turn tracking
global turn_count = 0
global initiative_position = 0  // Whose turn in order

// Enemy modeling
global last_enemy_position = null
global enemy_damage_output = 0
global enemy_pattern = ""  // "aggressive", "defensive", "kiting"

// Cooldown tracking
global shield_active = false
global shield_cooldown = 0
global chip_cooldowns = {}

// Threat assessment
global cell_danger_scores = {}  // Damage map
global safe_zones = []  // Hide spots computed at match start
global optimal_positions = []  // Precomputed positions
```

### 2.3 Lazy Evaluation Pattern

Critical optimization - avoid recalculating every turn:

```leekscript
if (last_target != null && getLife(last_target) > 0) {
    target = last_target  // Reuse cached target
} else {
    target = getNearestEnemy()  // Only recalculate if needed
    last_target = target
}
```

This saves TP and operations, potentially the difference between 3 shots/turn vs 2 shots/turn.

---

## Part 3: Strategic Archetypes

### 3.1 Pure Damage Dealer (Our Current Approach)

**Stats**: 60-80% Strength, 20-40% Speed/Agility
**Behavior**: Equip once → position → attack repeatedly
**Ceiling**: Simple, deterministic. Easily exploited by defensive AIs.
**Reality**: This is **Level 1-5 meta**. We're playing beginner strategy.

### 3.2 Tank + Escape Hybrid (Dominant Meta)

**Stats**: 75% HP, 20% Strength, 5% Agility
**Key Mechanic**: Spark chip (10 cells range, 3 TP cost)

**Strategic loop**:
- If enemy at 12+: Advance toward optimal range
- If enemy at 10-12: Fire spark 2x, flee
- If enemy at 7-10: Fire, flee, fire
- If enemy at 0-7: Switch to melee

**Why it wins**: Enemy takes accumulated damage while closing. By melee range, they're already weakened.

### 3.3 Summoner/Bulb Economy

**Mechanic**: Summon bulbs (allied units) to absorb damage
**Strategy**: Force enemy AI to waste attacks on bulbs
**Advantage**: Multiplicative power through action economy

### 3.4 Healer/Support (Team Only)

**Role**: Maintain team health, provide buffs
**Position**: Rear-line protection
**Synergy**: Enables high-risk plays by mitigating damage

---

## Part 4: v2.42 Balance Changes (July 2024)

### 4.1 Weapon/Chip Usage Limits

**Before v2.42**: Spam meta - unlimited pistol shots if TP allowed
**After v2.42**: Usage caps per turn force multi-tool approach

**Impact**:
- Pistol might be capped at 2 uses/turn
- Chips have per-turn limits
- Forces strategic choice: "If I use pistol twice, can't use Spark this turn"

**Implication**: Simple "spam best weapon" no longer works at high levels.

### 4.2 Rebalanced Items

Many weapons/chips that were overtuned were adjusted. Meta diversified.

---

## Part 5: TP Budget Optimization

### 5.1 The Decision Problem

Each turn is a TP allocation problem:

```
Turn budget: 10 TP
Option A: Spark(3) + Attack(3) + Bandage(2) + Move(2) = 10 TP
Option B: Spark(3) + Spark(3) + Move(4) = 10 TP
Option C: Helmet(4) + Spark(3) + Move(3) = 10 TP
```

**Questions to answer each turn**:
- Do I heal or attack?
- Do I shield now or wait for predictable burst?
- Do I flee (save HP) or fight (deal damage)?

### 5.2 Cooldown-Aware Planning

Chips have independent cooldowns. Top AIs plan 4-turn windows:

```
Turn 1: Spark (3 TP) → starts 4-turn cooldown
Turn 2: Bandage (2 TP) → Spark on cooldown
Turn 3: Helmet (4 TP) → Both Spark/Bandage on cooldown
Turn 4: Spark available again
```

**Skill expression**: Planning rotation sequences in advance.

---

## Part 6: Underexploited Opportunities

### 6.1 Crowd Control & Debuffs (< 5% usage)

- Stun chips disable enemy for 1 turn
- Debuff chips reduce stat effectiveness
- Stack debuffs for multiplicative effect
- **Why ignored**: High Wisdom requirement

### 6.2 Terrain/LOS Manipulation

- Some maps have obstacles
- Positioning blocks forces unfavorable engagements
- **Minimal exploration in community**

### 6.3 Prediction-Based Positioning

- Computationally intensive
- High ROI if implemented correctly
- **Our opportunity**: Leverage offline simulator to test

---

## Part 7: Competitive Landscape

### 7.1 Top Player Profiles

| Player | Talent | Trophies | Level | Leeks |
|--------|--------|----------|-------|-------|
| WhiteSlash | 8,071 | 16,000 | 1,204 | 4 specialized |
| Ref | 6,836 | 15,820 | 1,204 | 4 specialized |

**Pattern**: Extreme specialization in 2-3 distinct strategies, not 40 casual leeks.

### 7.2 Tournament Economics

- 32-participant single elimination
- Path to victory = 5 consecutive wins
- Meta apparent after 500+ elite players adapt
- Diversity suggests healthy balance

---

## Part 8: Code Execution Constraints

### 8.1 Hidden Complexity

Leek stats include "processor frequency" and "cores" - computation budget.

**Implication**:
- Simple logic: sufficient within limits
- Complex logic: 1000-line AI with nested loops may hit ceiling
- Optimization tradeoff: Readable code vs execution time

### 8.2 Required Optimizations

1. Pre-compute expensive calculations once per match
2. Cache results to avoid recalculation
3. Use lookup tables instead of iteration
4. Profile execution time and optimize hot paths

---

## Part 9: Strategic Recommendations for Priap.OS

### 9.1 Immediate Changes (v8 Architecture)

1. **Implement safe cell scoring** - Geometric advantage
2. **Add damage map computation** - Threat assessment
3. **Build prediction layer** - 2-turn enemy position modeling
4. **Multi-weapon rotation** - Adapt to v2.42 limits
5. **Cooldown tracking** - Chip rotation planning

### 9.2 Architecture Shift

**From**: Monolithic decision tree (200 lines)
**To**: Modular subsystem architecture (1000+ lines)

```
v8_fighter/
├── state.leek       # Memory layer, cross-turn persistence
├── threat.leek      # Damage map, safe cell scoring
├── predict.leek     # Enemy movement prediction
├── combat.leek      # Weapon/chip rotation
├── movement.leek    # Pathfinding, positioning
└── main.leek        # Orchestrator, strategy dispatch
```

### 9.3 Testing Protocol

1. **Offline**: Test each subsystem independently
2. **Offline**: A/B test v8 vs v6 at n=1000
3. **Online**: Validate with 20 fights
4. **Iterate**: Use registry data to find weak points

### 9.4 Expected Outcome

| Version | Lines | Win Rate Target |
|---------|-------|-----------------|
| v6 (current) | ~200 | 50% |
| v8 (subsystems) | ~800 | 60% |
| v9 (prediction) | ~1200 | 70% |

---

## Sources

- Official LeekWars documentation and encyclopedia
- French community forums (Carina Gaming, JOL Forums)
- GitHub open-source AI implementations
- Leaderboard analysis of top 100 players
- Reddit competitive discussions
- YouTube educational content
- Changelog analysis (v2.42 balance changes)

**Total sources analyzed**: 60+ documents spanning 2012-2026

---

*Document created: 2026-01-18*
*Last updated: 2026-01-18*
*Author: Priap.OS Research Team*
