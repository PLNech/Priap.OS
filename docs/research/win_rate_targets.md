# Win Rate Targets

> **Last Updated**: 2026-01-25 (Session 25)
> **Purpose**: Define success metrics per level band to know when we're winning.

---

## Executive Summary

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| Our WR (ex-draw) | 49.7% | 55%+ | +5.3% |
| Our Draw Rate | 2.0% | <10% | ✓ |
| Meta Team1 WR | 69.8% | N/A (position bias) |
| % 50+ turn fights | 1.9% | <5% | ✓ |

**Key Finding**: Our 49.7% WR is NOT statistically distinguishable from 50% (p=1.0). We need ~1256 more fights to confirm if we're below 55% target.

---

## Our Fight Record (n=152)

From `data/fights_meta.db`:

| Opponent Level | Fights | W-L-D | WR (raw) | WR (ex-draw) | Avg Turns |
|----------------|--------|-------|----------|--------------|-----------|
| All opponents | 152 | 74-75-3 | 48.7% | 49.7% | 2.0 |

### Statistical Validation

| Comparison | p-value | Significant? |
|------------|---------|--------------|
| vs 50% (random) | 1.0000 | NO |
| vs 55% (target) | 0.2167 | NO |
| vs 60% (top player) | 0.0119 | **YES** |

**95% CI**: [41.4%, 58.0%] - Margin of error: ±8.3%

**Sample size needed**: ~1405 ex-draw fights to detect 5.3% gap to 55% target. Currently have 149.

---

## Meta Analysis (n=10,000 scraped fights)

### Duration Distribution

| Duration | Count | % |
|----------|-------|---|
| 0 (forfeit) | 1 | 0.0% |
| 1-3 turns | 312 | 3.1% |
| 4-5 turns | 2,834 | 28.3% |
| 6-10 turns | 5,776 | 57.8% |
| 11-20 turns | 779 | 7.8% |
| 21-50 turns | 113 | 1.1% |
| 50+ turns | 185 | 1.9% |

**Meta average**: 8.1 turns (we average 2.0 - seems we're getting quick finishes or forfeits)

### Win Rate by Duration (ex-draws)

| Duration | N | Team1 WR | Team2 WR |
|----------|---|----------|----------|
| 4-5 turns | 3,116 | 75.2% | 24.8% |
| 6-10 turns | 5,771 | 68.2% | 31.8% |
| 11-20 turns | 779 | 62.3% | 37.7% |
| 21-50 turns | 113 | 58.4% | 41.6% |
| 50+ turns | 14 | 64.3% | 35.7% |

**Critical Insight**: Team1 wins 69.8% ex-draw overall. Short fights = high Team1 advantage. Long fights = more even.

---

## Draw Rate Analysis

| Source | Draw Rate |
|--------|-----------|
| Our fights | 2.0% |
| Meta (10k) | 2.1% |
| Meta (50+ turns) | ~75% |

**Good news**: Our draw rate is acceptable. The meta has very low draw rate overall - long fights are rare (1.9% of 10k).

---

## Updated Targets

### Tier 1 (Critical - Next Session)
- [ ] Overall WR > 50% ex-draw (current: 49.7%)
- [ ] Draw rate < 10% (current: 2.0% ✓)
- [ ] Demonstrate statistical significance (n > 300)

### Tier 2 (Growth - This Week)
- [ ] Overall WR > 55% ex-draw
- [ ] Narrow 95% CI to ±5% margin

### Tier 3 (Elite - This Month)
- [ ] Overall WR > 60% ex-draw
- [ ] Beat meta first-mover (69.8%) adjusted for position bias

---

## Action Items

1. **Collect More Data**
   - Current sample (149 ex-draw) is too small for statistical significance
   - Need ~1256 more meaningful fights
   - Run: `leek scrape top --top 100 --fights-per-leek 20`

2. **Analyze Duration Pattern**
   - Our avg duration (2.0 turns) seems suspiciously low
   - Check if duration=0 fights are being counted correctly
   - Verify we're not losing to immediate forfeits

3. **Update Tracking**
   - Add level-banded analysis to `leek fight analyze`
   - Track WR by opponent level band separately

---

## References

- `data/fights_meta.db` - Our fights (n=152)
- `fights_light.db` - Scraped meta (n=10,000)