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

### Equipped (6/6 slots)
| Chip | Action Log ID | Role | Status |
|------|--------------|------|--------|
| Flame | 10 | Primary damage | OK — 61% WR when sole chip |
| Flash | 7 | AoE damage | PROBLEM — 16% WR when sole chip |
| Protein | 24 | STR buff (+80) | UNUSED — not appearing in fight logs |
| Motivation | 33 | TP buff (+2) | UNUSED — not appearing in fight logs |
| Boots | 30 | MP buff | UNUSED — not appearing in fight logs |
| Cure | 2 | Heal (38 HP) | 93% WR is SURVIVOR BIAS (S26 sim). Heal post-combat at 40% HP |

### Chips To Buy (Priority Order)
| Chip | Why | Level Req | Evidence |
|------|-----|-----------|----------|
| **Helmet** | Flat damage reduction (15, 2t). Every peer has it. | L10 | Opponents with Helmet beat us 71-87% |
| **Shield** | Stronger damage reduction (20, 3t). Every peer has it. | L35 | Same — defensive chips counter our burst |
| **Spark** | No-LOS damage. Opponents using it beat us 63%+ | L19 | Session 25 chip correlation analysis |
| **Bandage** | Secondary heal (23 HP, CD 1). Double healing = sustain | L3 | Peers with dual heals out-sustain us |
| **Solidification** | +180 RES buff (3t). RipInPeace/SmartThing/StockFiish use it | L40 | Peer builds analysis |

### Chip Usage Rules (for AI logic)
1. **Cure**: Post-combat only, HP < 40%. Pre-attack heal at 60% = 10.8% WR (sim-verified catastrophic). 93% WR was survivor bias, not causation.
2. **Flame > Flash**: Always prefer Flame (range 2-7) as primary. Flash as supplement only. Flame-only=61%, Flash-only=16%.
3. **Buffs**: Use turn 1 when distance > 10 (shouldBuff fix deployed). Verify in post-fight logs.
4. **Helmet/Shield** (when bought): Use proactively before taking damage, not reactively.

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
- [ ] **What are components and how do we get them?** Peers have 4-8, we have 0.
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

---

## Decision Log

| Date | Decision | Rationale | Result |
|------|----------|-----------|--------|
| S25 | Backfill 5,327 fights with combat stats | Can't analyze what we can't measure | 18,076 observations enriched, 0 errors |
| S25 | Prioritize Cure fix over new chips | Free (code change), highest expected impact | Pending |
| S24 | Deploy shouldBuff distance fix | Buff when far (>10), attack when close | Deployed, monitoring |
| S23 | Spend 194 capital on STR | Data said STR dominant at our level | STR 452, but now data says it's overkill |
