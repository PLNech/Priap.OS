# Top-N Reference Class (NEW-A)

> Generated 2026-04-18T22:55:37.257004 from rankings.db + fights_meta.db
> Pure local-data analysis — no scrape calls.

## Top 10 individual breakdown

| Rank | Leek | Farmer | Talent | L | STR | AGI | WIS | RES | MAG | SCI | HP | TP | MP | Archetype |
|-----:|:-----|:-------|------:|--:|----:|----:|----:|----:|----:|----:|---:|---:|---:|:----------|
| 1 | twogether | tagadalone | T3620 | 301 | — | — | — | — | — | — | — | — | — | *no data* |
| 2 | hardleeker | tagadanar | T3563 | 301 | 400 | 200 | 300 | 400 | 0 | 0 | 1940 | 20 | 6 | str-heavy |
| 3 | Claudios | tagadai | T3548 | 301 | 540 | 90 | 390 | 200 | 0 | 100 | 2087 | 28 | 6 | str-heavy |
| 4 | Peuhwaro | fujiwar | T3505 | 301 | 600 | 340 | 500 | 100 | 0 | 90 | 3130 | 28 | 8 | str-heavy |
| 5 | GeneralMamene | SachaBougPalette | T3490 | 301 | 50 | 320 | 460 | 50 | 642 | 130 | 2580 | 25 | 6 | mag-heavy |
| 6 | Peuwareau | fujiwar | T3485 | 301 | 600 | 340 | 500 | 100 | 0 | 90 | 3130 | 28 | 8 | str-heavy |
| 7 | LéodaganDeCarmélide | ArthourCuillere | T3458 | 301 | — | — | — | — | — | — | — | — | — | *no data* |
| 8 | Claudius | tagadai | T3443 | 301 | 540 | 90 | 390 | 200 | 0 | 100 | 2087 | 28 | 6 | str-heavy |
| 9 | Kraneur | Kraspen | T3439 | 301 | 0 | 300 | 500 | 40 | 600 | 90 | 3465 | 27 | 7 | mag-heavy |
| 10 | LégumesTrésBon | Legumatore | T3381 | 301 | 50 | 400 | 400 | 50 | 830 | 100 | 2280 | 26 | 5 | mag-heavy |

**Top-10 archetype census**:
- `str-heavy` — 5 leeks
- `mag-heavy` — 3 leeks

## Universal traits (top-10)

> A stat with low zero-rate across top-10 is an *entry ticket*. A stat with high zero-rate is *optional*.

| Stat | mean | median | p25–p75 | zero-rate |
|:-----|-----:|-------:|:--------|:----------|
| STRENGTH | 348 | 470 | 50–600 | 12% | 🎟️
| AGILITY | 260 | 310 | 200–340 | 0% | 🎟️
| WISDOM | 430 | 430 | 390–500 | 0% | 🎟️
| RESISTANCE | 142 | 100 | 50–200 | 0% |
| MAGIC | 259 | 0 | 0–642 | 62% |
| SCIENCE | 88 | 95 | 90–100 | 12% |
| LIFE | 2587 | 2430 | 2087–3130 | 0% | 🎟️
| TP | 26 | 28 | 26–28 | 0% |
| MP | 6 | 6 | 6–8 | 0% |

> 🎟️ = universal (low zero-rate + meaningful median). These stats likely gate admission to top-10.

## Broader bracket aggregates

| Cohort | n | STR | AGI | WIS | RES | MAG | SCI | HP | TP | MP |
|:-------|--:|----:|----:|----:|----:|----:|----:|---:|---:|---:|
| top-10 (observed) | 8 | 470 | 310 | 430 | 100 | 0 | 95 | 2430 | 28 | 6 |
| top-100 (observed) | 92 | 505 | 275 | 480 | 110 | 50 | 100 | 2950 | 27 | 6 |
| L301 bracket | 949 | 410 | 206 | 400 | 205 | 50 | 90 | 2560 | 24 | 6 |

## Top-10 weapon / chip usage (from scraped fight replays)

> Template IDs (not names). Cross-reference `leekwars_agent.models.equipment.CHIP_REGISTRY` / `WEAPON_REGISTRY` for names.
> Empty means our fight parser didn't capture this leek's equipment usage.

- **Claudios** (rank #3): weapons [29×3, 33×3, 25×2, 23×2, 36×2] | chips [17×3, 18×3, 20×3, 23×3, 24×3, 25×3, 26×3, 30×3]
- **Peuhwaro** (rank #4): weapons [25×4, 23×4, 36×1] | chips [24×7, 25×7, 26×7, 29×7, 32×7, 33×7, 35×7, 28×6]
- **GeneralMamene** (rank #5): weapons [10×1, 21×1, 23×1, 27×1, 36×1] | chips [4×2, 28×2, 33×2, 34×2, 35×2, 37×2, 56×2, 62×2]
- **Peuwareau** (rank #6): weapons [25×24, 23×20, 19×15, 27×4, 33×4] | chips [24×25, 25×25, 34×25, 38×25, 81×25, 94×25, 104×25, 36×24]
- **LéodaganDeCarmélide** (rank #7): weapons [4×1] | chips [12×1]
- **Claudius** (rank #8): weapons [25×30, 33×29, 40×29, 29×25, 23×21] | chips [38×30, 70×30, 94×30, 11×29, 18×29, 20×29, 22×29, 23×29]
- **Kraneur** (rank #9): weapons [8×8, 10×7, 35×7, 20×2] | chips [34×10, 81×10, 38×9, 70×9, 80×9, 94×9, 36×8, 61×8]
- **LégumesTrésBon** (rank #10): weapons [35×2, 14×1] | chips [33×2, 34×2, 38×2, 47×2, 55×2, 56×2, 57×2, 58×2]

## Data caveats

- Top-10 stats come from the MAX observed value per stat column. If our scrapes are old, the stats may be lower than current state.
- `weapons_used` / `chips_used` coverage is ~52% / 60% across all observations — fight parser gaps mean some leeks appear equipment-blank.
- Archetype labels are heuristic (max-stat signature); actual playstyle may differ.
