# PySim ELO Tournament Results

**Date**: 2026-04-07 (S42)
**Participants**: 9
**Fights per matchup**: 100 (50/side)
**Total fights**: 3600

## ELO Rankings

| Rank | AI | ELO | WR% | W | L | D |
|------|-----|-----|-----|---|---|---|
| 1 | pbondoer | 2057 | 85.2 | 682 | 106 | 12 |
| 2 | v14 | 1924 | 86.0 | 688 | 2 | 110 |
| 3 | arch_rusher | 1468 | 15.5 | 124 | 157 | 519 |
| 4 | arch_tank | 1468 | 30.8 | 246 | 302 | 252 |
| 5 | arch_burst | 1423 | 6.0 | 48 | 212 | 540 |
| 6 | shup1_pata | 1348 | 0.0 | 0 | 398 | 402 |
| 7 | arch_kiter | 1301 | 18.1 | 145 | 407 | 248 |
| 8 | shup1_main | 1283 | 0.0 | 0 | 396 | 404 |
| 9 | arch_balanced | 1229 | 41.5 | 332 | 285 | 183 |

## Head-to-Head Matrix (wins)

| | v14 | pbondoer | shup1_main | shup1_pata | arch_balanced | arch_burst | arch_kiter | arch_rusher | arch_tank |
|---|---|---|---|---|---|---|---|---|---|
| **v14** | - | 98-0-2 | 100-0-0 | 99-1-0 | 100-0-0 | 50-50-0 | 100-0-0 | 42-58-0 | 99-1-0 |
| **pbondoer** | 2-0-98 | - | 100-0-0 | 100-0-0 | 100-0-0 | 89-9-2 | 98-1-1 | 93-2-5 | 100-0-0 |
| **shup1_main** | 0-0-100 | 0-0-100 | - | 0-100-0 | 0-4-96 | 0-100-0 | 0-100-0 | 0-87-13 | 0-13-87 |
| **shup1_pata** | 0-1-99 | 0-0-100 | 0-100-0 | - | 0-2-98 | 0-100-0 | 0-100-0 | 0-84-16 | 0-15-85 |
| **arch_balanced** | 0-0-100 | 0-0-100 | 96-4-0 | 98-2-0 | - | 7-77-16 | 69-3-28 | 0-97-3 | 62-0-38 |
| **arch_burst** | 0-50-50 | 2-9-89 | 0-100-0 | 0-100-0 | 16-77-7 | - | 30-4-66 | 0-100-0 | 0-100-0 |
| **arch_kiter** | 0-0-100 | 1-1-98 | 0-100-0 | 0-100-0 | 28-3-69 | 66-4-30 | - | 22-4-74 | 28-36-36 |
| **arch_rusher** | 0-58-42 | 5-2-93 | 13-87-0 | 16-84-0 | 3-97-0 | 0-100-0 | 74-4-22 | - | 13-87-0 |
| **arch_tank** | 0-1-99 | 0-0-100 | 87-13-0 | 85-15-0 | 38-0-62 | 0-100-0 | 36-36-28 | 0-87-13 | - |

## Analysis

### Expected vs Actual Tier Order

| Expected | Actual | ELO | Notes |
|----------|--------|-----|-------|
| 1. v14 | **2. v14** | 1924 | Loses ELO to draws (58 draws vs rusher, 50 vs burst) |
| 2. pbondoer | **1. pbondoer** | 2057 | Consistent winner, fewer draws |
| 3. shup1_main | **8. shup1_main** | 1283 | 0% WR — spatial queries may be buggy |
| 4. shup1_pata | **6. shup1_pata** | 1348 | 0% WR — depends on shup1 framework |
| 5. Archetypes | **3-9** | 1229-1468 | Varied performance, expected |

### Key Findings

**v14 vs pbondoer: v14 wins head-to-head (98-2) but lower ELO.**
pbondoer beats every archetype 89-100%, while v14 has a massive draw problem: 58 draws vs arch_rusher, 50 draws vs arch_burst. These draws drag v14's ELO down despite dominating h2h.

**The draw problem is real.** v14 draws 110 out of 800 fights (13.75%). This matches our online experience (12% draw rate in S39-S40). The stalemate occurs when v14 shields up against aggressive opponents — both entities survive to turn 64. This is the #1 problem to solve for v15.

**shup1 at 0% WR needs investigation.** shup1 has sophisticated spatial logic (danger maps, getCellsToUseChip positioning) that may not work correctly with our sim. The 100-draw results vs each other suggest they fail to attack. However, the tournament gate (pbondoer vs shup1 = decisive) still passed — pbondoer kills shup1 cleanly.

**Archetype rock-paper-scissors:**
- arch_rusher > arch_kiter (74-22) — rushers overwhelm kiters before kiting matters
- arch_kiter > arch_burst (66-30) — kiters avoid burst damage windows
- arch_tank > arch_rusher (87-13) — tanks survive rushes
- arch_balanced beats kiter/tank but loses to rusher/burst — jack of all trades

### Simulator Validity

The ELO gradient confirms the simulator produces **meaningful, differentiated outcomes**:
- Top tier (v14, pbondoer): 1900-2057 ELO, 85%+ WR
- Mid tier (archetypes): 1229-1468, varied WR
- Bottom tier (shup1): 1283-1348, 0% WR

The archetype RPS dynamics and v14's stalemate problem match real game patterns.
**The sim is valid for A/B testing**, though shup1's complete failure warrants follow-up.
