# Priap.OS Strategic Plan (living doc, revised 2026-04-18)

> Replaces `tasks/s51_tasklist.md` (kept as historical snapshot).
> North Star: 🏆 **#0001 — Reach top 10 leaderboard.**
> This plan exists to answer: *what sequence of work gets us there, and how do we know it's working?*

---

## The honest state

**Where we are** (verified from `rankings.db` + `fights_meta.db`, 2026-04-18):
- IAdonis: **L151, T~341, rank ~8993** — we've leveled L117→L151 in ~28 days (≈1.2 levels/day)
- Historical WR: **47.8%** across 1420 observed fights (stable across S37/S39/now)
- Rank trajectory: oscillating 7610–9398 for 28 days — **not climbing**
- Top 10 threshold today: **T3381, L301+**. Top 1000: T1733, L301+.

**What the numbers mean:**
- **Level is climbing fast** (P1 pillar is working — grinding is real)
- **Talent is flat** — 48% WR in-bracket means we neither gain nor lose talent meaningfully
- **Rank is flat** — talent drives rank; flat talent → flat rank
- **All top-1000 leeks are L301+** — level gates endgame chips/weapons. This is a structural ceiling, not a soft constraint.

## The methodology pivot

Sessions S41–S51 poured effort into PySim fidelity. The tournament reshuffle caused by a single `dist==0` fix (ck_pistol1: 40-0 → 0-10) and the **22-point gap between PySim WR (70%) and online WR (48%)** suggest we've been tuning against an unvalidated oracle.

**New first principle**: every flywheel iteration must pass through measurement. PySim ELO is a hypothesis about reality, not reality itself.

### Priority tiers

| Tier | Purpose | Gate to next tier |
|------|---------|-------------------|
| **P0 — Measurement** | Validate what we trust | Must complete before P2 |
| **P1 — Level & equipment** | Attack the binding constraint | Runs in parallel with P0/P2 |
| **P2 — AI iteration** | Only after P0 says the flywheel works | Blocked by P0 correlation study |
| **P3 — Operational discipline** | Fix self-inflicted leaks (tournament drain, scraper gaps) | Always-on hygiene |

---

## P0 — Measurement (unblocks everything)

| # | Task | Purpose |
|---|------|---------|
| **NEW** | PySim↔Online correlation study | 5 AIs × 50 online fights. Spearman ρ vs PySim ELO. ρ<0.5 ⇒ flywheel broken, v15 deferred. |
| **NEW** | Trajectory model | This session. Read rankings.db + fights_meta.db, project fights-to-T1733 at current pace, WR-sensitivity scenarios. Writes `docs/research/trajectory_s52.md`. |
| **NEW** | Scraper staleness fix | `leek_observations` stops at 2026-03-01 — re-scrape our last 40 days. Prerequisite for any recent-WR claim. |
| #0306 | Track passive income XP | How much XP comes from non-fights? Feeds trajectory model. |
| #0405 | Understand level-up XP curve | Calibrates "1.2 levels/day" projection into months-to-L301. |

## P1 — Level & equipment (binding-constraint attack)

At L146, we literally cannot run Awakening (L200), Arsenic (L285), Carapace (L141 — just unlocked).

| # | Task | Leverage |
|---|------|----------|
| #0403 | Research optimal build allocation by level | Stops us guessing where Capital goes |
| #0406 | Core/Memory upgrades for ops budget | Ops limit is a silent AI cap |
| #0409 | Buy Drip chip (28K habs) | Only if bracket data shows heals matter — **re-evaluate post-trajectory** |

## P2 — AI iteration (gated on P0 validation)

| # | Task | Status |
|---|------|--------|
| #0219 | v15 "Phalanx II" | **DEFERRED** pending PySim↔online correlation. No online deploy until P0 #1 clears. |
| #0217 | Anti-kiter strategy | Continue — kiter 25% WR is a real online signal, not PySim-dependent |
| #0214 | getEffects() shield optimization | Low-risk efficiency fix, online-verifiable |
| #0211 | Adaptive counter-strategy viability | Blocked by #0127 (sim observability) |
| #0208 | AI simplification | Polish, deprioritized |
| #0221 | Realistic archetype bots | Deprioritized — PySim opponents shouldn't drive our design |
| #0222 | 18×18 grid correctness | Curiosity — 48% online WR says BFS is fine as-is |
| #0207 | tagadai RL/NN exploration | Research-only |
| #0204 | Validate AI debug logging online | Small task, pair with any online deploy |

## P3 — Operational discipline

| # | Task | Why |
|---|------|-----|
| **INVERT #0505** | Do **not** auto-enter tournaments. S39: 0W-14L = ~70 talent lost. Explicit opt-in only. |
| #0506 | Fight cooldown/budget management | Spread 50 fights/day evenly for max talent |
| #0509 | Battle Royale WebSocket automation | Free XP/habs if reliable |
| #0504 | Operational dashboard | Builds on P0 measurement work |

## Infrastructure (selective, blocked or supporting)

| # | Task | Status |
|---|------|--------|
| #0103 | CI LeekScript syntax check | Good hygiene, cheap |
| #0106 | Test coverage — core library | Pair with every fix |
| #0124 | Daemon crash reporting | Fix when scraper work overlaps |
| #0125 | `leek fight history` Pydantic | Quick win, pair with CLI polish |
| #0127 | Sim observability | Blocks #0211, #0221 — do if P2 thaws |
| #0128 | Fix `validate_archetypes.py` | Small |
| #0132 | PySim fidelity audit | **in_progress** — finish AOE falloff + push/attract then close |
| #0098 | PySim performance (PyPy, AST cache) | Deprioritized — fast enough |
| #0105, #0107, #0110, #0116, #0119, #0123 | Deprioritized |

## Data & analysis

| # | Task | Status |
|---|------|--------|
| #0304 | Fight replay viewer validation | Pair with #0132 |
| #0308 | Scout nemesis opponents | Cheap intel, do with any online work |
| #0310 | PySim vs real game fidelity replay | Blocked by #0132 |
| #0318 | Study top-10 rank climbers | Research, informs P1 |

## Game mechanics & showcase

| # | Task | Status |
|---|------|--------|
| #0403, #0405, #0406, #0409 | See P1 |
| #0121 | Showcase SPA | Deprioritized until we have something to showcase |

---

## Immediate next action (this session)

1. ✅ Fix `leek_ranks` talent/level zero-bug in `ranking_tracker.py` + backfill historical rows
2. 🔄 Build trajectory model (`leek trajectory` CLI + library)
3. 🔄 Run model, write `docs/research/trajectory_s52.md`
4. 🔄 Based on findings, decide P1 emphasis (level roadmap) vs P2 thaw criteria

## Success criteria for this strategic pivot

- A quantitative answer to: "At current pace, how many days / fights until top-1000?"
- A quantitative answer to: "Does PySim ELO predict online WR?" (P0 #1, subsequent session)
- No v15 online deployment until P0 #1 passes
- A level-first capital-allocation plan driven by P1 data, not intuition

---

## Verdict from trajectory model (2026-04-18)

Full report: [`docs/research/trajectory_s52.md`](../docs/research/trajectory_s52.md).

**What we learned:**
- **Level velocity is healthy** (~1.2 L/day). L301 (top-1000 ceiling) is **~127 days / 4.2 months** away.
- **Talent is flat at 48% WR** (+0.24/day over 30d). Matchmaking keeps us at bracket average as we level.
- **Recent 7-day window shows regression**: −2.59 talent/day, +57 rank/day. Either matchmaking caught up to our L146→L151 jump, or something regressed. Can't diagnose yet — fights DB is 39 days stale.
- **WR is the high-leverage lever**: 48→55% WR compresses top-10 ETA from years to ~3.4 months. 55→60% halves it again.
- **Level and WR are co-equal**: both pillars arrive at the north star on ~4-month timescales. They compound.

**Revised strategy:**
1. **Both pillars matter.** Earlier "level is the binding constraint" framing was incomplete. The math says we need ~L301 *and* ~55% WR together.
2. **AI iteration is back in play — but still gated on P0 #1.** A 5–7 point WR improvement is worth months. But we need evidence PySim ELO correlates with online WR before we ship v15.
3. **Fix the data pipeline first.** We can't trust WR claims while `fights_meta.db` is 39 days stale. The scraper fix (#119) becomes P0.
4. **Revisit in ~2 weeks** with fresh data to confirm velocities.

**Immediate next actions (in priority order):**
1. Fix fights_meta.db staleness (task #119) — re-scrape our recent fights
2. Design PySim↔online correlation study (task #120)
3. Parallel: P1 level work — continue grinding; #0403 build allocation research
4. When #119 + #120 complete: decide v15 thaw or level-grind dominance

> *"Pay attention to what is important, not just what is quantifiable."* — Donella Meadows
