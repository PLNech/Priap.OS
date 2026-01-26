# PONR (Point of No Return) Validation

**Objective:** confirm or refute the Alpha Strike notebook claim that “80% of fights are decided by turn 2.7”, using the current `fights_meta.db` corpus (2,434 fights scraped as of 2026‑01‑25).

## Methodology

1. Queried every row from `data/fights_meta.db`.
2. For each fight, walked the raw `fight.data.actions` stream:
   - Built initial team HP pools from `fight.data.leeks` (skipping summons).
   - Subtracted HP whenever a `LOST_LIFE` action fired to keep running HP totals.
   - Tracked the active turn via `NEW_TURN`/`END_TURN`.
   - Marked the **Point of No Return** when one team’s remaining HP was at least double the opponent’s (2:1 ratio) or when a team hit 0 HP.
3. Aggregated the first turn where the ratio triggered (`ponr_turn`). 1,858 fights reached this condition; the rest never produced a 2:1 ratio (usually very even or immediate wipes).

## Results

| Turn threshold | Fights decided ≤ turn | Share of fights with PONR |
|---------------:|----------------------:|---------------------------:|
| ≤ 0            | 299                   | 16.1%                      |
| ≤ 2            | 378                   | 20.3%                      |
| ≤ 3            | 633                   | 34.1%                      |
| ≤ 4            | 917                   | 49.4%                      |
| ≤ 5            | 1,205                 | 64.9%                      |
| ≤ 6            | 1,375                 | 74.0%                      |
| ≤ 7            | **1,502**             | **80.8%**                  |
| ≤ 8            | 1,598                 | 86.0%                      |
| ≤ 10           | 1,702                 | 91.6%                      |
| ≤ 15           | 1,785                 | 96.1%                      |
| ≤ 61           | 1,858                 | 100%                       |

Additional stats:
- Average decisive turn: **5.4**
- Median decisive turn: between 5 and 6 (since 50% threshold crosses between turns 4 and 5).

## Comparison vs Alpha Strike Claim

- Claim: *“80% of fights are decided by turn 2.7.”*
- Observation: only **20.3%** of fights achieve a 2:1 HP split by turn 2, and **34.1%** by turn 3. The 80% mark is not reached until **turn 7**.

**Conclusion:** The 2.7-turn claim does **not** hold on the Priap.OS dataset; fights typically take ~5–7 turns before one side gains a decisive HP edge. Any Alpha Strike heuristics based on the 2.7-turn figure should be recalibrated using the distribution above.***
