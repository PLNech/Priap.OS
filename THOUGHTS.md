# Priap.OS - Active Thoughts & Learnings

> Living document for hypotheses, discoveries, and session-to-session insights.
> Claude: Read this at session start, update as you learn.

---

## TODOs (Next Session)

1. ✅ **BUY CHIPS FROM MARKET** (#0401) - 6/6 chips equipped! Weapon pending (low habs)
2. 🔴 **FIX KITE STALEMATES** (#0201) - 21% draw rate kills win rate
3. 🟡 **Implement garden API** (#0109) - Passive income endpoints
4. 🟡 **Implement tournament API** (#0110) - Registration endpoints
5. 🟢 **Archetype testing** (#0203) - Offline A/B
6. 🟢 **Scrape full fights DB** - See tip below

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
