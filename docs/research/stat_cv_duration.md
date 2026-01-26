# stat_cv vs Fight Duration (Strand #73)

## Hypothesis
Pure STR (high `stat_cv`) might be less punishing in long fights than previously assumed. We tested whether the coefficient of variation of primary stats correlates with win rates once fights are bucketed by duration.

## Data & Method
- Source: `data/fights_meta.db` (2535 fights scraped 2026‑01‑23). Filtered for **solo** fights (`fight_type=0`) with a fully downloaded replay payload.
- Durations recomputed from replay actions by counting `NEW_TURN` markers (opcode `6`) to avoid missing JSON metadata.
- Excluded summons; only the two player-controlled leeks per fight were considered.
- Calculated `stat_cv = std(active_stats) / mean(active_stats)` with the same helper used in `alpha_strike.py` (active stats = STR/AGI/WIS/RES/MAG/SCI > 0). Entities with <2 active stats default to 1.0 (pure).
- Duration buckets: short ≤5 turns, mid 6‑15 turns, long ≥16 turns.
- CV buckets: balanced ≤0.60, semi-hybrid 0.61‑0.85, pure >0.85 (captures our 0.94 build).
- For each entity we compared its team to the recorded fight winner to capture win/loss; draws counted when the fight winner was 0.

Sample sizes:

| Duration bucket | Fights | Entities |
|-----------------|--------|----------|
| short (≤5)      | 324    | 678      |
| mid (6-15)      | 711    | 1,443    |
| long (16+)      | 190    | 392      |

## Results

Win rate = wins / (wins + losses). Draw rate = draws / total samples in the bucket.

| Duration | CV bucket | Samples | Win rate | Draw rate | Wins / Losses / Draws |
|----------|-----------|---------|----------|-----------|------------------------|
| short (≤5) | balanced (≤0.6) | 157 | 35.0% | 0.0% | 55 / 102 / 0 |
| short (≤5) | semi-hybrid (0.61-0.85) | 200 | 51.5% | 0.0% | 103 / 97 / 0 |
| short (≤5) | pure (>0.85) | 321 | 51.7% | 0.0% | 166 / 155 / 0 |
| mid (6-15) | balanced (≤0.6) | 348 | 45.4% | 0.0% | 158 / 190 / 0 |
| mid (6-15) | semi-hybrid (0.61-0.85) | 508 | 50.3% | 0.2% | 255 / 252 / 1 |
| mid (6-15) | pure (>0.85) | 587 | 50.7% | 0.2% | 297 / 289 / 1 |
| long (16+) | balanced (≤0.6) | 112 | 50.0% | 32.1% | 38 / 38 / 36 |
| long (16+) | semi-hybrid (0.61-0.85) | 150 | 43.8% | 19.3% | 53 / 68 / 29 |
| long (16+) | pure (>0.85) | 130 | **57.3%** | **42.3%** | 43 / 32 / 55 |

## Findings
1. **Short fights punish imbalanced builds**: Balanced ≤0.6 CV leaks 15‑17 percentage points vs hybrid/pure in ≤5 turn brawls. Semi-hybrid and pure are tied (~51%).
2. **Mid fights neutralize most CV differences**: Once fights stretch past turn 6, all buckets converge around 50% win rate. No evidence that lowering CV improves performance here.
3. **Long fights reward high CV**: Pure builds (>0.85) win 57% of decisive long fights and draw 42% of the time, dwarfing semi-hybrid’s 44% win / 19% draw profile. Balanced builds only tie pure because draws inflate their record; decisive outcomes are 50/50.

## Recommendation
- Keeping our current **stat_cv ≈ 0.94** is aligned with the data for attrition games (turn ≥16). The high draw rate indicates these fights often stall but ultimately favor the pure build when someone lands the final blow.
- If we need stronger short-game reliability, consider nudging one secondary stat up to move into the semi-hybrid bracket (0.7‑0.8 CV). Otherwise, prioritize tools that push fights longer—mobility, sustain, or control—to exploit the pure CV edge.
