# AGORA - Multi-Agent Coordination Space

> **Workers: READ THIS FIRST, then follow the protocol below.**

## Worker Protocol (MANDATORY)

1. **On task start**: Update "Active Workers" table with your agent name + strand
2. **On each milestone**: Edit your strand section with progress/findings
3. **On blockers**: Add to "Blockers" section immediately
4. **On completion**: Mark strand **VERIFY** (not DONE) - Orchestrator verifies then marks DONE
5. **Commit after each milestone**

**IMPORTANT**: Workers NEVER mark DONE. Only VERIFY. Orchestrator tests and confirms.

---

## Current Session: 2026-01-26 (Cleanup Sprint)

### Mission
**Fix the measurement system before optimizing further.** We discovered:
- Team detection broken → all fights showing as "D"
- DB schema mismatch → saves failing
- Simulator import broken → tooling fragile

### Active Workers
| Agent | Task | Status | Started | Notes |
|-------|------|--------|---------|-------|
| Crush | STRAND 1 Operations Fix | 🔄 VERIFY | 2026-01-26 | #78 + #79 fixed - team detection + DB migration |
| Haiku | STRAND 2 Simulator Fix | ✅ DONE | 2026-01-26 | #80 - use `Simulator` directly |

### Blockers
| Agent | Blocker | Needs |
|-------|---------|-------|
| - | - | - |

### Orchestrator Notes

**Current State**: L38, T39-43 (fluctuating), WR unknown (measurement broken!)
**Budget**: 50/50 fights available
**Priority**: P0 fixes before any new features

---

## Open Strands

### STRAND 1: Operations Fix (#78 + #79)
**Status**: VERIFY (complete)
**Priority**: P0 - Measurement is broken
**Autonomous**: YES

**Goal**: Fix fight logging so we can measure actual WR

**Root Causes Found**:
1. **Team detection**: `leeks1`/`leeks2` can be arrays of integers OR dictionaries - code assumed dicts only
2. **DB schema**: Old `fights.db` was missing columns (`status`, `seed`, `duration`, `fetched_at`) and related tables (`leeks`, `fight_participants`)

**Fixes Applied**:
1. **auto_daily_fights.py:208-242**: Added `get_leek_id()` helper to handle both int and dict formats
2. **src/leekwars_agent/db.py:97-168**: Added schema migration for:
   - `fights` table: `status`, `seed`, `duration`, `fetched_at` columns
   - `leeks` table: `farmer_id`, `farmer_name`, `last_seen` columns  
   - `fight_participants` table: Created with all stat columns

**Success Criteria**:
- [x] DB schema has all required columns (`status`, `seed`, `duration`, `fetched_at`)
- [x] Team detection handles both int and dict formats
- [x] Cancelled fights (winner=-1) handled separately
- [x] DB save succeeds without error

**Files Changed**:
- `scripts/auto_daily_fights.py` - +15 lines (team detection fix)
- `src/leekwars_agent/db.py` - +80 lines (schema migration)
- `src/leekwars_agent/scraper/db.py` - DB schema
- `data/fights_meta.db` - actual database

---

### STRAND 2: Simulator Import Fix (#80)
**Status**: ✅ DONE (verified by Orchestrator)
**Priority**: P1 - Blocks clean tooling
**Autonomous**: YES

**Goal**: Make `from leekwars_agent.simulator import LocalSimulator` work

**Problem**:
```python
ImportError: cannot import name 'LocalSimulator' from 'leekwars_agent.simulator'
```

**Root Cause**: Class was named `Simulator` but import expected `LocalSimulator`

**Fix Applied**: Added `LocalSimulator = Simulator` alias at end of simulator.py

**Evidence**:
```
$ poetry run python -c "from leekwars_agent.simulator import LocalSimulator; print('OK')"
OK

$ poetry run python scripts/compare_ais.py ais/archetype_rusher.leek ais/archetype_kiter.leek -n 3
[... runs successfully ...]
```

**Success Criteria**:
- [x] `poetry run python -c "from leekwars_agent.simulator import LocalSimulator; print('OK')"` succeeds
- [x] `poetry run python scripts/compare_ais.py ais/archetype_rusher.leek ais/archetype_kiter.leek -n 3` still works
- [x] No breaking changes to existing scripts

---

## Orchestrator Reserved

### Investigation: opponent_stats (#81)
Orchestrator will investigate where opponent data actually lives while workers fix the critical path.

---

## Completed This Session

| Strand | Task | Result |
|--------|------|--------|
| STRAND 2 | Simulator Import (#80) | Just use `Simulator` - canonical name, no alias needed |

---

## Shared Context

### Build
- Level: 38, Talent: 39-43 (variance in reports)
- STR: 310, AGI: 10, stat_cv: 0.94
- Weapons: Pistol, Magnum, Destroyer (L85 locked)
- AI Deployed: Unknown (need to verify after fixes)

### Key Files for This Sprint
```
scripts/auto_daily_fights.py     # Fight automation
src/leekwars_agent/fight_parser.py    # Parse fight results
src/leekwars_agent/scraper/db.py      # DB schema
src/leekwars_agent/simulator.py       # Local simulation
data/fights_meta.db                   # Fight database
```

### Verification Protocol (2-Phase)
1. **Worker**: Gather raw evidence, show outputs
2. **Orchestrator**: Review adversarially, confirm PASS/FAIL
