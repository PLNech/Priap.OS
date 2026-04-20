# PySim ↔ Online Correlation Study

> Generated 2026-04-19T21:49:52  
> Sample: 50 fights × 5 sim reps = 250 PySim runs

## Headline

**Agreement**: 27/50 = **54.0%**

❌ **Gate failed**: PySim disagrees with reality too often. Fix fidelity before trusting tournament outcomes.

## Confusion matrix

| | PySim says WIN | PySim says LOSS |
|---|---:|---:|
| **Real WIN** | 23 (TP) | 0 (FN) |
| **Real LOSS** | 23 (FP) | 4 (TN) |

## Per-archetype breakdown

| Archetype | N | Agree | Accuracy |
|:--|-:|-:|-:|
| str_heavy | 47 | 25 | 53.2% |
| balanced | 3 | 2 | 66.7% |

## Archetype distribution in sample

- str_heavy: 47
- balanced: 3

## Methodology notes

- Our AI: `fighter_v14_flat.leek` (deployed version).
- Opponent AI: archetype proxy from `ais/opponents/` selected by dominant opponent stat.
- Equipment / stats / spawn / obstacles: faithfully lifted from real fight JSON via `setup_from_fight(restrict_equipment=True)`.
- Seed varied per replay; majority winner taken across K reps.
- **Noise floor** of archetype proxy: expect ≤5pp loss vs. true opponent AI source.
- Skipped: 0; Per-rep errors: 0.

## Diagnostic: turn-count fingerprint

Comparing real vs PySim turn counts by outcome class reveals the failure mode:

| Class | n | Real turns | PySim turns | Ratio |
|:--|-:|-:|-:|-:|
| TP (correct wins) | 23 | 7.3 | 7.4 | **1.02** |
| TN (correct losses) | 4 | 5.2 | 5.9 | 1.13 |
| **FP (false wins)** | **23** | **14.4** | **6.9** | **0.48** |

**Interpretation**: When PySim's fight length matches reality, the winner
agrees. When PySim cuts the fight short (FP), it incorrectly calls us the
winner. Real STR-heavy opponents at our bracket survive 14+ turns because
they stack Helmet + Shield + Armor + Motivation. Our archetype proxy
(`cktang88_magnum1.leek`) is pure offense: `setup_from_fight` gives it the
shield chips from the real fight, but the AI source never invokes them.
Opponent gets one-shot by our Flame, PySim declares win turn 4-6.

**This is a proxy AI problem, not an engine problem.** The engine simulates
faithfully when both AIs play like their real counterparts (TP/TN cases
matched real turn count). It misfires only when the proxy AI is weaker than
the real opponent.

## Implication for v15 gate

- **Absolute** PySim win-rate is unreliable (±25pp overconfidence).
- **Relative** PySim ELO between two of our AIs *might* still rank-order
  correctly, since both face the same weak-proxy pool. Unverified.
- Safe gate for v15 deploy: **real A/B test** against v14, ~100 fights each
  (2 days of our 50/day budget). The correlation study doesn't buy us a
  shortcut around this.

## Follow-up v2 (2026-04-20): defensive proxy didn't help

Hypothesis: replace cktang88_magnum1 with a simpler proxy that unconditionally
stacks Helmet/Shield/Armor/Armoring turn 1. Built `proxy_defensive_striker.leek`
and verified via action-log inspection that it does cast these chips (unlike
cktang88 which has over-conditional gates).

Result (`correlation_study_v2.md`):
- **Accuracy 46% — slightly worse than 54%.**
- FP count dropped 23 → 22, but 5 new FN cases appeared (proxy now
  occasionally beats v14 in sim when real had us winning).
- FP turn ratio barely moved: 0.48 → 0.53.

Interpretation: the proxy's defense wasn't the bottleneck. When we inspected
one FP fight (id 51864249), v14 in PySim dealt **~720 damage in 5 turns**
regardless of whether the opponent cast 2 or 4 shield chips. Real fight:
same matchup ran 13 turns and we lost. So v14 executes in PySim in a way
that deals far more damage per turn than reality allows.

**Likely real causes** (ordered by how much they'd explain):
1. **Ops limit / TP starvation**: real v14 may hit ops cap and skip actions
   PySim completes normally (see task #70, #98).
2. **LOS / range failures in real maps**: PySim maps from our DB might have
   friendlier geometry than live-game maps we actually play.
3. **Frequency/initiative differences**: order-of-play matters when one side
   has a glass cannon; PySim may always resolve our action first.
4. **Chip effect fidelity**: subtle formula differences on Flame damage or
   shield application stacking.

None of these are quick proxy fixes. Real A/B testing v14 vs v15 on the
50-fight/day budget remains the only decisive gate.

## Next steps

1. **Abandon the "fix the proxy" path.** v2 disproved that hypothesis.
2. Diagnose the v14-execution fidelity gap — instrument real vs sim
   action counts per turn. Start with ops counts from fight_data.ops.
3. Independent of sim work, set up v14 vs v15 real A/B as the decisive
   gate. Sim tournaments remain useful for iterative A/B tests BETWEEN our
   own AIs (both face the same skewed proxy pool), but not for absolute
   prediction against humans.
4. Classifier bug fixed post-study (`f52086880` STR 70 / WIS 380 / RES 380
   now routes to `balanced`).