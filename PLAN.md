# Priap.OS: Road to Top 10

## The Goal
Climb from rank #56,000 to **top 10** on LeekWars ladder.

## The Strategy
Build **infrastructure that lets us iterate faster than anyone else**.

### Core Numbers
| Resource | Daily Limit | Our Capacity |
|----------|-------------|--------------|
| Online fights | 150 | 150 |
| Offline fights | unlimited | 1.8M (21.5/sec) |
| **Leverage ratio** | - | **13,000:1** |

The winner is whoever learns fastest from each fight and tests more variations offline.

---

## Current State (Session 3, 2025-01-02)
- **Level**: ~4 (17 capital available)
- **Rank**: #56,928
- **Record**: 19W-5L (79% win rate)
- **Build**: STR=96, AGI=10, 17 capital SAVED
- **Fights remaining**: ~139 today
- **AI**: fighter_v1.leek deployed

---

## The Scaffolding (Infrastructure to Build)

### 1. Fight History System
**Purpose**: Let Claude see and analyze real fights at scale.

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/fetch_fight.py` | Download fight by ID | TODO |
| `scripts/parse_history.py` | Scrape all fight IDs from history page | TODO |
| `src/leekwars_agent/fight_analyzer.py` | Extract patterns (who shot first, damage efficiency) | TODO |

**Deliverable**: `poetry run python scripts/analyze_fight.py 50863105` → structured insights

### 2. Offline A/B Testing
**Purpose**: Test AI variations at scale before deploying.

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/compare_ais.py` | Run N fights between two AI versions | TODO |
| `scripts/test_builds.py` | Parameter sweep for stat allocation | TODO |

**Deliverable**: `poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000` → win rate comparison

### 3. AI Variant Management
**Purpose**: Track, test, and deploy AI versions systematically.

```
ais/
├── fighter_v1.leek      # Current deployed
├── fighter_v2.leek      # Shoot-first variant
├── variants/            # Strategic variants
└── experiments/         # Throwaway tests
```

### 4. Build Experimentation
**Purpose**: Find optimal capital allocation through data.

**Deliverable**: "At our level, +8 STR gives +3% win rate, +17 AGI gives +5%"

---

## Session 3 Results

### Scaffolding Built ✓
- [x] `scripts/fetch_fight.py` - Download fight by ID
- [x] `scripts/compare_ais.py` - A/B test AIs offline
- [x] `scripts/test_builds.py` - Capital allocation testing
- [x] `scripts/parse_history.py` - Fight history parser
- [x] `src/leekwars_agent/fight_analyzer.py` - Pattern extraction

### Simulator Fixed ✓
- **Issue found**: Team 1 had 96% win rate due to map spawn bias
- **Fix**: Swap teams every other fight (now 50/50)
- **Validation**: v1 vs v1 = 49-47 (perfect balance)

### AI v2 Tested (Shoot-First Logic) ❌
- **Hypothesis**: Shooting before moving would win more fights
- **Result**: 235W-230L (50.5% vs 49.5%) = **NO DIFFERENCE**
- **Why**: Both AIs converge to same behavior:
  - If in range → shoot immediately (both do this)
  - If out of range → move then shoot (both do this)

### Real Problem Identified
Fight 50863105 loss wasn't about shoot-order. It was:
1. **Range timing**: Opponent reached attack range first (Turn 5)
2. **Movement efficiency**: We took longer path to engagement
3. **Positioning**: Starting cells matter more than action order

### Capital Allocation Tested ✓
- **Tested**: +8 STR vs +17 AGI vs +17 Frequency
- **Result**: All exactly 50% win rate (25W-23L each)
- **Conclusion**: With simple AI, stats DON'T matter - strategy does
- **Recommendation**: Save capital until we have better AI

### Key Learnings
1. **Simulator works**: 2.5 fights/sec (not 21.5, but functional)
2. **Scaffolding complete**: Can now A/B test any AI changes offline
3. **Stats are irrelevant**: Until AI is smarter, capital allocation is noise
4. **Real bottleneck**: Movement, positioning, range optimization

### Next Steps
- [ ] Deploy fighter_v1 and run online fights (collect real data)
- [ ] Analyze actual losses to find real improvement areas
- [ ] Save capital for when we have better strategy

### Infrastructure Sprint (main focus)

**Thread A: Fight History**
- [ ] Create `scripts/fetch_fight.py`
- [ ] Fetch fight 50863105 and our other 20 fights
- [ ] Parse into structured format
- [ ] Analyze all 5 losses - find patterns

**Thread B: Offline Testing**
- [ ] Create `scripts/compare_ais.py`
- [ ] Run 1000 fights: v1 vs v2
- [ ] Create `scripts/test_builds.py`
- [ ] Test: baseline vs +8 STR vs +17 AGI

### Then Online Fights
- [ ] Run 50 fights with enhanced data collection
- [ ] Analyze any losses immediately
- [ ] Iterate if needed
- [ ] Run remaining fights

---

## Crafting & Inventory (Later Priority)

LeekWars has a **crafting system**:
- Loot resources from fights
- Combine with recipes to craft inventory items
- Items boost stats (e.g., apple = +100 HP)
- **8 inventory slots** total
- Early game: equip everything you have
- Late game (lvl 80-100+): Must choose builds strategically
- Set inventory on website where you set AI

**Testing**: Can skip leveling and create test fights with custom stats/items

**Current focus**: Simulator and AI optimization
**Later**: Learn optimal crafting paths and build synergies

---

## Capital Strategy

**Decision: SAVE for now.**

| Option | Cost | Benefit | Status |
|--------|------|---------|--------|
| +8 STR (96→104) | 16 cap | More damage | Test first |
| +17 AGI (10→27) | 17 cap | Toward +1 MP | Test first |
| +17 Frequency | 17 cap | Better turn order? | Test first |

After `test_builds.py` experiments, spend based on data.

---

## Phase Roadmap

### Phase 1: Scaffolding (This Session)
- [ ] Fight history parser
- [ ] Offline A/B testing
- [ ] AI v2 with shoot-first
- [ ] Build experiments

### Phase 2: Optimize (This Week)
- [ ] Deploy best AI from testing
- [ ] Spend capital based on data
- [ ] Run 150 fights/day
- [ ] Track rank progression
- [ ] Target: Level 10, Rank <40,000

### Phase 3: Scale (Week 2)
- [ ] Multiple AI variants for different matchups
- [ ] Opponent analysis (what beats us?)
- [ ] Equipment optimization as we level
- [ ] Target: Level 25, Rank <20,000

### Phase 4: Compete (Week 3+)
- [ ] RL training if heuristics plateau
- [ ] Meta adaptation
- [ ] Push for top rankings
- [ ] Target: Level 50+, Top 1000

### Phase 5: Dominate (Month 2+)
- [ ] Top 100 push
- [ ] Tournament participation
- [ ] Advanced strategies
- [ ] Target: Top 10

---

## Key Insights (Session 3)

### Fight 50863105 Analysis (Loss)
```
Us: 37 dmg/shot avg, 3 shots = 111 total
Them: 22 dmg/shot avg, 5 shots = 109 total
Result: We lost by 2 HP
```

**Lesson**: Action economy > raw damage. First strike wins close fights.

### The Flywheel
```
Fight Online → Collect Data → Analyze Losses → Improve AI Offline
     ↑                                                    ↓
     └──────────── Deploy Best Variant ←──────────────────┘
```

---

## Success Metrics

| Metric | Current | Session Target | Week Target |
|--------|---------|----------------|-------------|
| Win rate | 79% | >85% | >90% |
| Rank | #56,928 | <55,000 | <40,000 |
| Level | ~4 | 5+ | 10+ |
| Scaffolding | 0% | Fight history + A/B testing | Complete |
| Capital | 17 unused | Data-driven decision | Optimized |

---

## Daily Commitment
1. **Use all 150 fights** - Non-negotiable
2. **Analyze every loss** - Learn from mistakes
3. **Test offline first** - Never waste online fights on experiments
4. **Iterate daily** - Small improvements compound

The goal isn't perfect AI. The goal is **faster iteration than everyone else**.
