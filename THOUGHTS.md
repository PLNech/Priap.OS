# Priap.OS - Active Thoughts & Learnings

> Living document for hypotheses, discoveries, and session-to-session insights.
> Claude: Read this at session start, update as you learn.

---

## TODOs (Next Session)

1. ✅ ~~**FIX SIMULATOR CHIP SUPPORT** (#0111)~~ - Fixed!
2. ✅ ~~**Test Scenario API** (#0118)~~ - Unlimited server-side fights!
3. ✅ ~~**Fight DB Scraper** (#0308)~~ - 2400+ fights scraped, BFS graph traversal!
4. ✅ ~~**Meta Analysis CLI** (#0303)~~ - `leek analyze meta/level/stats`
5. 🔴 **Fix kite stalemates** (#0201) - Our 6.5% draw rate is OK but could improve
6. 🟠 **Battle Royale automation** (#0509) - 10 free fights/day, needs WebSocket
7. 🟡 **Buy magnum** (#0407) - Need 7,510 habs
8. 🟢 **Continue scraping** - Queue ready, run `leek scrape discover && leek scrape run`

---

## Session 17 Fight Scraper & Meta Analysis (2026-01-24)

**Theme:** Built full fight scraper with BFS graph traversal, analyzed 2400+ fights.

### Infrastructure Built

| Component | Description |
|-----------|-------------|
| **Scraper** | BFS graph traversal of leek-fight bipartite graph |
| **FightDB** | SQLite + WAL mode, priority queue, observations |
| **Analyze CLI** | `leek analyze meta/level/stats` |
| **Retry** | Exponential backoff in auth + scraper (429 recovery) |

### CLI Commands Added
```bash
leek scrape discover -l 100    # BFS discovery from observed leeks
leek scrape run -n 500         # Process queue
leek analyze meta              # Full L25-100 analysis
leek analyze level 34          # Level-specific deep dive
leek analyze stats             # Database statistics
```

### Key Meta Findings (2417 fights, 12K leeks)

| Metric | Value | Insight |
|--------|-------|---------|
| First-mover | 50% vs 44% | Slight advantage, not dominant |
| Draw rate | 6.5% | Our ~21% was anomalous, now closer to meta |
| STR dominance | 45% WR | Wins everywhere except L40-49 transition |
| AGI weakness | 25% WR | Pure AGI fails at low levels |
| L90+ AGI | 71% WR | High-level AGI viable (small sample) |

### Optimal STR by Level (from data)

| Level | Avg STR | Optimal Range | Win Rate |
|-------|---------|---------------|----------|
| L29-39 | 179 | 200-249 | 56% |
| L40-49 | 56 | Hybrid zone | 45% |
| L50-59 | 211 | 200+ | 42% |
| L90-99 | 205 | AGI viable | 71%* |

**Our STR (234) is in the optimal range for L34!**

### Database Stats
- **2,417 fights** | **11,712 observations** | **48 MB**
- Queue persists to disk (interrupt-safe)
- BFS tracks scraped leeks to avoid duplicates

### API Endpoint Fix
`history/get-leek-history/{id}` (was using wrong path)
- Source: `tools/leek-wars/src/component/history/history.vue:163`

---

## Session 16 Test Scenario API Discovery (2026-01-23)

**Theme:** Discovered UNLIMITED server-side fights via test scenario API!

### Critical Discovery 🔥

LeekWars has a hidden test fight system with **NO daily limit**:

| Endpoint | Purpose |
|----------|---------|
| `POST ai/test-scenario` | Run test fight → returns fight_id |
| `GET test-scenario/get-all` | List saved scenarios |
| `POST test-scenario/new` | Create scenario |
| `POST test-leek/new` | Create custom test leek |

### Three-Tier Testing Pyramid (NEW!)

| Tier | Tool | Speed | Limit | Use Case |
|------|------|-------|-------|----------|
| **1. Local** | Java simulator | 21.5/sec | Unlimited | Quick AI logic tests |
| **2. Server Test** | `leek test run` | ~3sec | **UNLIMITED** | Real server validation |
| **3. Garden** | `leek fight run` | ~3sec | 50/day | Talent/XP gain |

### CLI Commands Added

```bash
leek test list           # Show 7 saved scenarios
leek test run 37863      # Run test fight (NO quota burn!)
leek test create "Name"  # Create new scenario
leek test add-leek ...   # Add leek to scenario
```

### Impact on Flywheel

**Before:** Local sim (approximate) → Garden fights (precious, 50/day)
**After:** Local sim → **Server test (unlimited, real)** → Garden fights

This means we can validate AI changes on the REAL server before burning daily fights!

---

## Session 15 Trophy Hunting (2026-01-23)

**Theme:** Discovered trophy enigmas = free habs! Built trophy hunting infrastructure.

### Quick Wins Unlocked 💰
| Trophy | Method | Reward |
|--------|--------|--------|
| **konami** (#113) | ↑↑↓↓←→←→BA anywhere | 40,000 habs ✅ |
| **you_can_see_me** (#234) | Toggle SFW mode in /settings | 2,500 habs ✅ |

**Total earned: 42,500 habs**

### Trophy Enigmas Discovered (via API inspection)

| Trophy | Habs | Description | Players |
|--------|------|-------------|---------|
| **lost** (#323) | 810,000 | `"???"` | Only 37! |
| **xii** (#188) | 810,000 | "Consume 12 12 12 12 12 operations" | Only 73! |
| **9_34** (#231) | 360,000 | `"???"` Platform 9¾ | 209 |
| **mathematician** (#87) | 250,000 | "Walk on 50 prime cells" | ~30 |
| **shhh** (#187) | 250,000 | `"???"` Secret | ~300 |
| **lucky** (#92) | 90,000 | Click clovers | ~30 |

**Available habs from enigmas: ~2.6M**

### Infrastructure Built

1. **`leek trophy status`** - CLI command to check enigma progress
2. **`ais/trophy_hunters/`** - Specialized AIs:
   - `mathematician.leek` - Routes through prime cells (2,3,5,7,11...)
   - `wanderer.leek` - 100m in one fight
   - `executor.leek` - Win in <5 turns
   - `patient.leek` - Win in >60 turns
   - `static.leek` - Win without moving
   - `pacifist.leek` - Win without damage
   - `xii_ops.leek` - Experimental ops counter

### Key Learnings

#### Trophy API Endpoints
- `GET /trophy/get-farmer-trophies/{id}/en` - Full trophy status with descriptions
- `GET /trophy-template/get/{code}/en` - Single trophy details
- `POST /trophy/unlock` - UI-triggered unlocks (konami, SFW, etc.)

#### Enigma Patterns
- `"???"` description = secret/puzzle trophy
- Very low player counts = hard puzzles worth investigating
- XII trophy description reveals exact mechanics (ops counting)

#### Prime Cells for Mathematician
Arena is 18x18 (cells 0-323). Primes: 2,3,5,7,11,13,17,19,23,29,31,37,41,43,47...
Need 50 total across all fights (cumulative).

---

## Session 14 Deploy Infrastructure (2026-01-23)

**Theme:** Fix deploy pipeline, get v10 online with chips.

### Accomplished
1. ✅ **Spent 76 capital** → STR 310 (+32% damage)
2. ✅ **Fixed `leek ai deploy`** - Multi-file support with dependency tracking
3. ✅ **Fixed API endpoint** - `ai/new` → `ai/new-name` (verified from frontend)
4. ✅ **Deployed v10 "Phoenix"** - Self-contained, uses chips via getChips()

### Key Learnings

#### LeekWars Multi-File AI Limitation
**Each AI file is compiled SEPARATELY** - includes are resolved at runtime, not compile time.
- v9's modular architecture (5 files with inter-dependencies) → FAILS
- Each module tries to call functions from other modules → "undefined function"
- **Solutions:**
  1. Self-contained AIs (v10 approach)
  2. Bundle modules into one file
  3. Careful dependency ordering with forward declarations

#### API Discovery Protocol (Added to CLAUDE.md)
**NEVER guess endpoints** - always check frontend source first:
```bash
grep -rn "LeekWars.post.*endpoint" tools/leek-wars/src
```
Then cite source in api.py docstring.

#### CLI-First Development (Added to CLAUDE.md)
Never raw API calls → always improve CLI first, then use it.

### Current State
| Metric | Value |
|--------|-------|
| STR | **310** (was 234) |
| AI | **v10 "Phoenix"** (was v6) |
| Chips | Uses FLAME, FLASH, CURE, PROTEIN, BOOTS, MOTIVATION |
| Fights | 0/50 (waiting for refill) |

---

## Session 13 Ground Truth Grounding (2026-01-23)

**Theme:** Stop Claude hallucinating game values with systematic grounding.

### Problem Identified
User feedback: Claude was making math errors and inventing values:
- "4+4+3 = 11 TP but you only have 10" - planned impossible actions
- Confused pistol (3TP) with magnum (5TP)
- Forgot `setWeapon()` costs 1 TP

### Root Cause
Ground truth EXISTS in submodules but wasn't being consulted:
- `tools/leek-wars/src/model/weapons.ts` - 40 weapons
- `tools/leek-wars/src/model/chips.ts` - 174 chips
- `tools/leek-wars-generator/.../FightConstants.java` - constants

### Solution Implemented (#0112 ✅)
1. **`docs/GROUND_TRUTH.md`** - Quick reference for equipment stats + TP budget
2. **Grounding Protocol in CLAUDE.md** - Mandatory verification before combat math
3. **`scripts/parse_ground_truth.py`** - Parser for submodule data
4. **Bug fixes**:
   - `market.py:88` - Fixed comment (ID 40 is destroyer, not magnum)
   - `visualizer.py:512` - Added 8 more weapons to mapping

### Key Values to Remember
| Item | TP Cost | Notes |
|------|---------|-------|
| Pistol | 3 | max 4/turn |
| Magnum | 5 | max 2/turn, need to buy |
| `setWeapon()` | 1 | HIDDEN COST! |
| FLAME | 4 | max 3/turn |
| FLASH | 3 | AOE, CD=1 |

**Rule**: Trust submodules > API exports > our code

---

## Session 12 AI Rebuild & Simulator Gap (2026-01-23)

**Theme:** First-principles AI rebuild, discovered simulator doesn't support chips.

### v10 "Phoenix" Created
New AI with burst aggro philosophy:
- Uses `getChips()` for simulator compatibility
- FLASH + FLAME x3 + weapon rotation
- Tracks chip cooldowns manually
- Buffs turn 1 (MOTIVATION, BOOTS, PROTEIN)

### Critical Discovery: Simulator Gap 🔴
| Issue | Impact |
|-------|--------|
| `getChips()` returns empty | Can't test chip AIs offline |
| CHIP_* constants undefined | Had to use dynamic lookup |
| Chips passed but not accessible | EntityConfig.chips not exposed |

**Task created**: #0111 - Fix simulator chip support

### Chip Ground Truth (from chips.ts)
| Chip | TP | CD | Uses/Turn | Range | Effect |
|------|----|----|-----------|-------|--------|
| FLAME (5) | 4 | 0 | **3 max** | 2-7 | 29±2 DMG |
| FLASH (6) | 3 | 1 | unlimited | 1-10 | 32±3 DMG |
| CURE (4) | 4 | 2 | unlimited | 0-5 | 38±8 HEAL |
| PROTEIN (8) | 3 | 3 | unlimited | 0-4 | +80 STR x2t |
| BOOTS (14) | 3 | 5 | unlimited | 0-5 | +2 MP x2t |
| MOTIVATION (15) | 4 | 6 | unlimited | 0-5 | +2 TP x3t |

### CLI Improvements
New commands added:
- `leek status` - Quick overview (fights, habs, AI, recent)
- `leek build show/spend/recommend` - Capital management
- `leek ai list/deploy/local` - AI management
- `leek sim specs/compare/debug` - Simulation with real specs

### Current State
- **Level**: 34, **Talent**: 38
- **Capital**: 76 unspent!
- **AI**: v6 deployed (doesn't use chips!)
- **Fights**: 30/30 remaining
- **Recent**: WDDDD (still draws from stalemates)

---

## Session 11 Equipment & Testing (2026-01-23)

**Theme:** Bought chips, learned about dynamic data, added regression tests.

### The Weapon Destroyer Incident 🔥
| What | Impact |
|------|--------|
| Hardcoded ID 40 as "magnum" | It's actually "destroyer" (L85!) |
| Bought wrong weapon | Wasted 7,510 habs, couldn't equip |
| Root cause | Manual item ID mapping = human error |

**Fix:** Dynamic item loader with fallback chain:
```
API (fresh) → Cache (recent) → File (items.ts) → Hardcoded (emergency)
```

### Equipment Progress
| Before | After |
|--------|-------|
| 0/6 chips | **6/6 chips** ✅ |
| 0 weapons | Still pistol (need habs for magnum) |
| 75k habs | 4,752 habs |

**Chips equipped:** flash, spark, flame, cure, leather_boots, protein

### Key Rule Added
> **"Whoops = Unit Test"** - Every bug deserves a regression test.

11 tests in `tests/test_market.py` now guard against item ID confusion.

### Scraping Tip (tagadai)
- 10 req/sec max, wait 10s on 429
- Full fights DB in hours
- Already on GitHub

---

## Session 10 CLI & Crafting (2026-01-23)

**Theme:** Built unified CLI tool, discovered crafting API works!

### `leek` CLI Built (#0104 ✅)
| Command | Purpose |
|---------|---------|
| `leek info garden/leek/farmer` | Status checks |
| `leek craft inventory` | List resources |
| `leek craft list` | Show craftable recipes |
| `leek craft make <id>` | Craft items! |
| `leek fight status/run/history` | Fight operations |
| `leek --json <cmd>` | Machine output for Claude |

### Key Discoveries
| Finding | Impact |
|---------|--------|
| Crafting API EXISTS | `POST /api/item/craft {scheme_id}` works! |
| Inventory in farmer data | `/farmer/get-from-token` has everything |
| 0 chips, 0 weapons owned | Explains crippled damage! |
| Chips = market purchase | Not crafted - need to BUY |
| 60 recipes in schemes.ts | Components craftable, chips buyable |

### Crafting Test
```
Before: sand x3, earth x10, fire x13
Craft: `leek craft make 60` (sand recipe)
After: sand x4, earth x6, fire x9 ✅
```

---

## Session 9 Infrastructure Blitz (2026-01-23)

**Theme:** Fixed the broken grind, connected the data pipeline.

### Critical Fixes
| Issue | Fix | Impact |
|-------|-----|--------|
| Cron dead 29 days | GitHub Actions 3x daily | Reliable grind |
| main/master mismatch | Force push master→main | Workflow deploys |
| Poetry 1.7 vs 2.0 | Updated to 2.0.1 | PEP 621 support |
| Missing README | `--no-root` flag | Install works |
| No DB saving | Added `store_fight()` | Data pipeline connected |

### API Discoveries (Frontend Study)
| Feature | Endpoint | Status |
|---------|----------|--------|
| Garden fights | `/garden/start-solo-fight/...` | Found, not implemented |
| Tournament reg | `/leek/register-tournament/...` | Found, not implemented |
| Chip crafting | None | Browser-only, no API |

### Current State
- **Level:** 27 (was 25)
- **Fights:** 150/150 (bought pack via GH Actions!)
- **Talent:** 79
- **First GH Actions fight:** DRAW vs Sukamushu (stalemate confirmed)

### Task System Established
42 tasks across 5 pillars:
- #0100 Infrastructure (7 tasks)
- #0200 AI Strategy (5 tasks)
- #0300 Data & Analysis (6 tasks)
- #0400 Game Mechanics (6 tasks)
- #0500 Operations (8 tasks)

---

## Session 8 Fight Analysis (95 fights, 2026-01-18)

**Result**: 36W-39L-20D (38% raw, 48% excluding draws)
**Level**: 20 → 25 (+5!)

### Critical Finding: 21% Draw Rate
All 20 draws were 64-turn timeouts (kite stalemates).

| Pattern | Count | Insight |
|---------|-------|---------|
| Quick wins (≤5t) | 18 | STR advantage decisive when we strike first |
| Quick losses (≤5t) | 6 | Enemy has better positioning/first strike |
| Long fights (>10t) | 15 | Both kiters, neither commits |
| Draws (64t) | 20 | **KITE STALEMATES** - priority fix |

### Why Draws Happen (Theory)
1. Both AIs enter kite mode simultaneously
2. Neither commits to close gap (both retreat after shooting)
3. Damage dealt < effective threshold
4. Fight times out at turn 64

### Proposed Fix
```leekscript
// In v8_state.leek - add stalemate detection
if (turn_count > 30 && total_damage_dealt < 100) {
    fight_phase = "force_engage"  // Break the kite loop
}
```

### Opponent Analysis
- **L20-21**: Mostly wins (favorable matchups)
- **L22-23**: Mixed (skill-based)
- **L24-25**: More losses (level disadvantage)

---

## Chip/Crafting Discovery (Session 8)

**LeekWars v2.40+ changed item acquisition:**
- Chips are NOT purchased - must be CRAFTED from components
- Components drop from fights ("rareloot" in fight data)
- Most chip APIs return 401 - browser UI only
- We have 12+ components ready to craft

**To craft**: /market → Inventory → click item → craft recipe

**Resource template IDs we have**:
- 191, 193, 194, 195 (common)
- 203, 204, 206, 207 (materials)
- 231, 232, 233, 236 (special)

---

## Scraping Tip (from tagadai)

**Full fights DB scraper** - 10 req/sec max, wait 10s on 429:
```
- Already on GitHub (tagadai's repo)
- With regulator: full DB in a few hours
- Dashboard included (crude but functional)
```

Rate limit: 10 req/sec → wait 10s on HTTP 429

---

## Open Questions

1. **What chips can we craft** with current components?
2. **Does danger map actually influence positioning?** (need debug validation)
3. **Why do some L20 opponents beat us?** (analyze specific losses)
4. **Optimal turn threshold for force_engage?** (30? 25? 40?)

---

## Hypotheses Backlog

| ID | Hypothesis | Test Method | Status |
|----|------------|-------------|--------|
| H001 | Turn 30+ stalemate → force_engage | Offline A/B n=1000 | Pending |
| H002 | Chip damage increases WR | Online before/after | Pending |
| H003 | First-strike advantage > stats | Analyze quick wins/losses | Pending |
| H004 | Danger map positioning helps | Add debug logging | Pending |

---

## Rejected Hypotheses

| ID | Hypothesis | Result |
|----|------------|--------|
| S005 | Kite at 60% HP vs 40% | REJECTED (49.9% vs 50.1%) |
| S006 | Shoot before retreat in kite | REJECTED (49.9% vs 50.1%) |

**Lesson**: Kite variations don't matter at high STR - fights end quickly.

---

## Technical Learnings

### Operations Budget
- v8 optimized: 27k ops/turn (was 707k)
- `getCellDistance()` is expensive - cache results
- BFS flood-fill is expensive - skip in opening phase
- Error 113 = too_much_ops = turn ends immediately

### LeekScript Gotchas
- `include("file.leek")` needs `.leek` extension
- Semicolons after bare `return;` statements
- `for (var k : var v in map)` - both need `var`
- Empty maps: `var m = [:]`

### API Quirks
- Crafting endpoints return 401 - use browser
- `spend-capital`: needs `json.dumps({'strength': N})`
- Fight history: scrape `/leek/ID/history`, no bulk API
