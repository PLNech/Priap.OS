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
|| Agent | Task | Status | Started | Notes |
||-------|------|--------|---------|-------|
|| Worker 1 | STRAND 4 Data Foundation | ✅ DONE | 2026-01-26 | Archetypes fixed, backfill pending |
|| **Worker 2** | **STRAND 5 v14 Opening Burst** | 🔨 **VERIFY** | 2026-01-26 | Tests passing - deploy ready |

### Blockers
|| Agent | Blocker | Needs |
||-------|---------|-------|
|| - | - | - |

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
**Status**: 🔨 **VERIFY** (Tests passing - ready for orchestrator verification)
**Priority**: P1 - WR improvement
**Autonomous**: YES

**Strategic Context**:
Data proves opening is our weakness:
- 41% WR in ≤5 turn fights
- 60% WR in 6-15 turn fights
- 86% of losses end in ≤5 turns

If we survive to turn 5, we win 60% of the time. v14 must maximize opening damage to either win fast or survive to mid-game.

**Implementation Complete**:
- `ais/v14_opening.leek` - NEW opening burst module (FLASH + weapon turn 1)
- `ais/fighter_v14.leek` - Main AI with v14 opening + v11 mid-game
- `docs/research/v14_design.md` - Design document with TP math

**Test Results** (20 fights each, fair comparison with turn/map swap):
| Matchup | v14 WR | Wins | Fights |
|---------|--------|------|--------|
| vs Rusher | **100%** | 16 | 20 |
| vs Kiter | **72%** | 13 | 20 |
| vs v11 (baseline) | **56%** | 9 | 20 |

**Analysis**:
- FLASH opener gives us guaranteed 32 damage turn 1
- v11's movement logic handles kiter pursuit (reserve 1 MP)
- Aggressive opening dominates rushers, improves vs kiters

**Key Improvements Over v11**:
- Turn 1: FLASH (32 dmg) + weapon (~15 dmg) = ~47 damage vs ~0 damage
- Turn 2-3: Sustained pressure with full TP
- Falls through to v11 mid-game logic for positioning

**Success Criteria**:
- [x] v14 design doc in `docs/research/v14_design.md`
- [x] Turn 1-5 sequence documented with TP math
- [x] Offline test shows improvement (72% vs kiters, 56% vs v11)
- [ ] **Ready for DEPLOYMENT DECISION**

**Key Files**:
- `ais/v14_opening.leek` - New opening burst module
- `ais/fighter_v14.leek` - Main AI with v14 opening
- `docs/research/v14_design.md` - Design document
- `docs/research/nemesis_analysis.md` - Counter-strategy ideas
- `docs/GROUND_TRUTH.md` - TP costs and chip stats

---

## Completed This Session

|| Strand | Task | Result |
||--------|------|--------|
|| STRAND 1 | Operations Fix (#78+#79) | Team detection + DB migration |
|| STRAND 2 | Simulator Import (#80) | Use `Simulator` directly |
|| STRAND 3 | Test Fight | W vs Peper confirmed, WR measurement works |
|| STRAND 4 | Data Foundation (#82+#83) | Archetypes: 197 rusher, 101 kiter, 98 tank (was 100% balanced) |
|| - | #74 v13 mid-game | **WONTDO** - data showed mid-game already strong |
|| STRAND 5 | v14 Opening Burst | **VERIFY** - 100% vs rusher, 72% vs kiter, 56% vs v11 |

---

## Key Learnings This Session

1. **Data beats intuition**: We thought mid-game was weak. Data showed it's 60% WR.
2. **Task definitions matter**: Describe problems, not solutions. Let workers discover.
3. **Two DBs = tech debt**: `fights.db` vs `fights_meta.db` causes confusion.
4. **Archetype inference broken**: 100% "balanced" is clearly wrong.
5. **FLASH opener works**: 32 guaranteed damage turn 1 improves win rate significantly.

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