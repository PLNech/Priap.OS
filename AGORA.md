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
| - | STRAND 1 Operations Fix | ⏳ READY | - | #78 + #79 |
| - | STRAND 2 Simulator Fix | ⏳ READY | - | #80 |

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
**Status**: READY FOR WORKER
**Priority**: P0 - Measurement is broken
**Autonomous**: YES

**Goal**: Fix fight logging so we can measure actual WR

**Problems**:
1. Team detection returns None → all fights logged as "D"
2. DB schema missing `status` column → saves fail

**Evidence**:
```
[2026-01-25 20:02:00] [32/32] D vs ElMago [?] (t?, HP:?/?)
Results: 0W-0L-32D (0.0% WR)
DB save failed: table fights has no column named status
```

**Steps**:
1. Read `scripts/auto_daily_fights.py` - find team detection logic
2. Read `src/leekwars_agent/fight_parser.py` - understand how team is determined
3. Read `src/leekwars_agent/scraper/db.py` - check schema definition
4. Compare DB schema: `sqlite3 data/fights_meta.db ".schema fights"`
5. Fix team detection (likely API response parsing issue)
6. Add migration for missing columns
7. Test with `leek fight run -n 1` (ASK ORCHESTRATOR FIRST - costs 1 fight)

**Success Criteria**:
- [ ] `sqlite3 data/fights_meta.db ".schema fights"` shows `status` column
- [ ] Team detection returns 1 or 2, not None
- [ ] Fight result shows W or L, not D (unless actual draw)
- [ ] DB save succeeds without error

**Key Files**:
- `scripts/auto_daily_fights.py` - main automation script
- `src/leekwars_agent/fight_parser.py` - fight parsing logic
- `src/leekwars_agent/scraper/db.py` - DB schema
- `data/fights_meta.db` - actual database

---

### STRAND 2: Simulator Import Fix (#80)
**Status**: ✅ VERIFY
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
| - | - | - |

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
