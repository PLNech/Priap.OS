# Priap.OS - LeekWars AI Agent

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

## Current State (Session 3)
- Level: ~4 (17 capital available)
- Rank: ~56,000
- Win rate: 79% (19W-5L from 21 fights)
- Build: STR=96, AGI=10
- Capital: 17 UNUSED (SAVE - stats don't matter yet)
- Fights remaining: ~139 today
- AI: fighter_v1.leek deployed

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

```bash
# Validate LeekScript locally
java -jar tools/leek-wars-generator/leekscript.jar ais/fighter_v1.leek

# Run simulated fights
poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000
```

Requires Java 21+ (use SDKMAN: `sdk install java 21.0.5-tem`)

### LeekScript Gotchas
- `var` = block-scoped, `global` = file-scoped
- Use `global` for variables reassigned across blocks
- Error 33 = undefined reference, Error 35 = unused variable
- `setWeapon()` costs 1 TP - only call once per fight!

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
