# The Thesis — How IAdonis Wins

> A living strategy document. Updated as data proves or disproves hypotheses.
> Every claim links to evidence. Every change records what we learned.

**Last updated**: Session 25 (2026-02-11)
**Current Talent**: 89 | **Target**: T200 (short-term), T500 (medium-term)

---

## Core Belief

**Survivability unlocks damage.** Raw STR only matters if you live long enough to deliver it. The data proves: we win 62% of fights lasting 9+ turns but only 42% of fights lasting 4-6 turns. Our STR 452 is the highest among peers — but our WR is the lowest.

**Evidence**: [session25_competitive_analysis.md](research/session25_competitive_analysis.md)

---

## Build Philosophy

### Current Build (The Problem)
| Stat | Value | Diagnosis |
|------|-------|-----------|
| STR | 452 | Overkill — 2x any peer, but unused if we die turn 5 |
| HP | 319 | Dangerously low — peers average 500+ |
| RES | 0 | No damage mitigation at all |
| TP | 10 | Minimum viable — peers have 12-14 |
| MP | 3 | Minimum viable — peers have 4-5 |
| Chips | 6 | Half of peers (9-12) |

### Target Build (The Direction)
As capital becomes available, rebalance toward survivability:

**Priority order for new capital** (next ~200 capital):
1. **TP** — more actions/turn = more chip usage = more tactical depth
2. **HP** — survive the turn 5-6 kill window
3. **MP** — positioning flexibility, kiting option
4. **STR** — only after survivability is adequate

**Why not more STR?** Our win data shows STR 452 deals avg 467 dmg in wins — overkill. Opponents die regardless. The bottleneck isn't damage output, it's surviving to deliver it.

**Respec consideration**: If the game allows, moving 100 STR (452→352) into TP+HP would likely boost WR. Even at STR 200 (peer standard), peers achieve T500+.

---

## Chip Strategy

### Equipped (6/6 slots) — Updated S26
| Chip | Template | TP | Role | Status |
|------|----------|-----|------|--------|
| Flame | 5 | 4 | Primary damage (29 dmg, range 2-7) | OK — 61% WR |
| Flash | 6 | 3 | Secondary damage (32 dmg, range 1-10, AoE) | Supplement only |
| Cure | 4 | 4 | Heal (38 HP, CD 2) | Post-combat at 40% HP |
| Motivation | 15 | 4 | +2 TP for 3 turns (net +2 TP gain) | Turn 1 buff when distance > 10 |
| **Helmet** | 21 | 3 | -15 dmg reduction, 2 turns, CD 3 | **NEW S26** — every turn when off CD |
| **Shield** | 20 | 4 | -20 dmg reduction, 3 turns, CD 4 | **NEW S26** — every turn when off CD |

### In Inventory (not equipped)
| Chip | Template | TP | Notes |
|------|----------|-----|-------|
| Protein | 8 | 3 | Swapped out S26 — +80 STR on 452 is diminishing |
| Boots | 14 | 3 | Swapped out S26 — showed UNUSED in fight logs |
| Spark | 18 | 3 | Bought S26 — no-LOS 8 dmg, for future loadout experiments |
| Bandage | 3 | 2 | Bought S26 — 23 HP heal CD 1, for dual-heal loadout |

### Chips To Buy (Next Priority)
| Chip | Why | Level Req | Cost |
|------|-----|-----------|------|
| **Solidification** | +180 RES buff (3t). Top peers use it. | L40 | 24,400 |
| **Wall** | Damage reduction. Stronger than Shield. | L18 | 8,700 |
| **Armor** | Best damage reduction (unlocked at L74!) | L74 | 85,500 |

### Chip Usage Rules (for AI logic)
1. **Cure**: Post-combat only, HP < 40%. Pre-attack heal at 60% = 10.8% WR (sim-verified catastrophic).
2. **Flame > Flash**: Always prefer Flame as primary. Flash as supplement only.
3. **Motivation**: Turn 1 only, when distance > 10 (always true online). 4 TP → +6 TP over 3 turns.
4. **Helmet/Shield**: Use EVERY turn when off cooldown. Not gated by shouldBuff. -35 dmg/hit when both active.

---

## AI Behavior Strategy

### Turn Priority (what the AI should do each turn)
```
1. HEAL if HP < 60% and Cure available
2. BUFF if turn 1 and distance > 10 (Protein → Motivation → Boots)
3. SHIELD if available and not active (Helmet → Shield, when equipped)
4. ATTACK with best available:
   a. Flame (primary damage)
   b. Flash (secondary/AoE)
   c. Weapon (if in range and TP permits)
5. MOVE toward enemy if not in range, away if critically low HP
```

### Anti-Patterns (proven failures)
| Pattern | WR | Evidence |
|---------|-----|---------|
| Flash as sole damage source | 16% | 159 fights, session 25 |
| Never healing | ~48% | 800+ fights without Cure usage |
| Always buff turn 1 (no distance check) | 18% | Session 24, pre-shouldBuff fix |
| Pure kiting (low STR) | 20% | Session 4, v3 kiting AI |

---

## Competitive Landscape

### Our Peer Group (L50-100, T400+)
| Leek | T | Build Archetype | Key Advantage |
|------|---|----------------|---------------|
| LeSuperDavid | 656 | HP tank (1094 HP) | Massive HP pool |
| MeAndYou | 577 | Hybrid (AGI+WIS) | Versatility, 12 chips |
| SmartThing | 557 | Balanced tank (RES+TP) | 14 TP, 9 chips, defensive toolkit |
| StockFiish | 555 | TP specialist (14 TP) | Action economy, 12 chips |
| RipInPeace | 511 | RES tank (100 RES) | Damage mitigation + 12 chips |
| **IAdonis** | **89** | Glass cannon (452 STR) | Raw damage — if alive |

### Universal Patterns Among Peers
- Nobody invests > 300 STR
- Everyone has TP >= 10, most have 12-14
- Everyone has defensive chips (Helmet + Shield minimum)
- Everyone has dual healing (Cure + Bandage)
- 9-12 chips equipped (vs our 6)
- 4-8 components equipped (vs our 0)

---

## Open Questions

- [ ] **Does the shouldBuff fix actually produce buff usage?** Need post-deployment fight log analysis.
- [x] **What are components?** Craftable items giving stat bonuses (Core: +4 cores, Fan: +40 freq, Apple: +100 HP). We have 7 recipes ready, 8 empty slots. They do NOT affect max_chips.
- [ ] **What controls max_chips?** We have 6, SmartThing has 9, both RAM 6. Server-side formula unknown.
- [ ] **Can we respec stats?** Moving STR → TP/HP might be transformative.
- [ ] **What's SmartThing's AI strategy?** Scrape their fight replays for decision patterns.
- [ ] **What causes our AI errors?** 213 errors in losses vs 130 in wins — ops limit? bad positioning?
- [ ] **Is the shouldBuff distance threshold (>10) optimal?** Could be tuned with sim.

---

## Thesis Evolution

| Session | What we believed | What we learned | What changed |
|---------|-----------------|-----------------|--------------|
| S1-S4 | More STR = more wins | Kiting with low STR = 20% WR | Committed to STR build |
| S14 | Pure STR glass cannon | Capital unspent for 10 sessions | Spent 194 capital on STR |
| S23 | AI quality is secondary | 5 days of data showed 50% WR | Recognized AI as primary lever |
| S24 | SmartThing has 20 cores | API scrape showed cores=1 | Corrected — same cores, different strategy |
| S25 | Our damage should win | Flash-only = 16% WR, Cure = 93% WR | **Survivability > damage. Chip usage is THE lever.** |
| S26 | Buy + equip defensive chips | Helmet+Shield give -35 dmg/hit. v13 sim 51.2% vs v12 | Defensive chips used EVERY turn, not just buff turns |
| S26 | Sim spawns were wrong (dist 4) | Rewrote to generator quadrant formula (dist 18-34) | v12 61.4% vs v11 only visible with correct spawns |

---

## Decision Log

| Date | Decision | Rationale | Result |
|------|----------|-----------|--------|
| S25 | Backfill 5,327 fights with combat stats | Can't analyze what we can't measure | 18,076 observations enriched, 0 errors |
| S26 | Buy Helmet+Shield+Spark+Bandage (20,960 Habs) | Every peer has defensive chips, we had none | Equipped, v13 deployed |
| S26 | Swap Protein+Boots for Helmet+Shield | Protein (+80 STR on 452 = diminishing), Boots UNUSED | Loadout: Flame/Flash/Cure/Motivation/Helmet/Shield |
| S25 | Prioritize Cure fix over new chips | Free (code change), highest expected impact | Completed — v12 Asclepius |
| S24 | Deploy shouldBuff distance fix | Buff when far (>10), attack when close | Deployed, monitoring |
| S23 | Spend 194 capital on STR | Data said STR dominant at our level | STR 452, but now data says it's overkill |
