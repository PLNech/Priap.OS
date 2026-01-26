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

## Current Session: 2026-01-26 (Data-Driven Pivot)

### Mission
**Data revealed: opening is our weakness (41% WR), mid-game is strong (60% WR). Pivot accordingly.**

Key insights from fight analysis:
- 48.7% overall WR (74W-78L)
- 5.8 avg fight duration (we're aggro, it works)
- 41% WR in ≤5 turns ← **THE PROBLEM**
- 60% WR in 6-15 turns ← already strong
- 100% opponents "balanced" ← archetype inference broken → FIXED

### Active Workers
| Agent | Task | Status | Started | Notes |
|-------|------|--------|---------|-------|
| Worker 1 | STRAND 4 Data Foundation | ✅ DONE | 2026-01-26 | Archetypes fixed, backfill pending |
| - | STRAND 5 v14 Opening Burst | ⏳ READY | - | Address 41% early WR |

### Blockers
| Agent | Blocker | Needs |
|-------|---------|-------|
| - | - | - |

### Orchestrator Notes

**Current State**: L38, T45, WR 48.7%
**Budget**: 49/50 fights
**Priority**: Data foundation → v14 design → deploy

---

## Open Strands

### STRAND 4: Data Foundation (#83 + #82)
**Status**: READY FOR WORKER
**Priority**: P0 - Blocks analytics
**Autonomous**: YES

**Strategic Context**:
We have TWO fight databases with different schemas. This is confusing and error-prone. The archetype classifier shows 100% "balanced" which is clearly broken. We need clean data to make good decisions.

Fix the foundation before building on it.

**Problems**:
1. Archetype inference returns 100% "balanced" for all 2,819 opponents
2. Can't answer "WR vs kiters" without working archetypes

**DB Architecture** (Orchestrator verified):
- `data/fights.db` = Older fights (133, IDs 50817188-50900766)
- `data/fights_meta.db` = Newer fights (4,392, IDs 51069862-51224667)
- **Zero overlap** — different time periods!

**Action**: Backfill the 133 older fights into `fights_meta.db` via scraper, then deprecate `fights.db`. Don't lose data.

**Investigation Steps**:
1. Extract 133 fight IDs from `fights.db`: `SELECT id FROM fights WHERE id < 90000000`
2. Queue them for scraping: add to `scrape_queue` in `fights_meta.db`
3. Run scraper to backfill: `leek scrape run` or equivalent
4. Verify backfill: count should increase from 4,392 to ~4,525
5. Then fix archetype inference:
   - Check `leek opponent infer --help` and code in `scraper/db.py`
   - Why 100% "balanced"? Never ran? Logic broken? Default never updated?
6. Run inference and verify variety

**Success Criteria**:
- [ ] 133 older fights backfilled into `fights_meta.db`
- [ ] `fights.db` marked as deprecated (or deleted)
- [ ] Archetype distribution shows variety (not 100% balanced)
- [ ] Document in `docs/research/data_architecture.md`

**Key Files**:
- `src/leekwars_agent/db.py`
- `src/leekwars_agent/scraper/db.py`
- `src/leekwars_agent/cli/commands/opponent.py`

---

### STRAND 5: v14 Opening Burst Design (#76)
**Status**: READY FOR WORKER
**Priority**: P1 - WR improvement
**Autonomous**: YES

**Strategic Context**:
Data proves opening is our weakness:
- 41% WR in ≤5 turn fights
- 60% WR in 6-15 turn fights
- 86% of losses end in ≤5 turns

If we survive to turn 5, we win 60% of the time. v14 must maximize opening damage to either win fast or survive to mid-game.

**Problem**:
We're losing the alpha strike. Opponents deal more damage in turns 1-5.

**Design Constraints** (from GROUND_TRUTH.md):
- Turn 1: 10 TP available
- setWeapon costs 1 TP (call once!)
- FLASH: 3 TP, 32±3 dmg, range 1-10
- PROTEIN: 3 TP, +80 STR for 2 turns
- Magnum: 5 TP, 25±15 dmg

**Design Questions**:
1. PROTEIN first (buff then hit) or FLASH first (immediate damage)?
2. Should we always open with chip damage before closing?
3. How do we handle kiters who retreat turn 1?

**Investigation Steps**:
1. Read current v11/v13 opening logic
2. Read nemesis analysis for counter-strategy ideas
3. Draft v14 design doc with turn-by-turn opening sequence
4. Test offline: v14 draft vs archetype_rusher (n=20)
5. Measure: "WR in ≤5 turns" should improve

**Success Criteria**:
- [ ] v14 design doc in `docs/research/v14_design.md`
- [ ] Turn 1-5 sequence documented with TP math
- [ ] Offline test shows improvement over v11 in short fights
- [ ] Ready for deployment decision

**Key Files**:
- `ais/fighter_v11.leek` (current baseline)
- `ais/fighter_v13.leek` (mid-game focus, reference only)
- `docs/research/nemesis_analysis.md`
- `docs/GROUND_TRUTH.md`

---

## Completed This Session

| Strand | Task | Result |
|--------|------|--------|
| STRAND 1 | Operations Fix (#78+#79) | Team detection + DB migration |
| STRAND 2 | Simulator Import (#80) | Use `Simulator` directly |
| STRAND 3 | Test Fight | W vs Peper confirmed, WR measurement works |
| STRAND 4 | Data Foundation (#82+#83) | Archetypes: 197 rusher, 101 kiter, 98 tank (was 100% balanced) |
| - | #74 v13 mid-game | **WONTDO** - data showed mid-game already strong |

---

## Key Learnings This Session

1. **Data beats intuition**: We thought mid-game was weak. Data showed it's 60% WR.
2. **Task definitions matter**: Describe problems, not solutions. Let workers discover.
3. **Two DBs = tech debt**: `fights.db` vs `fights_meta.db` causes confusion.
4. **Archetype inference broken**: 100% "balanced" is clearly wrong.

---

## Shared Context

### Build
- Level: 38, Talent: 45
- STR: 310, AGI: 10, stat_cv: 0.94
- Weapons: Pistol, Magnum, Destroyer (L85 locked)

### Fight Stats (from analysis)
- WR: 48.7% (74W-78L)
- Avg duration: 5.8 turns
- WR by phase: ≤5 turns (41%), 6-15 turns (60%)

### The Strategic Insight
> We're an aggro that wins mid-game. Fix the opening, and 60% WR becomes our floor.
