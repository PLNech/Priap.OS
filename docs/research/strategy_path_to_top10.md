# Strategy: Path to Top 10

**Date**: 2026-01-24
**Current Level**: 34
**North Star**: Task #0001 - Reach Top 10 Leaderboard

## Current Position Assessment

| Metric | Current | Problem |
|--------|---------|---------|
| Level | 34 | Low - top 10 is likely L300+ |
| Win Rate | 38% raw | Below 50% = net negative talent |
| Draw Rate | 21% | 3x meta average (6.5%) - points bleeding |
| Build | STR 234 | Aligned with meta ✓ |
| Chips | 0/6 equipped | Missing ~60 damage/turn |
| Simulator | Chips broken | Can't test v10 stalemate fix |

## Core Strategic Insight

**We're not competing on fights. We're competing on iteration speed.**

Top players grind manually. We have 13,000:1 leverage (1.8M offline fights/day vs 150 online).
But that leverage is currently broken:
1. Simulator lacks chips → can't test real combat
2. 21% draws → wasting online fights on stalemates
3. No offline validation → deploying blind

## Three-Phase Strategy

### Phase 1: Unblock the Flywheel (This Week)

**Goal**: Make offline testing actually work.

| Blocker | Fix | Impact |
|---------|-----|--------|
| Simulator chips | Fix `compare_ais.py` defaults | Can test v10 |
| v10 stalemate | Validate + deploy | Drop draws 21%→<10% |
| Online chips | `leek market buy` | +60 damage/turn |

**Success metric**: Draw rate < 10%, win rate > 50%

### Phase 2: Data-Driven Climb (Next Month)

**Goal**: Use the flywheel at full speed.

```
Scrape meta → Analyze patterns → Generate AI variants → Test 10k offline → Deploy winner
```

- Scraper continues building L25-300 meta understanding
- Identify what beats us (loss analysis from #0300 pillar)
- Generate counter-strategies, A/B test at 13,000:1

**Success metric**: Climbing ranks weekly, talent trending up

### Phase 3: Endgame Optimization (When L100+)

**Goal**: Study and counter top players specifically.

- Scrape top 10 fight histories
- Identify their patterns, counter-build
- Tournament-specific tactics

## Key Levers

### Lever 1: Draw Rate (Highest Impact)

Our 21% draw rate is 3x the meta average (6.5%).

**Math**: Converting half those draws to wins:
- Current: 38% win, 21% draw, 41% loss
- Target: 48.5% win, 10% draw, 41.5% loss
- Impact: +10.5% effective win rate

This is the difference between bleeding talent and gaining it.

### Lever 2: Chip Damage

Currently 0/6 chips equipped. Missing per-turn damage:
- FLAME: 29 damage (2 TP)
- FLASH: 32 damage (3 TP)
- Combined: +61 damage/turn potential

### Lever 3: Iteration Speed

The 13,000:1 leverage ratio means:
- 1 hour offline = 77,400 simulated fights
- 1 day online = 150 fights max

Every improvement to simulator fidelity multiplies our advantage.

## The Flywheel

```
Fight Online → Collect Data → Analyze Losses → Improve AI Offline
     ↑                                                    ↓
     └──────────── Deploy Best Variant ←──────────────────┘
```

Current bottleneck: "Improve AI Offline" - chips don't work in simulator.

## Success Metrics by Phase

| Phase | Timeline | Key Metric | Target |
|-------|----------|------------|--------|
| 1 | This week | Draw rate | < 10% |
| 1 | This week | Win rate | > 50% |
| 2 | Month 1 | Talent trend | Positive weekly |
| 2 | Month 1 | Level | 50+ |
| 3 | Month 2+ | Rank | Top 100 → Top 10 |

## Immediate Tactics

1. Fix `compare_ais.py` chip defaults (plan exists)
2. Validate v10 offline (100+ fights)
3. Deploy v10 if draw rate < 10%
4. Buy + equip chips online
5. Run 50 fights, measure new baseline
