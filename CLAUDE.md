# Priap.OS - LeekWars AI Agent

> **Claude**: At session start, Read `docs/THESIS.md` (strategic north star). `MEMORY.md` auto-loads.
> Update THESIS.md as data proves/disproves hypotheses. Update memory files for verified patterns.
> Task system (#0001-#0500) is the source of truth for all planning — not this file.

## Document Architecture

| Document | Role | Update When |
|----------|------|-------------|
| **`docs/THESIS.md`** | Strategy: build philosophy, chip priorities, AI behavior, competitive landscape | Every session as data flows |
| **`MEMORY.md`** *(auto-loaded)* | State + verified patterns: API quirks, peer data, architecture conventions | Patterns confirmed across sessions |
| **`docs/GROUND_TRUTH.md`** | Equipment stats, TP costs, chip/weapon data from submodules | Submodule updates |
| **`CLAUDE.md`** *(this)* | Stable conventions, safety protocols, tooling reference | Rarely |
| **`docs/research/*.md`** | Analysis outputs (17+ files). Research compounds. **NEVER LOSE.** | After each analysis |
| **`THOUGHTS.md`** | Historical session log (S8-S23). Archived — **not boot-time reading.** | Retired |

## Task Taxonomy

Source of truth: Claude Code task system. Archive completed to `tasks/sessionN_archive.json`.

| Range | Pillar |
|-------|--------|
| #0001 | 🏆 North Star: Top 10 Leaderboard |
| #0100 | 🔧 Infrastructure: Tooling, flywheel, simulation |
| #0200 | 🧠 AI Strategy: Combat logic, archetypes |
| #0300 | 📊 Data & Analysis: Fight parsing, pattern detection |
| #0400 | 🎮 Game Mechanics: Build, chips, stats, equipment |
| #0500 | ⚙️ Operations: Daily fights, automation |

Sub-tasks: #0201, #0202, etc.

## Project Overview

Automated LeekWars agent → **top 10 ladder**. Build infrastructure to iterate 13,000x faster than manual play.

- Online fights: 50/day (scarce). Offline: 1.8M/day potential (21.5 fights/sec).
- **Principle**: Never test online what we can test offline. Online = data collection only.

### The Flywheel
```
Fight Online → Collect Data → Analyze Losses → Improve AI Offline
     ↑                                                    ↓
     └──────────── Deploy Best Variant ←──────────────────┘
```

---

## Safety Rules

### Online Fight Protocol (MANDATORY)

> ⛔ Before running ANY online fight or workflow, **ASK THE USER FIRST**.

| Action | Permission? |
|--------|-------------|
| `gh workflow run daily-fights.yml` | ✅ ASK FIRST |
| `leek fight run -n N` | ✅ ASK FIRST |
| `auto_daily_fights.py` | ✅ ASK FIRST |
| Offline simulation (`compare_ais.py`) | ❌ Run freely |
| Test scenario API (`leek test run`) | ❌ Unlimited |

### Post-Fight Verification (MANDATORY)

After EVERY online fight batch, verify logs before declaring success:
```bash
leek fight get <fight_id> --log 2>/dev/null | grep -i "error\|incompatible\|failed"
```
No AI is "deployed successfully" until one fight's logs show no runtime errors.

### Grounding Protocol

> You have hallucinated game values before. ALWAYS verify from ground truth.

**Priority**: Equipment Registry > Submodules > API exports > Our code

| Data | Source |
|------|--------|
| Chip/Weapon IDs, templates, stats | `from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY` |
| Raw chip/weapon TS definitions | `tools/leek-wars/src/model/{chips,weapons}.ts` |
| Constants | `tools/leek-wars-generator/.../FightConstants.java` |
| Our equipment | `docs/GROUND_TRUTH.md` |

### Equipment Registry (MANDATORY)
**NEVER hardcode chip_id↔template mappings.** Use the registry:
```python
from leekwars_agent.models.equipment import CHIP_REGISTRY, WEAPON_REGISTRY

# Decode a fight action template ID
chip = CHIP_REGISTRY.by_template(57)  # -> Chip(name='tranquilizer', id=94, ...)
weapon = WEAPON_REGISTRY.by_name("b_laser")  # -> Weapon(template=13, item=60, ...)
```
The registry parses `chips.ts`/`weapons.ts` at import time. It is the single source of truth.
If you see a hardcoded dict like `{10: 'Flame', 20: 'Tranquilizer'}` — **that's a bug**. Use the registry.

**Red flags**: "costs about X TP", "I think the range is...", math doesn't add up → STOP, look it up.
**Hidden costs**: `setWeapon()` = 1 TP, `say()` = 1 TP. Use `debug()` instead (free).

---

## Development Conventions

### CLI-First (MANDATORY)
Never raw API calls in scripts. Always: `api.py` method → CLI command → use CLI.
**Ad-hoc Python scripts are a smell.** Once is exploration, twice means it should be a CLI command. If you're writing `poetry run python3 -c "..."` to do something, ask: should this be `leek <command>`?

### API Discovery (MANDATORY)
Never guess endpoints. Verify from frontend source:
```bash
grep -rn "LeekWars.post.*endpoint" tools/leek-wars/src
```
Document source location in api.py docstrings.

### Feature Development Checklist
1. Check frontend source for correct endpoint
2. Probe/test the endpoint
3. Document in `docs/research/` or relevant docs
4. Implement in `api.py` with error handling (cite source)
5. Expose via `leek` CLI
6. Add regression test
7. Git commit

### Testing: "Whoops = Unit Test"
- Every fix MUST have a regression test
- Run `poetry run pytest tests/ -v` after changes
- **Layers**: Synthetic data → Real data integration → ID mapping regression → Statistical sanity
- **Three-tier validation**: Local sim (fast) → Server test (unlimited, real) → Garden fights (precious)

### Git Discipline
- **Default branch is `main`** — all work happens on `main`. GH Actions daemon checks out `main`.
- Commit after each success (atomic, descriptive)
- Feature branches for new features
- Never push main without explicit request

### Research Outputs (NEVER LOSE)
All analysis → `docs/research/`. If you run analysis, write it to a file before responding.

### Data Modeling
Pydantic-first (`src/leekwars_agent/models/`). Start minimal, grow incrementally.

---

## Credentials

- Login: `leek@nech.pl`
- Account: PriapOS (Farmer ID: 124831)
- Leek 1: IAdonis (ID: 131321) — competitive climber
- Leek 2: AnansAI (ID: 132531) — theory test bed (created S35)

## Project Structure

```
src/leekwars_agent/        # Core library
  api.py                   # HTTP API client (retry/backoff)
  fight_parser.py          # Replay parser + extract_combat_stats()
  fight_analyzer.py        # Classification, pattern extraction
  simulator.py             # Local fight simulation (21.5 fights/sec)
  battle_royale.py         # WebSocket BR client
  scraper/                 # Fight scraper + SQLite DB
    scraper.py             #   BFS graph traversal
    db.py                  #   FightDB with combat stats pipeline
  models/                  # Pydantic models
  cli/                     # Click CLI (`leek` command)
scripts/                   # Automation
  auto_daily_fights.py     #   GH Actions daily runner
  compare_ais.py           #   A/B test AIs offline
  debug_fight.py           #   Single fight analysis
  br_daemon.py             #   Battle Royale systemd daemon
  sim_defaults.py          #   Single source of truth for sim config
ais/                       # LeekScript AI files
  current -> ...           #   Symlink to deployed version
  fighter_v*.leek          #   Versioned AIs (v1-v14)
  trophy_hunters/          #   Specialized trophy AIs
data/                      # Fight data, configs
  fights_meta.db           #   Canonical fight database (5,327+ fights)
docs/                      # Living documentation
  THESIS.md                #   Strategic north star
  GROUND_TRUTH.md          #   Equipment stats from submodules
  CHARTE_GRAPHIQUE.md      #   Design system (Greco-Futurism)
  research/                #   17+ analysis files
tests/                     # pytest test suite
  test_fight_parser.py     #   Extraction, entity mapping, ID regression
  test_market.py           #   Weapon ID regression
  test_simulator.py        #   Offline sim validation
systemd/                   # BR daemon service files
tasks/                     # Session archives
```

## Commands Reference

### `leek` CLI (Primary Tool)
```bash
# Status
leek info garden/leek/farmer    # Fight status, leek stats, farmer info
leek fight status               # Fights remaining + talent

# Combat
leek fight run -n 5             # Run online fights (ASK FIRST!)
leek fight history              # Recent results
leek fight get <id> --log       # Fight replay + action log

# AI Management
leek ai list/deploy/local       # AI versions, deploy, local files

# Build
leek build show/spend           # Capital management

# Analysis
leek scrape discover/run        # Fight scraping (BFS traversal)
leek analyze meta/level/stats   # Fight analytics

# Other
leek test list/run/create       # Unlimited server-side test fights
leek craft inventory/list/make  # Crafting
leek br status/join/run         # Battle Royale
leek --json <cmd>               # Machine-readable output
```

### Offline Simulation
```bash
poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000  # A/B test
poetry run python scripts/debug_fight.py v8.leek v6.leek           # Debug single
```
**Sim ≠ Online**: Useful for AI logic testing and A/B comparison, NOT win rate prediction (93% team 1 bias).

### Local Validation
```bash
# Sim validates automatically. Standalone (rarely needed):
java -jar tools/leek-wars-generator/leekscript/leekscript.jar ais/fighter_v1.leek
# Requires Java 21+ (sdk install java 21.0.5-tem)
```

---

## LeekScript Reference

### Gotchas
- `var` = block-scoped, `global` = file-scoped
- `setWeapon()` costs 1 TP — only call once per fight!
- `say()` costs 1 TP — use `debug()` instead (free)!
- LS4: `null` coerced to 0 in numeric contexts
- Type annotations are FREE (zero runtime cost)

### Syntax Requirements
- Includes: `include("module.leek")` (need `.leek` extension)
- Semicolons after bare return: `if (x) return;`
- Empty maps: `var m = [:]`
- For-each: `for (var k : var v in map)` (BOTH need `var`)

### Debugging Errors
1. Standalone compiler validates syntax but NOT fight functions (`UNKNOWN_VARIABLE_OR_FUNCTION` on getCell etc. is OK)
2. `CLOSING_PARENTHESIS_EXPECTED` → missing semicolons above
3. Fix ONE error at a time, re-test immediately

### AI Logging (CRITICAL)
Every AI MUST have comprehensive `debug()` output (FREE, no TP cost):
- Turn/phase/HP state, strategy selection (which + WHY), movement, combat execution

### Quick Reference
```leekscript
// Entity
getCell() / getCell(entity)     // Cell positions
getLife() / getLife(entity)     // HP
getMP() / getTP()               // Movement/Action points
getNearestEnemy() / getEnemies() / getAllies()

// Movement (NO moveToCell — only moveTowardCell!)
moveToward(entity) / moveToward(entity, n)
moveTowardCell(cell) / moveAwayFrom(entity) / moveAwayFromCell(cell)
getCellDistance(cell1, cell2)    // EXPENSIVE — cache it!

// Combat
setWeapon(WEAPON_PISTOL)        // Equip (costs 1 TP!)
useWeapon(entity)               // Attack
useChip(CHIP_CONSTANT, entity)  // Use chip
getWeaponCost(w) / getWeaponMinRange(w) / getWeaponMaxRange(w)

// Debug (FREE)
debug(value) / debugW(value) / debugE(value)

// Returns
USE_SUCCESS, USE_FAILED, USE_NOT_ENOUGH_TP, USE_INVALID_TARGET
```

### Operations Management
- Each leek has an ops limit per turn (upgradeable via cores)
- Error 113 = `too_much_ops` → turn ends immediately
- `getCellDistance()` expensive — cache results
- Limit loop iterations explicitly

---

## Orchestration Mode

When user says "orchestrator mode": delegate to worker agents, keep context clean.

**Files**: `AGORA.md` (worker progress), `docs/GANTT_SESSION*.md` (critical path)

**Rules**:
1. Don't grep/read — spawn `Task(subagent_type="Explore", model="haiku")`
2. Workers mark VERIFY, not DONE — Orchestrator tests then marks DONE
3. Adversarial 2-phase verification: Sonnet gathers evidence, Opus judges
4. Describe PROBLEMS not SOLUTIONS in strand definitions

**Strand template**: Strategic Context (WHY) → Problem (symptoms) → Investigation Steps → Success Criteria → Key Files

## Website

Greco-Futurism concept ("The Digital Oracle"). Design system: [`docs/CHARTE_GRAPHIQUE.md`](docs/CHARTE_GRAPHIQUE.md).
Stack: Astro + GitHub Pages. URL: https://plnech.github.io/Priap.OS/

## Resources

- [LeekWars API](https://leekwars.com/help/api)
- [Fight Generator](https://github.com/leek-wars/leek-wars-generator)
- [LeekScript](https://github.com/leek-wars/leekscript)
- [Java Utilities](https://github.com/LeBezout/LEEK-WARS)
