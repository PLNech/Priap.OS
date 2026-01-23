# Fight Meta Analysis (2026-01-23)

> Analysis of 10,000 public fights from fights_light.db (L1-L51 bracket, Dec 16-25, 2025)

## Executive Summary

**Key Finding**: Short fights strongly favor the attacker. Optimize for burst damage, not sustain.

## 1. Win Rate by Team Position

| Team | Win Rate | Count |
|------|----------|-------|
| Team 1 (Starter) | **68.4%** | 6,838 |
| Team 2 | 29.6% | 2,955 |
| Draw | 2.1% | 207 |

**Insight**: First-mover advantage is massive (~68% base win rate).

## 2. Fight Duration Analysis

### Duration vs Win Rate (CRITICAL)

| Duration | Team 1 Win Rate | Sample Size |
|----------|-----------------|-------------|
| Very short (1-4 turns) | **76.8%** | 1,226 |
| Short (5-7 turns) | **71.2%** | 5,519 |
| Medium (8-10 turns) | **64.7%** | 2,177 |
| Long (11-14 turns) | **64.0%** | 600 |
| Very long (15-29 turns) | **56.3%** | 254 |
| Extreme (30-63 turns) | **63.5%** | 52 |
| **TIMEOUT (64 turns)** | **0.0%** | 171 (ALL DRAWS) |

**Strategic Implications**:
1. **Shorter fights = higher win rate** (inverse correlation)
2. **Very long fights favor defender** (56.3% vs 76.8%)
3. **Timeout = automatic draw** (no win possible at turn 64)
4. **Kite stalemates are losing strategy** (draws hurt ranking)

### Average Duration

| Outcome | Avg Turns | Median |
|---------|-----------|--------|
| Wins | 7.0 | 6 |
| Losses | 7.7 | 7 |
| **Overall** | **7.1** | - |

## 3. Damage Analysis

### Winners vs Losers

| Metric | Winners | Losers | Delta |
|--------|---------|--------|-------|
| Damage Dealt | 118.8 | 111.5 | **+6.5%** |
| Damage Received | 72.6 | 67.2 | +8.0% |
| Survival | 100% | 0% | - |

**Key Insight**: Winners deal slightly more damage AND take slightly more damage. The difference is **who gets the kill first**, not who minimizes damage taken.

## 4. Strategic Recommendations

### Chip Priority (Based on Data)

#### Priority 1: Burst Damage
- **Why**: Short fights win more (76.8% @ 1-4 turns vs 56.3% @ 15+ turns)
- **Target**: Reduce avg fight from 7 turns to 5-6 turns
- **Expected lift**: +2-3% win rate
- **Chips**: flash, flame, rock, spark

#### Priority 2: Mobility/Escape
- **Why**: Break kite stalemates (avoid 64-turn timeout)
- **Effect**: Force engagement or safe retreat
- **Prevents**: 2.1% draw rate
- **Chips**: leather_boots (+2 MP)

#### Priority 3: Healing (Lower Priority)
- **Why**: 100% of winners survive - healing isn't the bottleneck
- **Use case**: Only if losing fights at low HP
- **Risk**: Healing prolongs fights (bad per duration analysis)
- **Chips**: cure, bandage (only if needed)

### Anti-Patterns to Avoid

1. **Kiting that extends fights** - Longer fights favor opponent
2. **Defensive/sustain builds** - Winners deal 6.5% more damage
3. **Stalemate strategies** - 64-turn timeout = guaranteed draw

## 5. Hypotheses to Test

| ID | Hypothesis | Test Method |
|----|------------|-------------|
| H005 | Adding damage chips reduces avg fight duration | Before/after analysis |
| H006 | Flash AOE increases win rate vs grouped enemies | Online A/B test |
| H007 | Protein (+80 STR) scales better than raw damage chips | Simulation |

## 6. Data Limitations

- Database contains **public meta fights**, not our personal history
- No fights with IAdonis (131321) in this sample
- Date range: Dec 16-25, 2025 (may not reflect current meta)
- Level range: L1-L51 (broad, includes many skill levels)

## Source
- Database: `/home/pln/Work/Perso/Priap.OS/fights_light.db`
- Schema: `fights` table with winner, duration, damage columns
