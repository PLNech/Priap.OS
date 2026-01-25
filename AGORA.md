# AGORA - Multi-Agent Coordination Space

> **Shared context for Orchestrator ↔ WorkerAgent communication.**
>
> **Workers: READ THIS FIRST, then follow the protocol below.**

## Worker Protocol (MANDATORY)

1. **On task start**: Update "Active Workers" table with your agent name + strand
2. **On each milestone**: Edit your strand section with progress/findings
3. **On blockers**: Add to "Blockers" section immediately, don't wait
4. **On completion**: Move findings to "Completed Work", mark strand DONE
5. **Commit after each milestone** - small atomic commits, descriptive messages

---

## Current Session: 2026-01-25

### Active Workers
| Agent | Task | Status | Started | Notes |
|-------|------|--------|---------|-------|
| Crush | Strand 1 Simulator Fix | DONE | 2026-01-25 | Implemented AI copy in simulator.py, verified with archetype tests |
| Crush | Strand 2 Assessment | DONE | 2026-01-25 | Found garden automation already exists in api.py + CLI |

### Blockers (Workers: Add here immediately if stuck)
| Agent | Blocker | Needs |
|-------|---------|-------|
| - | - | - |

### Orchestrator Notes

**Strategic Context (from PONR analysis):**
- PONR claim **disproved**: Turn 2.7 → actual Turn 5.5-10 (L20-259 data, n=2535)
- stat_cv validated: pure builds (>0.85) win **57% in long fights** (16+ turns)
- Our stat_cv=0.94 is GOOD for attrition play

**Today's Budget:**
- ~40 online fights remaining
- Unlimited offline simulation (BLOCKED by #26)
- Unlimited test scenario API

**Priority Stack:**
1. **#26 Simulator Fix** - Unblocks ALL offline testing (13,000:1 leverage)
2. **#57/#63 Free Fights** - Passive XP while we work

---

## Pending Handoffs

### STRAND 1: Simulator Fix (#26) - CRITICAL P0
**Status**: READY FOR NEW WORKER
**Autonomous**: YES
**Est. Time**: 1-2h
**Priority**: HIGHEST - blocks everything

**Problem**: Simulated fights timeout at turn 65, 0 damage. AI files not found by generator.

**ROOT CAUSE** (discovered by previous worker):
- AI files not copied to `tools/leek-wars-generator/ai/`
- LeekScript silently fails with VALUE_EXPECTED parse errors
- No AI code executes → no weapons fire

**SOLUTION** (pattern exists in codebase):
```python
# From scripts/debug_fight.py:268-269 - THIS WORKS
ai1_name, ai1_files = copy_ai_to_generator(ai1_path, ai1_path.name)
```

**Implementation Steps**:
1. Read `scripts/debug_fight.py:20-50` - see working `copy_ai_to_generator()`
2. Extract to shared util OR copy to `src/leekwars_agent/simulator.py`
3. Handle includes: parse `include("...")` lines, copy deps recursively
4. Call copy function before scenario creation in simulator
5. Test: `poetry run python scripts/validate_archetypes.py -n 1 --level 34`

**Success Criteria**:
- ActionUseWeapon events appear in fight logs
- Archetype mirrors produce wins/losses (not all 65-turn draws)
- `scripts/validate_archetypes.py` passes

**Key Files**:
- `scripts/debug_fight.py:20-50` - working copy function
- `src/leekwars_agent/simulator.py:291` - where ai_path is set
- `ais/*.leek` - have includes needing recursive copy

---

### STRAND 2: Garden Automation (#57) - ❌ INVALID - Already Exists
**Status**: ~~Ready for pickup~~ **COMPLETED** (no work needed)
**Assessment Date**: 2026-01-25

**Value**: ~~Free XP from garden solo fights~~ → N/A (garden fights use normal fight budget)

**Finding**: STRAND 2 description was inaccurate.

| Claimed | Actual |
|---------|--------|
| "Free" solo fights | All garden fights consume `fights` budget |
| `/garden/start-solo-fight/{leek_id}` | Requires `leek_id` + `target_id` body params |
| New endpoint needed | Already implemented in `api.py` |

**Already Implemented**:
- `api.get_garden()` - line 92
- `api.get_leek_opponents(leek_id)` - line 98
- `api.start_solo_fight(leek_id, target_id)` - line 116
- CLI: `leek fight run` - automates the complete workflow

**Reference**: `tools/leek-wars/src/component/garden/garden.vue:599-602`
```javascript
LeekWars.post('garden/start-solo-fight', {leek_id: this.selectedLeek.id, target_id: leek.id})
  .then(data => {
    store.commit('update-fights', -1)  // ← Consumes budget!
  })
```

**Conclusion**: No work needed. Garden fight automation already exists.

---

### STRAND 3: Battle Royale (#63) - P2
**Status**: Ready for pickup
**Autonomous**: YES
**Est. Time**: 2h

**Value**: 10 free fights/day from Battle Royale = passive XP.

**Steps**:
1. Study `tools/leek-wars/src/component/battle-royale/` for protocol
2. Identify WebSocket messages for join/spectate
3. Implement BR connection in `api.py` or new module
4. Add CLI command `leek br join`

**Caution**: WebSocket = stateful. May need event loop handling.

---

## Completed Work

### Session 20 (2026-01-25)

- **STRAND 2 (#57) - Garden Automation Assessment** ✅
  - **Finding**: Garden fight automation ALREADY EXISTS
  - `api.start_solo_fight(leek_id, target_id)` implemented at api.py:116
  - CLI command `leek fight run` handles full workflow
  - **No free fights** - garden fights consume normal fight budget
  - **Verdict**: STRAND 2 is INVALID, not incomplete

- **STRAND 1 (#26) - Simulator Fix** ✅
  - **FIXED**: Added `copy_ai_to_generator()` and `extract_includes()` to `simulator.py`
  - Modified `run_scenario()` to copy AI files before running fights
  - Verified: Weapons fire, fights end, archetypes produce wins/losses
  - Usage: `sim.run_1v1("ais/fighter_v11.leek", "ais/archetype_rusher.leek", level=34)`

- **STRAND 1 (#26) - Root Cause Found** (partial)
  - AI files not copied to generator dir → silent parse failure
  - Solution pattern identified in `scripts/debug_fight.py`
  - Implementation pending

---

## Shared Context

### Our Current Build
- Level: 36, Talent: 38
- STR: 310, AGI: 10
- stat_cv: 0.94 (validated as good for long fights!)
- Chips: PROTEIN, MOTIVATION, CURE, BOOTS, FLASH, FLAME
- Weapons: Pistol, Magnum

### PONR Data (disproves "Turn 2.7" claim)
| Level Band | Avg PONR | 80% Threshold |
|------------|----------|---------------|
| L20-39 | 4.58 | Turn 7 |
| L40-59 | 5.57 | Turn 8 |
| L100-119 | 6.75 | Turn 9 |
| L120+ | 8-10 | Turn 12-18 |

### Key Files
| Component | Path |
|-----------|------|
| Simulator | `src/leekwars_agent/simulator.py` |
| Debug Fight | `scripts/debug_fight.py` (has working copy_ai) |
| Archetypes | `ais/archetype_*.leek` |
| Ground Truth | `docs/GROUND_TRUTH.md` |

---

## Small Tasks (grab if blocked)
- [ ] Drain `data/top100_fights.db` queue: `leek scrape top --top 100 --fights-per-leek 20`
