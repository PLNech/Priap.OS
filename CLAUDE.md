# Priap.OS - LeekWars AI Agent

> **Claude**: Keep `THOUGHTS.md` in context (Read at session start) and up-to-date (Edit as you learn). Track learnings, questions, hypotheses to test there - not here.

## Task Hierarchy (Source of Truth: Claude Code Tasks)

Strategic planning lives in the task system. High-level structure:

| Task | Pillar | Purpose |
|------|--------|---------|
| #0001 | 🏆 North Star | Reach Top 10 Leaderboard |
| #0100 | 🔧 Infrastructure | Tooling, flywheel, simulation |
| #0200 | 🧠 AI Strategy | Combat logic, archetypes, stalemate fixes |
| #0300 | 📊 Data & Analysis | Fight parsing, pattern detection, metrics |
| #0400 | 🎮 Game Mechanics | Build, chips, stats, equipment |
| #0500 | ⚙️ Operations | Daily fights, automation, maintenance |

Sub-tasks use notation like #0201, #0202 under their pillar.

## Project Overview
Automated LeekWars agent aiming for **top 10 ladder**. The strategy: build infrastructure that lets us iterate faster than anyone else.

## The Winning Formula

### Core Insight
- Online fights: 150/day (scarce, precious)
- Offline fights: 1.8M/day potential (21.5 fights/sec)
- **Leverage ratio: 13,000:1**

**Principle**: Never test online what we can test offline. Every online fight is for data collection, not experimentation.

### The Flywheel
```
Fight Online → Collect Data → Analyze Losses → Improve AI Offline
     ↑                                                    ↓
     └──────────── Deploy Best Variant ←──────────────────┘
```

The scaffolding lets us spin this flywheel 13,000x faster than manual iteration.

## Website & Brand Identity

### Concept: "The Digital Oracle"
Priapos (Greek god of gardens) meets LeekWars meets Cyberpunk Singularity.
**Greco-Futurism**: Ancient wisdom encoded in neural networks.

### Charte Graphique
Full design system documented in [`docs/CHARTE_GRAPHIQUE.md`](docs/CHARTE_GRAPHIQUE.md).

**Quick Reference**:
| Element | Value |
|---------|-------|
| Background | `#1A1A2E` (Void Black) |
| Text | `#E8E4D9` (Marble Cream) |
| Primary Accent | `#00F5D4` (Oracle Cyan) |
| Secondary Accent | `#7B2CBF` (Divine Purple) |
| Success/Growth | `#90BE6D` (Leek Green) |
| Highlight | `#B8860B` (Bronze) |
| Headlines | Cinzel (serif, uppercase) |
| Body | Inter (sans-serif) |
| Code | JetBrains Mono |

### Website Stack
- **Generator**: Astro (in `docs/`)
- **Hosting**: GitHub Pages
- **Tone**: Playful mythological + tech blog casual with real code samples

### Logo
Oracle Eye pyramid with leek as pupil - see `docs/public/images/logo/`

## Development Philosophy: Empirical Agentic TDD

### Core Principles
1. **Test First, Discover Second** - Write small probing tests before building abstractions
2. **Iterative Discovery** - Use Playwright introspection to discover DOM/API structure empirically
3. **Fail Fast, Learn Fast** - Run experiments immediately, capture failures as documentation
4. **Living Documentation** - Update docs/ as discoveries are made, not after
5. **Build Tools as You Go** - Every repeated task is a tooling opportunity

### Tooling Philosophy
- **Identify repetition** - If you do something twice, consider automating it
- **Meta-tooling** - Tools that build tools accelerate exponentially
- **Layered automation**:
  - L0: Manual exploration (curl, browser)
  - L1: Scripts for specific tasks (login, fight, upload)
  - L2: Library abstractions (api.py, browser.py)
  - L3: Orchestration (batch runners, pipelines)
  - L4: Self-improving systems (RL, auto-tuning)
- **Invest in tooling early** - Time spent on good tools pays compound interest
- **Composable primitives** - Small, focused tools that combine well

### When Adding New Features
1. First: curl/browser test the endpoint/interaction manually
2. Second: Write a minimal probe script that captures the response
3. Third: Document findings in relevant docs/*.md
4. Fourth: Implement proper client method with error handling
5. Fifth: Add to test suite
6. **Sixth: Git commit after each successful milestone**

### Git Discipline
- **Commit after each success** - Small, atomic commits after each working feature
- **Descriptive messages** - What changed and why, not just "update"
- **Clean history** - Each commit should be a logical unit of work
- **Feature branches** - New features on branches, merge when stable

## Project Structure
```
src/leekwars_agent/    # Core library
  api.py               # HTTP API client
  simulator.py         # Local fight simulation (21.5 fights/sec)
  fight_parser.py      # Parse fight replays
  visualizer.py        # Fight replay viewer
  fight_analyzer.py    # Extract patterns from fights (TODO)
scripts/               # Automation scripts
  run_fights.py        # Online fight runner
  compare_ais.py       # A/B test AI versions (TODO)
  test_builds.py       # Capital allocation experiments (TODO)
  fetch_fight.py       # Download fight by ID (TODO)
  parse_history.py     # Scrape fight history (TODO)
ais/                   # LeekScript AI files
  fighter_v1.leek      # Current deployed AI
  fighter_v2.leek      # Improved variant (TODO)
data/                  # Fight data, configs
  fights/              # Raw + parsed fight data
docs/                  # Living documentation
  API.md               # API endpoints discovered
  LEEK.md              # Game mechanics & strategy
```

## Credentials
- Login: `leek@nech.pl`
- Account: PriapOS (Farmer ID: 124831)
- Leek: IAdonis (ID: 131321)

## Current State (Session 8 - 2026-01-18)
- **Level**: 25 (was 20, +5 this session!)
- **Rank**: Climbing (fighting L20-L25 opponents)
- **Win rate**: 38% raw / 48% excluding draws
- **Build**: STR=234, AGI=10
- **AI Deployed**: fighter_v8.leek "Architect"
- **Chips**: 0/6 equipped (need to craft - see below)
- **Habs**: 51,515+
- **Components**: 12+ resources for crafting
- **Website**: https://plnech.github.io/Priap.OS/
- **Priority Bug**: 21% draw rate from kite stalemates

### Active Learnings
**See `THOUGHTS.md`** for session analysis, hypotheses, and discoveries.

### AI Versions
| Version | Codename | Key Feature | Status |
|---------|----------|-------------|--------|
| v8 | Architect | 5-module subsystems, ops-optimized | **DEPLOYED** |
| v6 | Oracle | TTK + counter-kiter | Baseline |

## Session 4 Achievements
**Critical Discovery:**
- Operations management is a core game mechanic (error 113 = too_much_ops)
- `getCellDistance()` is expensive - minimize in loops
- v3 kiting AI: 85x more ops-efficient than v1 (750 vs 65,000 ops)

**Scripts Added:**
- `scripts/debug_fight.py` - Single fight analysis with full action log
- `scripts/get_recent_fights.py` - Fetch recent fight IDs
- `api.get_leek_history()` - New API method

**Key Finding:**
- Kiting strategy LOSES at low damage levels (20% vs 49% win rate)
- Extends fights to timeout instead of getting kills
- Strategy must match damage output capability

## Session 3 Achievements
**Scaffolding Built:**
- `scripts/compare_ais.py` - A/B test AIs offline (2.5 fights/sec)
- `scripts/test_builds.py` - Capital allocation testing
- `scripts/fetch_fight.py` - Download fight replays
- `scripts/parse_history.py` - Fight history parser
- `src/leekwars_agent/fight_analyzer.py` - Pattern extraction

**Critical Bugs Fixed:**
- Simulator had 96% team 1 bias → fixed with team swapping
- AI file paths not found → copy to generator directory first

**Tested & Validated:**
- AI v2 (shoot-first): NO improvement (50.5% vs 49.5%)
- Capital allocation: +STR/+AGI/+Frequency all 50% win rate
- **Conclusion**: Strategy matters, stats don't (yet)

## Key API Notes
- Base URL: `https://leekwars.com/api/`
- Auth: JWT token via cookie after login
- Login requires: `login`, `password`, `keep_connected` params
- Token in `set-cookie: token=<jwt>` header

### Critical API Discoveries
- `spend-capital`: POST with `characteristics` as JSON string: `data={'characteristics': json.dumps({'strength': 50})}`
- `add-weapon`: Returns "already_equipped" if weapon in slot (good)
- Weapons in slots ≠ weapon held. AI must call `setWeapon(WEAPON_PISTOL)` during combat
- WEAPON_PISTOL item ID = **37** (not 1!) - this caused early bugs
- `GET /fight/get/<fight_id>` - Full fight replay data
- No bulk fight history API - must scrape `/leek/131321/history` or track locally

## Commands
```bash
# Run any script
poetry run python scripts/<script>.py

# Run online fights
poetry run python scripts/run_fights.py 50

# Compare AI versions (TODO)
poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000

# Test build variants (TODO)
poetry run python scripts/test_builds.py --stat strength --range 90-110
```

## Local Validation (Java)

**Always prefer local validation over online API** - it's faster, reliable, and works offline.

**IMPORTANT**: Simulation validates AI code automatically - skip standalone validator and go straight to testing:

```bash
# Test AI directly (validates during simulation)
poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000
```

Optional standalone validation (rarely needed):
```bash
java -jar tools/leek-wars-generator/leekscript/leekscript.jar ais/fighter_v1.leek
```

Requires Java 21+ (use SDKMAN: `sdk install java 21.0.5-tem`)

### LeekScript Gotchas
- `var` = block-scoped, `global` = file-scoped
- Use `global` for variables reassigned across blocks
- Error 33 = undefined reference, Error 35 = unused variable
- `setWeapon()` costs 1 TP - only call once per fight!
- LS4: `null` coerced to 0 in numeric contexts (arithmetic, comparisons)
- LS4: Type annotations are FREE - zero runtime operation cost
- `say(message)` costs 1 TP - use `debug()` instead (free)!

### LeekScript Syntax (Compiler Requirements)
**IMPORTANT**: These cause silent failures or cryptic errors if violated:
- **Includes need `.leek` extension**: `include("module.leek")` NOT `include("module")`
- **Semicolons after bare return**: `if (x) return;` NOT `if (x) return` (parser gets confused)
- **Semicolons recommended**: While often optional, add `;` after statements to avoid parser ambiguity
- **Empty maps**: `var m = [:]` is valid LeekScript syntax for empty associative array
- **For-each syntax**: `for (var x in array)` or `for (var k : var v in map)` (BOTH vars need `var`!)
- **C-style for loops**: `for (var i = 0; i < n; ++i)` - prefer pre-increment `++i`

### LeekScript Debugging Meta-Approach
When encountering LeekScript compiler errors:
1. **Standalone compiler** (`leekscript.jar`) validates syntax but NOT fight functions
   - `UNKNOWN_VARIABLE_OR_FUNCTION` on fight functions (isEmptyCell, getCell, etc.) is OK
   - Use `compare_ais.py` or `debug_fight.py` for full validation with fight context
2. **Common error patterns**:
   - `CLOSING_PARENTHESIS_EXPECTED` → Check for missing semicolons on previous lines
   - `VALUE_EXPECTED` → Parser in wrong state, likely missing semicolons above
   - `AI_NOT_EXISTING` → Include path wrong (add `.leek` extension)
3. **When fixing syntax errors**:
   - Fix ONE error at a time, re-test immediately
   - Document each fix in this file for future reference
   - Apply fixes to ALL similar patterns (use sed/grep)

### AI Logging Requirements (CRITICAL)
**Every AI module MUST have comprehensive debug output** for online introspection.
Without logging, we fly blind during online fights and can't diagnose behavior issues.

**Required debug points in every AI:**
1. **State tracking**: Turn number, phase, HP, key metrics
2. **Strategy selection**: Which strategy was chosen and WHY
3. **Movement decisions**: Where we moved, what cell we targeted
4. **Combat execution**: Attacks made, damage dealt, TP used
5. **Positioning decisions**: Danger levels, safe cells found, retreat choices

**Debug function checklist per module:**
```leekscript
// v8_state: debugState() → turn, phase, TTK, patterns
// v8_danger_map: debugDangerMap() → min/max/avg danger, safest cell
// v8_combat: logs after executeAttacks() → hits, damage, TP
// v8_hide_seek: logs in getBestRetreatCell() → safe cell count, choice
// fighter_v8: strategy_name logged, all subsystem debug calls
```

**Remember**: `debug()` is FREE (no TP cost). Use it liberally!

### LeekScript Quick Reference
```leekscript
// Entity info
getCell() / getCell(entity)     // Cell positions
getLife() / getLife(entity)     // HP
getMP() / getTP()               // Movement/Action points
getNearestEnemy() / getEnemies() / getAllies()

// Movement (NO moveToCell - only moveTowardCell!)
moveToward(entity)              // Uses all MP toward entity
moveToward(entity, n)           // Move n cells toward entity
moveTowardCell(cell)            // Move toward a cell
moveAwayFrom(entity)            // Move away from entity
moveAwayFromCell(cell)          // Move away from cell
getCellDistance(cell1, cell2)   // EXPENSIVE - cache result!

// Combat
setWeapon(WEAPON_PISTOL)        // Equip (costs 1 TP)
useWeapon(entity)               // Attack
useChip(CHIP_CONSTANT, entity)  // Use spell

// Weapon info
getWeaponCost(w) / getWeaponMinRange(w) / getWeaponMaxRange(w)

// Debugging (FREE - no TP cost)
debug(value) / debugW(value) / debugE(value)

// Return codes
USE_SUCCESS, USE_FAILED, USE_NOT_ENOUGH_TP, USE_INVALID_TARGET
```

### Simulator vs Online Differences (IMPORTANT)

The local simulator (Java generator) differs from online fights:

| Aspect | Simulator | Online |
|--------|-----------|--------|
| First-mover advantage | ~0% impact | ~58% (attacker wins) |
| Team 1 position bias | ~93% win rate | Varies by map |
| Turn order | Random or `starter_team` | Attacker always first |

**Key findings:**
- `starter_team` parameter added to generator (fork: `feature/starter-team`)
- Even with `starter_team=1`, Team 1 wins 93%+ due to position advantage
- Stats have minimal impact (2-3% difference)
- Simulator is useful for AI logic testing, NOT for win rate prediction

**Use simulator for:**
- Validating AI code compiles
- Testing AI behavior/strategy
- A/B testing AI variants (relative comparison)
- Operations profiling

**Do NOT use simulator for:**
- Predicting online win rates
- Testing first-mover strategies
- Absolute performance measurement

### Operations Management (CRITICAL)
Each leek has an **operation limit per turn** (upgradeable via cores/memory).
- Every function call, loop iteration, comparison costs operations
- Error 113 = `too_much_ops` = AI exceeded operation limit → turn ends immediately
- `getCellDistance()` is expensive - minimize calls in tight loops
- Complex while loops can easily blow the budget

**Key Efficiency Metrics:**
- **Op Velocity** = operations per cell moved (movement efficiency)
- **Op Lethality** = operations per damage dealt (combat efficiency)
- **Op Budget** = % of limit used per turn (resource management)

**Best Practices:**
- Cache expensive calculations (e.g., compute distance once, store in variable)
- Use simple loop counters instead of recalculating conditions
- Limit loop iterations explicitly (e.g., `for (var i = 0; i < 10; i++)`)
- Profile operation usage in test fights

## Fight Analysis Insights (Session 3)

From analyzing fight 50863105 (a loss):
- **Damage per shot**: Us 37 avg vs opponent 22 avg (70% stronger!)
- **But we lost**: Opponent got 5 shots, we got 3
- **Root cause**: Range timing - opponent reached attack range first
- **Lesson**: Action economy > raw damage. First strike wins close fights.

## Resources
- [LeekWars API](https://leekwars.com/help/api)
- [Fight Generator](https://github.com/leek-wars/leek-wars-generator)
- [LeekScript](https://github.com/leek-wars/leekscript)
- [Java Utilities](https://github.com/LeBezout/LEEK-WARS)
