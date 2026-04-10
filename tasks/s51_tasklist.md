# Priap.OS Task List — S51 Snapshot (2026-04-10)

> Exported for cross-laptop session continuity. Full descriptions from task system.
> Taxonomy: #0001 North Star | #01xx Infra | #02xx AI | #03xx Data | #04xx Game | #05xx Ops

---

## 🏆 #0001: Reach Top 10 Leaderboard (NORTH STAR)

Currently rank #8404 at T368. Top 10 = ~T2000+. Every task below feeds this goal.
Pillars: AI quality > Equipment > Level > Stats.

---

## In Progress (3)

### 🧠 #0219: Design and deploy AI v15 "Phalanx II"
**Status**: in_progress | **Blocked by**: #0217, #0211
v14_flat deployed with Whip + RES 219. S51 tournament: draws eliminated, v14 rose #5->#3. **New bottleneck**: losses to cktang88 family (ck_pistol1 0-10, ck_venom_sg 1-9, ck_flamethrower 2-8, ck_magnum1 1-9). **v15 plan needs pivot from anti-draw to anti-cktang88.**

### 🧠 #0217: Anti-kiter AI strategy for v15
**Status**: in_progress | **Blocks**: #0219
Kiter matchup is 25% WR — worst archetype. Steps: (1) get 5-10 kiter loss replays, (2) analyze chase patterns — out of MP? timeout? (3) audit kiter detection in v14_flat, (4) counter-strategies: aggressive MP, early Tranq, b_laser range 8, forfeit-if-hopeless. (5) A/B test in PySim. **Completion**: kiter WR improvement demonstrated in sim.

### 🔧 #0132: PySim Fidelity Audit
**Status**: in_progress | **Blocks**: #0310
Systematic PySim vs real game comparison. S50: 5 bugs fixed via replay. S51: equipment restriction + 6.3x speedup. **Remaining gaps**: AOE falloff (always 1.0), push/attract distance (fixed 3 cells). **Success**: ±10% damage, same winner 8/10 test fights.

---

## Pending — 🧠 AI Strategy (7)

### 🧠 #0204: Validate AI debug logging works online
Confirm debug() output is visible in online fight logs. Essential for diagnosing AI behavior in production fights.

### 🧠 #0208: AI strategy optimization & simplification
v14 is 873 lines. Simplify strategy selection, remove dead code paths, streamline decision tree. Simpler = fewer bugs = higher WR.

### 🧠 #0211: Validate adaptive counter-strategy viability
Test whether dynamically switching strategy mid-fight (detect archetype -> counter) improves WR vs static aggro. Requires archetype detection in LeekScript.

### 🧠 #0214: Leverage getEffects() to skip redundant shields
Use getEffects(getEntity()) to detect active buffs before re-applying shields. Save TP for attacks when shields haven't expired. Also use getEffects(enemy) for Tranq timing optimization.

### 🧠 #0221: Realistic archetype bots — kiter, healer, aggro
**Blocked by**: #0127
Rewrite archetype_kiter.leek (Spark+Flash+Cure+Shield, WIS 100+), archetype_tank -> healer, archetype_rusher -> aggro. Use getChips()/getChipName() for dynamic discovery.

### 🧠 #0222: Investigate v14 AI 18x18 grid model on diamond grid
v14 uses cellFromXY/cellX/cellY with cell % 18 and cell // 18 — WRONG on real diamond grid (stride 35, 613 cells). Yet 48% WR online. Is BFS just lucky? Could fixing this improve WR?

### 🧠 #0207: Study tagadai RL/NN modules for AI training
tagadai codebase has RL and neural net training modules. Explore feasibility of RL-trained AI instead of hand-coded strategies.

---

## Pending — 🔧 Infrastructure (11)

### 🔧 #0103: CI/CD — validate AI syntax before deploy
Add LeekScript compilation check to CI pipeline. Use leekscript.jar (Java 21) in GH Actions. Prevent deploying AIs with syntax errors.

### 🔧 #0105: API completeness audit vs frontend
Audit all LeekWars frontend API calls vs our api.py coverage. Identify missing endpoints that unlock new features or data.

### 🔧 #0106: Test coverage for core library
Improve pytest coverage for fight_parser.py, fight_analyzer.py, simulator.py, api.py. Target: every fix gets a regression test.

### 🔧 #0107: Documentation audit — update stale docs
Review docs/ for outdated info. THESIS.md, GROUND_TRUTH.md, research files. Ensure consistency with current state.

### 🔧 #0110: Implement tournament registration in api.py
Add tournament registration/status API endpoints. Currently manual. Should be automated via CLI.

### 🔧 #0116: LeekScript step debugger
Build tooling to step through LeekScript execution. Currently debug() print statements only. Would dramatically speed up AI development.

### 🔧 #0119: Simulator debugging & introspection
Improve simulator observability: per-turn state dumps, action traces, resource tracking. Currently a black box.

### 🔧 #0123: Fix simulator map seeding for determinism
Spawn positions vary between runs. Need deterministic seeding for reproducible A/B tests.

### 🔧 #0124: Fix daemon crash reporting bug
S39: daemon log showed "5 crashes" but API confirms 5W-1L. Fight-result parsing fails silently, miscounts results. False crash positives.

### 🔧 #0125: Fix CLI `leek fight history` Pydantic validation error
Crashes on older fights that store leek IDs as ints instead of dicts. FightHistoryEntry model needs both formats.

### 🔧 #0127: Sim observability — verbose output, debug logs, real maps
**Blocks**: #0221
Add logs to FightOutcome, --verbose flag in compare_ais.py, --export JSON, switch to MapLibrary (167 real maps), render_turn_by_turn().

### 🔧 #0128: Fix validate_archetypes.py + stale descriptions
Two bugs: _run_fight_direct -> run_scenario, undefined archetype_names -> ARCHETYPES dict. Fix "L73 build" stale descriptions.

### 🔧 #0098: PySim performance — PyPy compat, AST caching, slot variables
**Partially addressed S51** (6.3x speedup via pickle cache, O(1) lookups, walkable neighbors). Remaining: (1) PyPy compatibility for 3-5x more, (2) AST caching per .leek file, (3) slot variables replacing dict-based Environment. Current: ~21.5 fights/sec. Target: 50+.

---

## Pending — 📊 Data & Analysis (5)

### 📊 #0304: Fight replay viewer validation
Validate fight parser output against web replay viewer. Ensure correct interpretation of positions, damage, buffs.

### 📊 #0306: Track passive income XP sources
Understand/optimize XP from non-fight sources: gardens, tournaments, daily bonuses. Feed into leveling projections.

### 📊 #0308: Scout nemesis opponents for build intelligence
S39 audit: 6 nemesis opponents with 0W-3L each (ArrnArchi, TerenceMyleek, GeekOfSmourad, ElCarotte, Spounleek, aarya). Run `leek scout batch`, analyze builds, find patterns, write to `docs/research/nemesis_builds_s39.md`.

### 📊 #0310: PySim vs real game fidelity — replay comparison
**Blocked by**: #0132
Pick 5-10 real fights with known builds. Replay in PySim. Compare damage/turn, duration, winner. Quantify fidelity gap. Validates whether PySim ELO is predictive.

### 📊 #0318: Study top-10 rank climbers for build/AI insights
Scout top-ranked leeks. Analyze build patterns, chip loadouts, weapon choices. Identify meta shifts. Use `leek scout batch`.

---

## Pending — 🎮 Game Mechanics (4)

### 🎮 #0403: Research optimal build allocation by level
Model optimal stat allocation at each level bracket. Factor in diminishing returns, capital costs, meta (RES matters). Guide capital spending.

### 🎮 #0405: Understand level-up XP curve
Map XP requirements per level. Calculate fights-to-level, optimal XP/day, time-to-target-level projections.

### 🎮 #0406: Core/Memory upgrades for ops budget
Invest in CPU cores and RAM for higher ops/turn and chip slots. Currently hitting ops limits in complex AI. Evaluate ROI vs stat investment.

### 🎮 #0409: Buy Drip chip (28,080 Habs)
32 heal, CD 1, 2 uses, 2 TP. Strictly better than Bandage. ~93K habs available. Quick win.

---

## Pending — ⚙️ Operations (4)

### ⚙️ #0504: Operational dashboard / monitoring
Dashboard: daily WR, talent trend, rank history, fight budget usage, equipment fund progress. Currently manual checks.

### ⚙️ #0505: Tournament participation automation
Auto-register for tournaments via API + CI. Currently manual. Tournaments give XP + habs + ranking exposure.

### ⚙️ #0506: Fight cooldown/budget management
Smarter fight scheduling: spread fights across day for optimal talent gain. Track cooldown timers. Avoid burst-then-idle.

### ⚙️ #0509: Battle Royale WebSocket automation
br_daemon.py exists but needs reliability. Auto-join BR events for bonus XP/habs. Currently systemd service.

---

## Pending — 🎨 Showcase (1)

### 🎨 #0121: Build project showcase SPA
Astro + GitHub Pages at plnech.github.io/Priap.OS. Greco-Futurism design (CHARTE_GRAPHIQUE.md). Rankings, fight stats, AI evolution story.

---

## Completed — S51

| Task | Description |
|------|-------------|
| #0131 | Fix PySim moveToward — entities must not occupy same cell |
| #0133 | PySim introspection — snapshot, step, inject, replay, compare |
| #0134 | PySim equipment fidelity — restrict to actual loadout in replay mode |
| — | PySim engine optimization pass (6.3x speedup) |
| — | Rerun 24-AI PySim tournament with S50+S51 fixes |
| — | Analyze tournament results and ranking changes |

---

## Recommended Next Actions
1. **v15 pivot** (#0219): Analyze why cktang88 AIs dominate v14. H2H matrix in `docs/research/pysim_elo_tournament.md`.
2. **Anti-kiter** (#0217): Fight replay analysis for kiter losses (25% WR).
3. **Buy Drip** (#0409): 28K habs, strict upgrade over Bandage. Quick win.
4. **PySim fidelity** (#0132): AOE falloff + push/attract remaining gaps.
5. **Nemesis scouting** (#0308): Intelligence on our 6 worst matchups.
