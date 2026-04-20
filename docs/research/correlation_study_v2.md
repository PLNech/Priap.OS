# PySim ↔ Online Correlation Study

> Generated 2026-04-20T11:35:01  
> Sample: 50 fights × 5 sim reps = 250 PySim runs

## Headline

**Agreement**: 23/50 = **46.0%**

❌ **Gate failed**: PySim disagrees with reality too often. Fix fidelity before trusting tournament outcomes.

## Confusion matrix

| | PySim says WIN | PySim says LOSS |
|---|---:|---:|
| **Real WIN** | 18 (TP) | 5 (FN) |
| **Real LOSS** | 22 (FP) | 5 (TN) |

## Per-archetype breakdown

| Archetype | N | Agree | Accuracy |
|:--|-:|-:|-:|
| str_heavy | 45 | 21 | 46.7% |
| balanced | 5 | 2 | 40.0% |

## Archetype distribution in sample

- balanced: 5
- str_heavy: 45

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