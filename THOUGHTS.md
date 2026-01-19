# Priap.OS - Active Thoughts & Learnings

> Living document for hypotheses, discoveries, and session-to-session insights.
> Claude: Read this at session start, update as you learn.

---

## Priority Queue (Next Session)

| # | Task | Impact | Approach |
|---|------|--------|----------|
| 🔴 | **Fix kite stalemates** | +21% WR | Add turn_count > 30 → force_engage |
| 🟡 | Craft chips | +damage | Manual UI: /market → Inventory |
| 🟢 | Archetype testing | Find gaps | Offline A/B vs rusher/tank/burst |

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
