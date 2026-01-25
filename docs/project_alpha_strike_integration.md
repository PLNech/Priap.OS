# Project Alpha Strike → Priap.OS Integration Notes

This document distills the two Alpha Strike notebooks into actionable guidance for Priap.OS. It is organized so we can later port the highest‑value findings into code, models, and AI heuristics.

## Part I — Elite Meta Blueprint (Build-Level Insights)

- **Action Economy Synergies**
  - `Frequency × Effective HP`: rush defensive buffs before first hit; reinforces first-move builds (see `fight_analyzer.analyze_first_strike` for hook).
  - `Agility × Savant Bulb` and `Total Life × Agility`: favor “spiky tanks” that punish attackers through return damage (tie into build planner + chip loader).
  - `Adrenaline × Effective HP`: extra TP loops require deep HP to survive to proc; note for stamina scripts in `auto_daily_fights`.
  - `Life × Stat Investment`: min-max all points; indicates need for tooling to audit our stat CV vs top builds.
- **Hybrid Dominance (`stat_cv`)**
  - Top 10 leeks maintain low primary-stat variance; we should codify CV checks when evaluating stats dumps.
  - Formula observed: `stat_cv = stat_std / mean(primary_stats)` (see Notebook Part I, Feature Engineering cell).
- **Mobility Threshold**
  - `mobility_ratio = MP / (total_life / 1000)`; elites cluster tightly, so falling short caps rank.
  - Suggest adding this metric to CLI `leek info` to flag when MP is below elite envelope.
- **Punishment over Pure Defense**
  - Savant Bulb + Agility indicates damage-return setups. We currently log chips but not synergy; need analyzer hooks to tag “return-damage ready” opponents.
- **Best-in-Slot Equipment**
  - Chips: Liberation, Savant Bulb, Adrenaline (+ Power Supply interactions).
  - Weapons: Gazor, Lightninger, B-Laser, Flame Thrower (with Teleport reposition).
  - Components: Motherboard 2/3, Power Supply.
  - Store as enums/constants to cross-check our inventory (ties to `cli/items_loader.py` and future buy list ranking).

## Part II — Tactical Frontier (Execution Insights)

- **4 Pillars**
  1. `top_20_count` → Action Quality. Winners maintain higher counts of a curated move list (`adrenaline`, `knowledge`, `armoring`, `wall`, `lightninger`, `Summon`, `steroid`, `jump`, `protein`, `serum`, `armor`, `heavy_sword`, `enhanced_lightninger`, `vaccine`, `remission`, `mutation`, `thorn`, `lightning`, `neutrino`, `shield`).
  2. `high_win_chips` delta (brainwashing, punishment, ball_and_chain, soporific, fracture) — binary gatekeeper.
  3. `tp_efficiency` — mid/late phase winners keep ≥0.9 ratio of TP spent vs available.
  4. `poison_delta` — attrition lead via arsenic/plague/covid/toxin/venom.
- **Opening Buff Gatekeeper**
  - Need 5/5 of `[knowledge, adrenaline, elevation, armoring, steroid]` by Turn 0; anything less mirrors “no setup”.
  - Derived classifiers `opening_buffs_0_2`, `opening_buffs_3_4`, `opening_buffs_5`, and opponent delta `opening_buffs_5_diff`.
- **Point of No Return (PONR)**
  - Matches reach 80% certainty by Turn 2.7. Analyzer should highlight pre-3 turn swing (e.g., mark in `fight_analyzer` summary).
- **Volatility Suppression**
  - Winners use Soporific/Tranquilizer to smooth probability curve; log when we/they cast these to detect control scripts.
- **State-Based Decision Rules**
  - Dominance logic: if `high_win_chip_diff > 0`, switch to attrition/defense.
  - Recovery logic: if predicted win prob < 0.4, introduce variance (heavy weapons, teleport combos).
  - TP Rule: if `tp_efficiency < 0.9`, deepen move search depth.

## Integration Hooks

1. **Fight Parsing**
   - Extend `fight_parser.py` to tag each action with chip/weapon IDs, TP/MP deltas, and phase bins. This unlocks opening buff tracking, high-win chip counters, TP efficiency, poison deltas, and top-20 move counts directly from parsed fights.
   - Persist the new fields in fight summaries so downstream tools don’t recompute per replay.
2. **Analyzer Upgrades**
   - Add an Alpha-Strike section to `fight_analyzer.py` (surfaced via `leek fight analyze --alpha-strike`) that reports:
     - Opening buff completion % and opponent delta.
     - TP efficiency per phase (target ≥0.9 mid/late).
     - High-win chip/weapon usage gaps and `top_20_count`.
     - Poison delta trend and volatility (soporific/tranquilizer usage).
     - Point-of-No-Return turn estimate (highlight when fights are decided before Turn 3).
3. **Data Persistence & Logging**
   - Update scraper DB schemas to store the metrics, enabling cohort studies without replay parsing.
   - `auto_daily_fights.py` should log archetype + Alpha-Strike KPIs per fight for daily review.
4. **Build & CLI Tooling**
   - `leek info`/`build` commands: display stat CV, mobility ratio, and warn when we fall outside elite thresholds.
   - Add inventory gap checks for Liberation, Savant Bulb, Adrenaline, Gazor, Lightninger, Motherboard 2/3, Power Supply.
5. **AI Heuristic Roadmap**
   - Implement an opening validator that refuses to engage until the 5-buff gatekeeper list is completed.
   - Introduce Dominance/Attrition/Recovery state transitions based on high-win chip deltas and TP efficiency once the metrics are available at runtime.

### Metric Priorities vs. Late-Game Gating

- **Core/Early Needs**
  - Opening buff completion + opponent delta (available now, no gear dependency).
  - TP efficiency tracking (per-phase) to detect wasted TP early.
  - Stat CV + mobility ratio reporting for build tuning.
  - High-win chip/weapon usage logging for opponents (even if we don’t own them yet).
- **Late-Game / Gear-Dependent**
  - `top_20_count` for our own AI (requires access to most of the curated move list).
  - High-win chip/weapon deltas for self-audit (needs chips like Savant Bulb, Liberation, Gazor/Lightninger).
  - Poison delta & volatility suppression as core strategies (granted by arsenic/plague/covid/toxin/venom and control chips).
  - State machine logic (Dominance vs Recovery) that assumes runtime availability of high-impact chips/weapons.

## Next Steps

1. Implement fight-parser plumbing for opening buffs, TP usage, and chip/weapon tagging.
2. Wire chip/weapon taxonomies into shared constants for parser, analyzer, and AI.
3. Backfill historical fights with the new metrics to validate claims against our dataset.
4. Once validated, expose analyzer reports + logging, then phase in LeekScript logic (TP efficiency gates, dominance switches).
