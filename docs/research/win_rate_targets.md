# Win Rate Targets

> **Last Updated**: 2026-01-25
> **Purpose**: Define success metrics per level band to know when we're winning.

---

## Executive Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Overall WR (ex-draw) | 48.8% | 55%+ | +6.2% |
| Draw Rate | 13.7% | <10% | -3.7% |
| Avg Fight Duration | 12.1 turns | 5-10 turns | -2 to -7 turns |

---

## Our Historical Performance

Based on 211 recorded fights:

| Opponent Level | Fights | W-L-D | WR (raw) | WR (ex-draw) | Avg Turns |
|----------------|--------|-------|----------|--------------|-----------|
| L0-19 | 98 | 41-54-3 | 41.8% | 43.2% | 7.7 |
| L20-29 | 113 | 41-43-29 | 36.3% | 48.8% | 16.6 |
| **TOTAL** | 211 | 82-97 | 38.9% | 45.8% | 12.1 |

**Key Finding**: We perform 5.6% worse against equal/higher level opponents (48.8% → 43.2% WR). This suggests our AI needs improvement in:
1. Closing out fights before opponent scales
2. Pressure/aggro against defensive play

---

## Meta Benchmarks (n=2535 scraped fights)

### First-Mover Advantage
| Matchup | Team1 WR | Team2 WR | Draw Rate | Avg Turns |
|---------|----------|----------|-----------|-----------|
| FAVORED | 54.7% | 38.4% | 6.7% | 1.9 |
| EVEN | 52.2% | 43.8% | 4.0% | 0.1 |
| UNDERDOG | 45.5% | 48.2% | 6.3% | 1.1 |

**Takeaway**: ~52% baseline for first-mover. We should target 55%+ (3% advantage over meta).

### Duration Impact on Win Rate
| Duration | Team1 WR | Draw Rate |
|----------|----------|-----------|
| 0-5 turns | 75.0% | 0% |
| 6-10 turns | 75.0% | 0% |
| 11-15 turns | 50.0% | 0% |
| 16-20 turns | 75.0% | 0% |
| 21-30 turns | 33.3% | 0% |
| 31-50 turns | 46.7% | 0% |
| 50+ turns | 25.0% | 75% |

**Critical Insight**: Long fights → high draw rate. **Target: finish by turn 10.**

---

## PONR Thresholds (from `docs/research/ponr_validation.md`)

| Level Band | Avg PONR | 80% KO | Recommended Max Duration |
|------------|---------|--------|--------------------------|
| L20-39 | 4.58 | Turn 7 | 8 turns |
| L40-59 | 5.57 | Turn 8 | 10 turns |
| L60-79 | ~6.0 | Turn 9 | 11 turns |
| L100-119 | 6.75 | Turn 9 | 12 turns |

**Our fights average 12.1 turns** - we're 2-4 turns slower than the meta expects.

---

## stat_cv Correlation

From `docs/research/stat_cv_duration.md`:
- **Pure builds (CV > 0.85)**: 57% WR in 16+ turn fights
- **Balanced builds (CV ≤ 0.6)**: 35-45% WR in long fights

**Our build**: CV = 0.94 (pure STR) → Good for attrition
**Problem**: We're LOSING long fights anyway (38.9% WR, high draw rate)

**Conclusion**: stat_cv validates our build choice, but execution is the problem.

---

## Targets by Opponent Level

### L0-19 (Underleveled Fights)
| Metric | Current | Target | Notes |
|--------|---------|--------|-------|
| WR | 43.2% | 65%+ | Should dominate weaker opponents |
| Avg Turns | 7.7 | <6 | Quick kills expected |
| Draw Rate | 3.1% | <2% | Rarely draw vs weaker |

### L20-29 (Competitive Fights)
| Metric | Current | Target | Notes |
|--------|---------|--------|-------|
| WR | 48.8% | 55%+ | Match first-mover advantage |
| Avg Turns | 16.6 | <10 | Too slow! |
| Draw Rate | 25.7% | <10% | High draw = kiting problem |

### L30+ (Challenging Fights)
| Metric | Current | Target | Notes |
|--------|---------|--------|-------|
| WR | N/A (need data) | 45%+ | Accept lower, focus on not drawing |

---

## Success Criteria

### Tier 1 (Critical - Next Session)
- [ ] Overall WR > 50% ex-draw
- [ ] Draw rate < 10%
- [ ] Avg fight duration < 10 turns
- [ ] L20-29 WR > 52%

### Tier 2 (Growth - This Week)
- [ ] Overall WR > 55% ex-draw
- [ ] Draw rate < 5%
- [ ] L0-19 WR > 60%

### Tier 3 (Elite - This Month)
- [ ] Overall WR > 60% ex-draw
- [ ] Win rate > meta first-mover (52%) by 5%+

---

## Action Items

1. **Reduce Draw Rate**
   - Implement "force_engage" at turn 15-20 (from v10 fix)
   - Better chip timing for damage spike

2. **Faster Kills**
   - Optimize range calculations (reduce TP waste)
   - Prioritize damage over safety in mid-fight

3. **Level Band Tracking**
   - Add to fight analysis: `leek fight analyze --by-level`
   - Track progress against these targets

---

## References

- `data/fight_history.json` - Our historical fights
- `data/fights_meta.db` - Scraped meta data (n=2535)
- `docs/research/stat_cv_duration.md` - stat_cv analysis
- `docs/research/ponr_validation.md` - PONR thresholds