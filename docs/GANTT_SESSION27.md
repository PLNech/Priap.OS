# Priap.OS — Strategic Roadmap (Session 27)

> Generated 2026-02-20 | L79 T106 | 44% WR (last 50) | 31 capital unspent
> North Star: Top 10 Leaderboard (#0001)

## Current Position

```
TALENT LADDER    You are here
     ↓               ↓
T50 ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ T600
                 T106                    Peers: T511-656
                 L79                     Peers: L50-96
                 44% WR                  Need: >55%
```

## Gantt — 4 Phases to Top 10

```
SESSION    27    28    29    30    31    32    33    34    35   ...   50+
           ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼──────┤

PHASE 1: STOP THE BLEEDING (S27-S28)                    ◄── YOU ARE HERE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #0400 Spend 31 capital
           ██                                            Build: TP/HP/RES
  #0208 v14 AI: TP-aware combat
           ████                                          Leverage new TP
  #0300 Analyze v13 losses
           ██                                            Why 33% at L79?
  #0504 Health dashboard
           ░░██                                          Track WR trends

PHASE 2: INFRASTRUCTURE (S29-S32)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #0103 CI/CD: validate before deploy
                 ████                                    Never deploy blind
  #0106 Test coverage
                 ░░████                                  Safety net
  Py4J simulator (#64)
                 ████                                    2x sim speed
  Sim regression tests (#66)
                     ████                                Sim trustworthiness
  #0116 LeekScript debugger
                         ████                            Debug AI logic
  #0105 API completeness
                     ░░██                                Unlock new actions

PHASE 3: INTELLIGENCE (S32-S38)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Study SmartThing replays
                         ████                            What does T557 DO?
  #0306 XP income sources
                         ██                              Faster leveling
  #0405 Level-up XP curve
                           ██                            Plan stat growth
  #0406 Core/Memory upgrades
                           ████                          More ops = smarter AI
  #0119 Sim introspection
                             ████                        See WHY AI decides

PHASE 4: SINGULARITY (S38+)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #0207 RL/NN training (tagadai)
                                     ████████████        ML-trained AI
  Archetype counter-play
                                         ████████        Rock-paper-scissors
  Adaptive AI (opponent profiling)
                                             ████████    Read & react
  #0001 TOP 10
                                                     ★   The summit
```

## Phase 1 Detail — The Burning Platform

**Problem**: 44% WR and falling. Matchmaker pairs us with tougher opponents as we level.
Our glass-cannon build (STR 452, HP 334, TP 10, MP 3) is outclassed.

**Immediate Actions (this session)**:

| # | Task | Capital/Cost | Expected Impact |
|---|------|-------------|-----------------|
| 1 | Spend 31 capital (TP? HP? RES? RAM?) | 31 capital | +1 stat tier |
| 2 | Analyze v13 fight logs — are Helmet/Shield firing? | Free | Verify S26 work |
| 3 | Create v14 with TP-awareness (if we buy TP) | Free | Exploit new stats |
| 4 | A/B test v14 vs v13 in sim (500+ fights) | Free | Prove improvement |

**Capital Decision Tree**:
```
                    31 CAPITAL
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
       +1 TP (30)   +124 HP (31)  +1 RAM (20) + HP
       TP 10→11     HP 334→458    RAM 6→7 + 44 HP
           │            │            │
     More actions   Survive 1-2   MAYBE unlock
     per turn       extra hits    7th chip slot
           │            │            │
     Needs v14 AI   Passive gain  High risk/reward
     to exploit     (no AI edit)  (unknown formula)
```

## Dependencies (Critical Path)

```
Spend Capital ──→ v14 AI (if TP) ──→ Deploy + Monitor ──→ WR > 50%?
      │                                                        │
      └── Analyze v13 losses (parallel) ──────────────────────┘
                                                               │
CI/CD (#0103) ──→ Sim Tests (#66) ──→ Safe iteration ─────────┘
                                                               │
Py4J (#64) ──→ Faster sims ──→ More A/B tests ────────────────┘
                                                               │
SmartThing study ──→ Archetype insights ──→ Counter-play ──────┘
                                                               │
                                                          TOP 10 ★
```

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| max_chips stuck at 6 | HIGH | Test RAM→7 hypothesis. If false, need level/unknown mechanic. |
| TP too expensive (30 cap) | MEDIUM | HP gives more value per capital. Consider HP-heavy build. |
| v13 AI has bugs | MEDIUM | Analyze fight logs for errors, verify chip usage. |
| Sim ≠ Online gap | HIGH | Sim has 93% team1 bias. Trust comparative results only. |
| Level-up = harder opponents | INHERENT | Must improve WR faster than matchmaker difficulty. |

## Key Metrics to Track

| Metric | Current | S28 Target | S32 Target | Top 10 |
|--------|---------|-----------|-----------|--------|
| Talent | 106 | 150 | 300 | 1000+ |
| WR (50-fight) | 44% | 52% | 55% | 60%+ |
| Level | 79 | 85 | 100 | 200+ |
| Chips equipped | 6 | 7? | 9 | 12 |
| AI errors/fight | ~1.5 | <0.5 | 0 | 0 |
