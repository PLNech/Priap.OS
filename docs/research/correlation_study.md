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

## Next steps

- Diagnose top FN/FP fights — read action logs, look for systemic fidelity gaps.
- Expand archetype proxy set or tighten selection rule.