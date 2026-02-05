# Priap.OS Roadmap to Top 10

> **North Star**: Reach Top 10 Leaderboard (Task #1)
> **Current**: Rank ~100k | L42 | T46 | 48% WR

---

## Strategic Phases

```
Phase 1: Foundation     Phase 2: Optimization    Phase 3: Domination
   (NOW)                   (L50+)                    (L100+)
    │                        │                          │
    ▼                        ▼                          ▼
┌─────────┐            ┌─────────┐               ┌─────────┐
│ Fix AI  │ ────────▶  │ Tune AI │ ──────────▶  │ Meta AI │
│ Measure │            │ Iterate │               │ Adaptive│
│ Iterate │            │ Counter │               │ RL/NN   │
└─────────┘            └─────────┘               └─────────┘
     │                      │                         │
     ▼                      ▼                         ▼
  ~50% WR               ~60% WR                   ~70%+ WR
  Rank 50k              Rank 5k                   Top 10
```

---

## Current Sprint (Session 22+)

### 🔴 Immediate (This Week)
| Task | Priority | Status | Notes |
|------|----------|--------|-------|
| #86 Validate v11 fix | P0 | PENDING | Tomorrow's 5x10 batches |
| #75 Buy Laser | P1 | PENDING | +58% damage at L38+ |
| #76 Re-evaluate v14 | P1 | PENDING | May not need if bug was the issue |

### 🟠 Short-term (Next 2 Weeks)
| Task | Pillar | Notes |
|------|--------|-------|
| #77 Solo tournament auto | ⚙️ Ops | Daily 12:00-14:00 CET |
| #59 Tournament participation | ⚙️ Ops | More XP/rewards |
| #9 CI/CD AI validation | 🔧 Infra | Catch bugs before deploy |

### 🟢 Medium-term (Month)
| Task | Pillar | Notes |
|------|--------|-------|
| #33 Study tagadai RL/NN | 🧠 AI | Long-term AI evolution |
| #34 AI simplification | 🧠 AI | Reduce ops, improve clarity |
| #53 Core/Memory upgrades | 🎮 Build | Ops budget for complex AI |

---

## Task Inventory by Pillar

### 🏆 North Star
- **#1** Reach Top 10 Leaderboard

### 🔧 Infrastructure (#0100)
| # | Task | Priority |
|---|------|----------|
| 2 | Infrastructure parent | - |
| 9 | CI/CD AI validation | HIGH |
| 11 | API completeness audit | LOW |
| 12 | Test coverage | MED |
| 13 | Documentation audit | LOW |
| 20 | LeekScript debugger | LOW |
| 23 | Simulator debugging | MED |
| 25 | Fix buy_fights 401 | LOW |
| 64 | Simulator Py4J default | MED |
| 65 | Simulator map seeding | MED |
| 66 | Simulator regression tests | MED |

### 🧠 AI Strategy (#0200)
| # | Task | Priority |
|---|------|----------|
| 3 | AI Strategy parent | - |
| 33 | Study tagadai RL/NN | MED |
| 34 | AI optimization | MED |
| 76 | v14 Opening Burst | RE-EVAL |

### 📊 Data & Analysis (#0300)
| # | Task | Priority |
|---|------|----------|
| 4 | Data parent | - |
| 41 | Fight replay viewer | LOW |
| 43 | Track XP sources | LOW |
| 86 | Validate v11 fix | **HIGH** |

### 🎮 Game Mechanics (#0400)
| # | Task | Priority |
|---|------|----------|
| 5 | Game Mechanics parent | - |
| 50 | L25 build allocation | DONE (we're L42) |
| 52 | Level-up XP curve | LOW |
| 53 | Core/Memory upgrades | MED |
| 75 | Buy Laser | **HIGH** |

### ⚙️ Operations (#0500)
| # | Task | Priority |
|---|------|----------|
| 6 | Operations parent | - |
| 58 | Operational dashboard | LOW |
| 59 | Tournament automation | MED |
| 60 | Fight budget mgmt | LOW |
| 77 | Solo tournament auto | MED |

---

## Milestones

| Milestone | Target | Criteria | Status |
|-----------|--------|----------|--------|
| **M1: Stable Foundation** | Week 4 | 50%+ WR, no silent bugs | 🔄 IN PROGRESS |
| **M2: Optimized AI** | Week 8 | 55%+ WR, adaptive strategy | ⏳ |
| **M3: Tournament Ready** | Week 12 | Auto-tournament, consistent rank-up | ⏳ |
| **M4: Top 1000** | Month 2 | Rank < 1000 | ⏳ |
| **M5: Top 100** | Month 4 | Rank < 100 | ⏳ |
| **M6: Top 10** | Month 6+ | Rank < 10 | ⏳ |

---

## Key Metrics

| Metric | Current | Target M1 | Target M6 |
|--------|---------|-----------|-----------|
| Win Rate | 48% | 52%+ | 65%+ |
| Level | L42 | L50 | L100+ |
| Talent | T46 | T60 | T200+ |
| Rank | ~100k | 50k | Top 10 |
| Daily Fights | 50 | 50 | 150 (packs) |

---

## Lessons Learned (Compounding)

1. **Deploy ≠ Live** - Push to remote before workflow runs
2. **Data > Intuition** - Jermaine was outlier, don't overfit
3. **Silent bugs kill** - Always grep logs for errors
4. **Progressive batches** - 5x10 > 3x17 for safety
5. **Tooling pays off** - CLI improvements save hours

---

*Last updated: Session 21 (2026-01-27)*
