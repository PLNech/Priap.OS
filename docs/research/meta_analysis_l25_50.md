# Meta Analysis: L25-50 LeekWars Fights

Generated: 2026-01-24
Dataset: 765 fights, 2694 leeks in level range

## Key Findings

### 1. First-Mover Advantage is MINIMAL
```
Attacker (Team1): 48.5% win rate
Defender (Team2): 45.9% win rate
Draws:             5.6%
```
**Insight**: Unlike our simulator (which showed ~93% Team1 bias), real online fights are nearly balanced. The simulator's position advantage doesn't reflect real play.

### 2. STR-Focused Builds Dominate
| Archetype | Count | Win Rate | Avg Level |
|-----------|-------|----------|-----------|
| STR-focused | 1288 | 45.5% | 40.6 |
| STR/AGI hybrid | 1090 | 43.1% | 48.0 |
| MAG-focused | 218 | 40.4% | 49.6 |
| AGI-focused | 51 | 25.5% | 43.0 |
| Balanced | 47 | 23.4% | 33.1 |

**Insight**: Pure AGI builds are WEAK at this level range. STR is king.

### 3. STR Sweet Spot: 100-149
| STR Range | N | Win Rate |
|-----------|---|----------|
| 0-49 | 25 | 24.0% |
| 50-99 | 114 | 43.0% |
| **100-149** | **313** | **49.8%** |
| 150-199 | 170 | 38.8% |
| 200-249 | 522 | 47.5% |
| 300-349 | 60 | 50.0% |

**Insight**: Diminishing returns after ~150 STR. The 100-149 range is optimal for efficiency.

### 4. Average Stats by Level
| Level | N | STR | AGI | MAG | HP | Win% |
|-------|---|-----|-----|-----|-----|------|
| 25-29 | 59 | 143 | 24 | 14 | 426 | 52.5% |
| 30-34 | 300 | 151 | 10 | 2 | 303 | 48.3% |
| 35-39 | 274 | 159 | 28 | 6 | 491 | 47.1% |
| 40-44 | 320 | 166 | 24 | 11 | 549 | 46.9% |
| 45-49 | 1325 | 51 | 35 | 18 | 232 | 41.9% |

**Anomaly**: L45-49 shows LOW STR (51 avg) with poor win rate. This may indicate:
- Many players transition builds at this level
- Or the sample is biased toward weaker players

### 5. Optimal STR by Level
| Level | Avg STR | Optimal | Best Win Rate |
|-------|---------|---------|---------------|
| L25-29 | 162 | 160+ | 80% |
| L30-34 | 168 | 120+ | 70% |
| L35-39 | 166 | 200+ | 80% |
| L40-44 | 174 | 240+ | 100% |
| L45-49 | 238 | 140+ | 51% |

## Implications for Our Build (L34)

Current: STR=234, AGI=10

**Analysis**:
- Our STR (234) is ABOVE average for L30-34 (168)
- Data shows 100-149 STR has best efficiency
- But higher levels need more STR (L40-44 optimal is 240+)

**Recommendation**:
- Current STR allocation is good for future levels
- Consider adding some AGI for hybrid play (43.1% vs 45.5% isn't huge)
- Focus on AI strategy over raw stats

## Draw Rate Analysis

5.6% draw rate suggests stalemate is real but not dominant.
Our reported 21% draw rate is MUCH higher than average.

**Implication**: Our AI has a kiting problem that causes excessive stalemates. Fixing #11 (force_engage) should bring us closer to meta average.

---

*Data collected via BFS graph traversal of leek-fight bipartite graph.*
*Source: `leek scrape discover` + `leek scrape run`*
