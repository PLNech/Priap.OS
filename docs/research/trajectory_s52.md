# IAdonis Trajectory Model

> Generated 2026-04-10T00:00:08.484460 from `rankings.db` + `fights_meta.db`

## Current state

- **Rank**: #8993
- **Talent**: T341
- **Level**: L151
- **WR** (matchmaking, all-time): 48.3% (677/1402)

## Velocities

| Window | Points | Talent/day | Level/day | Rank/day (− = improving) |
|--------|--------|-----------:|----------:|-------------------------:|
| 7d | 7 | -2.59 | +1.25 | +57.0 |
| 30d | 23 | +0.24 | +1.18 | -7.8 |
| 90d | 23 | +0.24 | +1.18 | -7.8 |

## Targets (latest snapshot)

| Rank | Talent needed | Level needed | Talent gap | Level gap |
|-----:|--------------:|-------------:|-----------:|----------:|
| #10 | T3381 | L301 | +3040 | +150 |
| #100 | T2724 | L301 | +2383 | +150 |
| #1000 | T1733 | L301 | +1392 | +150 |

## Projection at current (30d) velocity

| Rank | Days to reach talent | Days to reach level |
|-----:|:---------------------|:--------------------|
| #10 | ∞ | 4.2 months (127 days) |
| #100 | 27.3 years (9965 days) | 4.2 months (127 days) |
| #1000 | 15.9 years (5821 days) | 4.2 months (127 days) |

> Projections are naive linear extrapolation. Thresholds are *static* snapshots; 
> they will move as other leeks level up. Treat as a lower bound on required pace, not a schedule.

## WR sensitivity

> Assumes 50 fights/day, symmetric ±6 talent per result (approximate Elo).

| WR | Talent/day (est) | Days to top-1000 | Days to top-10 |
|---:|-----------------:|:-----------------|:---------------|
| 48% | -12.0 | unreachable at current pace | unreachable at current pace |
| 50% | +0.0 | unreachable at current pace | unreachable at current pace |
| 52% | +12.0 | 3.9 months (116 days) | 8.4 months (253 days) |
| 55% | +30.0 | 1.5 months (46 days) | 3.4 months (101 days) |
| 60% | +60.0 | 23.2 days | 1.7 months (51 days) |

## Data quality

- **fights_latest**: 2026-03-01T12:05:13
- **fights_stale_days**: 39
- **fights_staleness_warning**: Fight DB is 39 days stale — WR baseline is historical, not recent.
- **rankings_points**: 23
- **rankings_span_days**: 27

## Verdict

- **Level is climbing, talent is flat.** We are grinding XP but staying bracket-average (~48% WR). Leveling alone does not move rank — we get matched against higher-talent opponents as we level up.
- **Level ceiling**: top-1000 is L301; we are L151 (gap 150). At 1.2 levels/day, that is ~127 days (4.2 months).
- **Top-10 reality**: needs T3381 and L301. Even at 60% WR, this is measured in *years* without a level breakthrough.
- **Implication**: P1 (level + equipment) is the binding pillar. P2 (AI iteration) contributes only via its effect on WR — which P0 must validate before we trust it.
