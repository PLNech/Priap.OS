# v11 "Hydra" Fight Analysis - Session 18 (2026-01-24)

## Executive Summary

**40 fights analyzed** (via history API + manual verification)

| Metric | Value | Change from v8 |
|--------|-------|----------------|
| **Win Rate** | 43.6% | -5% (from 48%) |
| **Draw Rate** | **2.5%** | **-18.5%** (from 21%) |
| **Actual W-L-D** | 17W-22L-1D | Fixed logging issue |

## Key Finding: Stalemate Fix WORKS

The draw rate dropped dramatically:
- **Before (v8)**: 21% draws (kite stalemates)
- **After (v11)**: 2.5% draws (1 draw in 40 fights)

The `force_engage` logic triggers correctly after turn 25 with low damage.

## Data Quality Issue

**Original logging showed all 40 as "D"** (draws) because:
1. Script assumed `my_team = 1` always
2. When we're team 1, opponent wins = `winner=2`
3. Code fell through to draw check incorrectly

**Fixed**: Now determines team by checking leek IDs in `leeks1`/`leeks2`.

## Fight Breakdown

### By Result
- Wins: 17 (42.5%)
- Losses: 22 (55%)
- Draws: 1 (2.5%)

### By Level Difference
All opponents at same level (+0) - matchmaking is fair.

### Sample Fights
| Result | Opponent | Fight ID |
|--------|----------|----------|
| W | SoupoPoireau | #51211572 |
| L | Guido | #51211571 |
| L | rambothai2 | #51211570 |
| W | QLF | #51211562 |
| D | philippe74334 | #51211527 |

## Technical Fixes Made

1. **auto_daily_fights.py**: Fixed team detection logic
2. **fight.py CLI**: Fixed history, run, and added analyze command
3. **CLAUDE.md**: Added strict fight permission rule

## Next Steps

1. Monitor v11 over more fights to confirm draw rate stays <5%
2. Investigate why win rate dropped (43% vs 48%)
3. Consider if `force_engage` is too aggressive (causes more losses?)

## Learnings

- **Always verify which team you're on** before interpreting winner field
- **CLI is the source of truth** - fix it first when discovering API quirks
- **Draw rate is the key metric** for stalemate fix validation
