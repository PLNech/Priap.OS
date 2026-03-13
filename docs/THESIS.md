# The Thesis — How IAdonis Wins

> A living strategy document. Updated as data proves or disproves hypotheses.
> Every claim links to evidence. Every change records what we learned.

**Last updated**: Session 31 (2026-03-13)
**Current Talent**: 333 | **Rank**: #9317 | **Level**: 117
**Target**: T500 (short-term), Top 1000 (medium-term), Top 10 (north star)

---

## Core Belief

**Survivability unlocks damage; sustain closes the deal.** Raw STR only matters if you live long enough to deliver it — and sustain (lifesteal + TP denial) is what turns survival into victory.

Evidence trail:
- S25: Win 62% of fights lasting 9+ turns, only 42% at 4-6 turns → **survival = wins**
- S26: Triple-layer defense (Helmet+Shield+Armor) → v13 beat v12 in sim
- S29: Cure replaced by Tranquilizer → TP denial > unused heal (60% vs 33% WR)
- S30: b_laser lifesteal → 62% sim WR vs pre-b_laser v14 (strongest delta ever)
- S31: RES is kryptonite — avg opponent RES 142 in losses vs 84 in wins

The build has evolved: **glass cannon → defensive attrition → lifesteal attrition fighter**.

---

## Build Philosophy

### Current Build (S31)
| Stat | Value | S25 Value | Assessment |
|------|-------|-----------|------------|
| STR | 452 | 452 | Still high — effective vs 0 RES, wasted vs 150+ RES |
| HP | 692 (792 w/Apple) | 319 | +373 HP. Apple component = free 100 HP |
| RES | 0 | 0 | Unchanged — every opponent invests in it, we don't |
| TP | 14 | 10 | +4 TP. Full rotation now fits in one turn |
| MP | 4 | 3 | +1 MP. Minimum kiting capability |
| Capital | 35 (saving) | 0 | Unspent — waiting for strategic moment |

### What Changed Since S25
- **TP 10→14**: Most impactful stat investment. Unlocks full defense+offense+utility rotation. Motivation gives 16 TP turns.
- **HP 319→692**: Base HP grew with levels. Apple component adds 100.
- **Components (4/8)**: Apple (+100HP), Core (+4 cores), Fan (+40 freq), CD (+40 wis)

### Capital Strategy (35 unspent)
Saving. No immediate spend — diminishing returns on all current options at our level.

| Option | Cost | Gain | Assessment |
|--------|------|------|------------|
| TP 15 | 75 cap | +1 TP | Expensive. Need 40 more capital |
| MP 5 | 80 cap | +1 MP | Expensive. Need 45 more capital |
| HP | 1 cap = 4 HP | Incremental | Best ratio, but 35 cap = 140 HP — marginal |
| STR | 2 cap = 1 STR | Diminishing | Already overkill. Don't. |

**Respec still unknown** — if available, moving STR 452→300 into HP/TP would likely transform WR.

---

## Weapon Strategy

### Equipped (3 weapons)
| Weapon | TP | Range | Damage | Special | Uses/Fight |
|--------|-----|-------|--------|---------|------------|
| **b_laser** | 5 | 2-8 | 50±10 | +50±10 self-heal (lifesteal!) | 3 |
| Laser | 6 | 2-9 | 43±16 | None | 2 |
| Magnum | 5 | 1-8 | 25±15 | None | 2 |

### Weapon Selection (S31 fix)
AI scores weapons by **total effect value per TP** using `getWeaponEffects()`:
- b_laser: (50 dmg + 50 heal) / 5 TP = **20 value/TP**
- Laser: 43 dmg / 6 TP = **7.2 value/TP**
- Magnum: 25 dmg / 5 TP = **5 value/TP**

b_laser is the clear primary. Laser/Magnum are fallbacks when out of b_laser uses or out of range.

**S31 bug found**: Old scoring (`cost * 8`) gave Laser 48 vs b_laser 40 — backwards! b_laser was used in only 1/10 online fights. Fixed.

---

## Chip Strategy

### Equipped (6/6 slots) — Updated S31
| Chip | TP | Role | Since |
|------|-----|------|-------|
| **Flame** | 4 | Primary chip damage (29 dmg, range 2-7) | S1 |
| **Tranquilizer** | 3 | TP denial (50% TP shackle, 1t, 0 CD, 4 uses) | S29 |
| **Motivation** | 4 | +2 TP buff (3 turns). Turn 1 when distant | S1 |
| **Helmet** | 3 | -15 abs shield (2t, CD 3) | S26 |
| **Shield** | 4 | -20 abs shield (3t, CD 4) | S26 |
| **Armor** | 6 | -25 abs shield (4t, CD 5) | S28 |

**Defense budget**: When all shields active, -60 damage per hit. At TP 14, we apply defense AND offense each turn.

### In Inventory
| Chip | Notes |
|------|-------|
| Boots | No self-MP replacement until Winged Boots (L175) |
| Spark | Only no-LOS damage until Arsenic (L285) |
| Bandage | Outclassed by Drip (L56, strictly better) |
| Cure | Removed S29 — 0 heals in 12+ fights |

### Chips To Buy (Priority Order)
| Chip | TP | Level | Cost | Why |
|------|-----|-------|------|-----|
| **Ferocity** | 5 | 107 | 147,340 | +50% STR (2t). Anti-RES answer. At STR 452 → 678 effective |
| **Drip** | 2 | 56 | 28,080 | 32 heal, CD 1, 2 uses. Replaces Bandage |
| **Carapace** | 4 | 141 | ~150K? | 55 abs shield, **1 CD** = permanent armor. Replaces Helmet+Shield, frees 2 slots |
| **Regeneration** | 0 | 122 | ~100K? | 500 HP flat heal, once/fight. Panic button |

### Chip Usage Rules (AI logic)
1. **Defense first**: Helmet → Shield → Armor every turn when off cooldown
2. **Flame**: Primary chip damage, always before Tranq
3. **Tranquilizer**: After Flame — damage before debuff (data: 60% vs 33% WR when reversed)
4. **Motivation**: Turn 1 only, when distance > 10. 4 TP → +6 TP over 3 turns
5. **No pre-attack healing**: 10.8% WR. Cure was removed entirely

---

## AI Behavior Strategy

### v14 "Phalanx" — Defensive Attrition + TP Denial + Lifesteal

```
Turn priority:
1. EQUIP weapon (once — b_laser preferred by value/TP)
2. BUFF Motivation if turn 1 and distance > 10
3. SHIELD: Helmet → Shield → Armor (every turn when off CD)
4. DEBUFF: Tranquilizer on enemy (TP denial)
5. ATTACK:
   - Distance > 7: weapon-first (b_laser reaches where Flame can't)
   - Distance ≤ 7: Flame → weapon
6. MOVE toward enemy (approach target = weapon max range, typically 8)

Special modes:
- STALEMATE (3+ turns no damage): force aggro, no retreat
- KITING DETECTED: override retreat, close distance
- ENDGAME (enemy < 30% HP): all-in attack
```

### Anti-Patterns (proven failures)
| Pattern | WR | Evidence |
|---------|-----|---------|
| Flash as sole damage source | 16% | 159 fights, S25 |
| Never healing (pre-Cure era) | ~48% | 800+ fights |
| Always buff turn 1 (no distance check) | 18% | S24, pre-shouldBuff fix |
| Pure kiting (low STR) | 20% | S4, v3 kiting AI |
| Cure with 0 heal usage | Dead weight | S29, 12+ fights |
| Tranq before Flame | 33% | S29 (vs 60% Flame-first) |
| Stalemate threshold 5 turns | 0-dmg bug | S30, fight #51787170 |
| Weapon scoring by TP cost | b_laser unused | S31, 1/10 fights |
| Hardcoded approach distance (7) | Short of b_laser range 8 | S30 |

---

## Competitive Landscape

### Current Position (S31)
- **Rank #9317** in active leaderboard (~10K active players)
- **T333 band**: Opponents range L50-L257. Level is tiebreaker within talent.
- Climbed from ~T89 (S25) to T333 (S31) — **+244 talent in 6 sessions**

### What We Beat
- **Zero-RES opponents**: Our STR 452 destroys unshielded targets
- **Bulb summoners**: 64% WR (14 fights) — they waste TP on summoning
- **Low-HP opponents**: b_laser lifesteal means we out-sustain

### What Beats Us
- **RES 150+ opponents**: Our damage drops to ~150-285 total over 8+ turns. Kryptonite.
- **HP tanks (1000+)**: Simply outlast us (Pasdbol 1191 HP, LLpeterpan 1028)
- **WIS 200+**: Their heals/buffs are 2-3x stronger than ours (WIS 40)

### Online Fight Data (S30, 50 fights over 3 days)
- **Overall WR**: 52% (26W-24L)
- **vs RES 100+**: ~35% WR (most losses)
- **vs bulb users**: 64% WR
- **vs zero RES**: ~70% WR

**Evidence**: [v14_3day_overnight_s30.md](research/v14_3day_overnight_s30.md)

---

## Open Questions

### Resolved
- [x] **shouldBuff fix produces buff usage?** Yes — Motivation used consistently with TP 14 budget (S28)
- [x] **What are components?** Craftable items. 4/8 equipped: Apple, Core, Fan, CD (S27)
- [x] **Flash vs Flame priority?** Flame always primary. Flash removed entirely, replaced by Armor (S28)
- [x] **Is Cure useful?** No — 0 heals in 12+ fights. Replaced by Tranquilizer (S29)

### Open
- [ ] **Can we respec stats?** Moving STR 452→300 into HP/TP would transform matchups
- [ ] **What controls max_chips?** 6 slots, peers have 9-12. Server-side formula unknown
- [ ] **Ferocity timing**: When to buy (147K habs, ~4 days saving). Is it the RES counter we need?
- [ ] **Is MP 5 worth 80 capital?** More MP = better kiting/positioning, fewer 0-damage stalemates
- [ ] **What's our WR ceiling at T333?** AI-limited, equipment-limited, or stat-limited?
- [ ] **Carapace (L141) as endgame pivot?** 1 CD = permanent 55 abs shield. Frees 2 chip slots

---

## Thesis Evolution

| Session | What we believed | What we learned | What changed |
|---------|-----------------|-----------------|--------------|
| S1-S4 | More STR = more wins | Kiting with low STR = 20% WR | Committed to STR build |
| S14 | Pure STR glass cannon | Capital unspent for 10 sessions | Spent 194 capital on STR |
| S23 | AI quality is secondary | 5 days of data showed 50% WR | Recognized AI as primary lever |
| S24 | SmartThing has 20 cores | API scrape showed cores=1 | Corrected — same cores, different strategy |
| S25 | Our damage should win | Flash-only = 16% WR, Cure = 93% WR | **Survivability > damage** |
| S26 | Buy + equip defensive chips | Helmet+Shield give -35 dmg/hit | Defensive chips every turn, not just buff turns |
| S26 | Sim spawns were wrong (dist 4) | Rewrote to generator formula (dist 18-34) | v12 61.4% vs v11 only visible with correct spawns |
| S28 | Triple-layer defense + TP 14 | Armor + TP investment = full rotation per turn | Flash removed, Armor equipped. TP is king |
| S29 | Cure is essential | 0 heals in 12+ fights = dead weight | Tranquilizer replaces Cure. TP denial > unused heal |
| S30 | b_laser adds sustain | 62% sim WR vs old v14 (strongest delta ever) | Lifesteal weapon = sustain without chip slots |
| S30 | 52% online WR is our ceiling | RES opponents are kryptonite, AI bugs reduce WR | Need Ferocity + AI fixes for next jump |
| S31 | b_laser should dominate | Used in only 1/10 fights — scoring bug! | Fixed: getWeaponEffects() for real value/TP |

---

## Decision Log

| Session | Decision | Rationale | Result |
|---------|----------|-----------|--------|
| S23 | Spend 194 capital on STR | Data said STR dominant at our level | STR 452, later proved overkill |
| S24 | Deploy shouldBuff distance fix | Buff when far (>10), attack when close | Deployed, confirmed working |
| S25 | Backfill 5,327 fights with combat stats | Can't analyze what we can't measure | 18,076 observations enriched |
| S25 | Prioritize Cure fix over new chips | Free (code change), highest expected impact | v12 Asclepius |
| S26 | Buy Helmet+Shield+Spark+Bandage | Every peer has defensive chips, we had none | Equipped, v13 deployed |
| S26 | Swap Protein+Boots for Helmet+Shield | Protein diminishing on 452 STR, Boots UNUSED | 6/6 chip slots: all useful |
| S27 | Craft 4 components | Apple +100 HP, Core +4 cores, Fan +40 freq, CD +40 wis | 4/8 component slots filled |
| S28 | Buy Armor (85,500 Habs), replace Flash | Triple-layer defense; Flash redundant | -60 dmg reduction when all active |
| S28 | Invest capital in TP (10→14) and MP (3→4) | Peer analysis: TP 12-14 universal | Full rotation fits. Game-changing |
| S28 | API overhaul: LeekWarsError + _request() | 45 raw client calls → single gateway | Zero API confusion since |
| S29 | Replace Cure with Tranquilizer | 0 heals in 12+ fights = dead weight | Flame-first/Tranq-last: 60% WR |
| S30 | Buy b_laser (77,490 Habs) | 50 dmg + 50 heal. Strictly dominates Laser | 62% sim WR vs old v14 |
| S30 | Fix stalemate threshold (5→3 turns) | 0-damage oscillation bug in fight #51787170 | Deployed |
| S30 | Build ranking tracker (SQLite) | Can't improve what you can't measure | Baseline: rank #9325 |
| S31 | Fix weapon scoring with getWeaponEffects() | b_laser used 1/10 fights due to cost*8 bug | b_laser now scores 20/TP vs Laser 7.2/TP |
| S31 | Merge master→main + sync branches | GH Actions daemon checked out main (18 commits behind!) | All tooling now deployed to daemon |
