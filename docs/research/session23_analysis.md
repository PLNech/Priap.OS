# Session 23 Analysis: 866 Fights Post-v11 (Jan 26 - Feb 10)

## Backfill Summary
- **312 fights scraped** from Feb 5-10 (GH Actions data gap)
- Total tracked: **866 fights** since v11 deploy

## Aggregate Stats
| Metric | Value |
|--------|-------|
| Win Rate | **47.5%** |
| Record | 411W - 414L - 41D |
| Draw Rate | **4.7%** (down from 21% pre-v11) |

## Daily WR Trend
| Date | Fights | W | L | D | WR% | Draw% |
|------|--------|---|---|---|-----|-------|
| Jan 26 | 51 | 26 | 25 | 0 | 51.0 | 0.0 |
| Jan 29 | 51 | 23 | 26 | 2 | 45.1 | 3.9 |
| Jan 30 | 52 | 25 | 25 | 2 | 48.1 | 3.8 |
| Jan 31 | 52 | 24 | 24 | 4 | 46.2 | 7.7 |
| Feb 1 | 101 | 47 | 45 | 9 | 46.5 | 8.9 |
| Feb 2 | 101 | 48 | 49 | 4 | 47.5 | 4.0 |
| Feb 4 | 101 | 48 | 49 | 4 | 47.5 | 4.0 |
| Feb 5 | 51 | 25 | 22 | 4 | 49.0 | 7.8 |
| Feb 6 | 51 | 22 | 24 | 5 | 43.1 | 9.8 |
| Feb 7 | 51 | 25 | 24 | 2 | 49.0 | 3.9 |
| Feb 8 | 51 | 22 | 25 | 4 | 43.1 | 7.8 |
| Feb 9 | 151 | 76 | 74 | 1 | 50.3 | 0.7 |

**Observation**: WR oscillates 43-50%, no clear upward trend. Feb 9 spike (151 fights) from cumulation.

## WR by Fight Duration
| Bracket | Fights | Wins | WR% |
|---------|--------|------|-----|
| 1-5 turns | 245 | 110 | 44.9% |
| 6-15 turns | 414 | 203 | 49.0% |
| 31-50 turns | 1 | 0 | 0.0% |

**Confirms Session 20 finding**: opening is our weakness (44.9% in turns 1-5 vs 49% in 6-15).

## Opponent Comparison (Feb 1+, 627 fights)

| Stat | Beats Us (n=314) | We Beat (n=313) | Delta |
|------|------------------|-----------------|-------|
| **HP** | **572** | 474 | **+98** |
| STR | 155 | 142 | +13 |
| AGI | 10 | 7 | +3 |
| WIS | 41 | 43 | -2 |
| RES | 42 | **51** | **-9** |
| Level | 64 | 63 | +1 |

### Key Findings
1. **HP is the survival threshold** - biggest delta (+98 HP). We die before killing tankier opponents.
2. **STR delta is modest** (+13) - more STR helps but isn't the primary differentiator.
3. **RES doesn't help opponents** - we BEAT higher-RES opponents (51 vs 42). Pure damage reduction is less impactful than raw HP.
4. **WIS is irrelevant** - marginal difference either way.

### Capital Recommendation: All STR
- We can't invest capital in HP (it scales with level).
- RES isn't what separates winners from losers.
- More STR (310 → 505) = 63% more damage = faster kills = less time for HP advantage to matter.
- Glass cannon archetype is correct: kill them before they kill us.
- **Action**: `leek build spend str 195`

## Data Gaps
- `damage_dealt` / `damage_received` not populated in observations (scraper doesn't extract combat stats from replay actions)
- No 16-30 turn bracket fights recorded (interesting - fights either end fast or go long)
