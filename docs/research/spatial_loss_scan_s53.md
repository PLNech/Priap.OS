# Spatial Loss Scan — S53

Batch-ran `--spatial` over recent IAdonis losses. Each anomaly is a code-evident bug class we can re-verify with `leek fight get <id> --spatial`.

## Headline findings

1. **Every WHIP cast in 1v1 is a no-op.** Our v15 AI wastes ~4 TP/turn on `useChip(CHIP_WHIP, me)` — the chip has `targets=22` (ally-only) so in 1v1 it produces no `ADD_CHIP_EFFECT` (code 302), no damage, no heal. See `NO_OP_CAST` and `SELF_CAST_ALLY` counts.

2. **TP underutilization is the dominant failure mode.** When we're out of weapon range in early turns, the AI falls back to the no-op WHIP and ends turn with 9-10 TP unspent. Combined cost across 20 fights: **hundreds of TP evaporated before we ever engage**.

3. **The scanner itself corrected an observability bug mid-flight.** `END_TURN [8, eid, tp, mp]` carries the entity's MAX TP/MP — not spent. `fight_spatial.py` was previously labelling this as "TP spent"; now displays `TP 5/14` with `⚠ unspent: 9 TP` where applicable.

## Anomaly counts by kind

| Kind | Count | What it means |
|------|-------|----------------|
| **TP_UNDERUTILIZED** | 87 | Our turn left ≥6 TP on the table (OOR / TP-starved) |
| **NO_OP_CAST** | 73 | USE_CHIP produced no effect/damage/heal — wasted TP |
| **IDLE_TURN** | 20 | Our turn spent ≥5 TP with ZERO effect events — pure waste |
| **SELF_CAST_ALLY** | 19 | Ally-only chip cast on self in 1v1 — always no-op |

## Chip-level breakdown (for chip-origin anomalies)

- `whip` — 92 anomaly events

## Fight-level breakdown (top offenders)

- fight `52125134` — 22 anomalies
- fight `52193139` — 17 anomalies
- fight `52193096` — 15 anomalies
- fight `52192224` — 15 anomalies
- fight `52118457` — 14 anomalies
- fight `52194779` — 11 anomalies
- fight `52192216` — 11 anomalies
- fight `52130300` — 11 anomalies
- fight `52193123` — 9 anomalies
- fight `52194776` — 8 anomalies

## Sample evidence

### NO_OP_CAST

- fight `52194779` · whip cast @ cell 598 produced no effect/damage/heal
- fight `52194779` · whip cast @ cell 600 produced no effect/damage/heal
- fight `52194779` · whip cast @ cell 600 produced no effect/damage/heal

### IDLE_TURN

- fight `52194779` · Our turn spent 5 TP with ZERO effect events (no damage, no heal, no buff)
- fight `52194776` · Our turn spent 5 TP with ZERO effect events (no damage, no heal, no buff)
- fight `52194770` · Our turn spent 5 TP with ZERO effect events (no damage, no heal, no buff)

### TP_UNDERUTILIZED

- fight `52194779` · Our turn used only 5/14 TP — 9 TP wasted (probably OOR / starved)
- fight `52194779` · Our turn used only 4/14 TP — 10 TP wasted (probably OOR / starved)
- fight `52194779` · Our turn used only 4/14 TP — 10 TP wasted (probably OOR / starved)

### SELF_CAST_ALLY

- fight `52125134` · whip (targets=22, ally-only) cast on self @ cell 118
- fight `52125134` · whip (targets=22, ally-only) cast on self @ cell 116
- fight `52125134` · whip (targets=22, ally-only) cast on self @ cell 116
