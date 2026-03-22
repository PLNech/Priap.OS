# The Thesis — How IAdonis Wins

> A living strategy document. Updated as data proves or disproves hypotheses.
> Every claim links to evidence. Every change records what we learned.

**Last updated**: Session 37 (2026-03-22)
**Current Talent**: 377 | **Rank**: ~#8200 | **Level**: 130
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

### Current Build (S37)
| Stat | Value | S25 Value | Assessment |
|------|-------|-----------|------------|
| STR | 452 | 452 | Highest in bracket. Diminishing returns vs RES opponents |
| HP | 951 (1051 w/Apple) | 319 | +632 HP. Apple component = free 100 HP |
| RES | **40** | 0 | **S35: First defense investment.** 20 cap → 40 RES (2:1 at tier 0) |
| TP | 14 | 10 | +4 TP. Full rotation fits in one turn |
| MP | 4 | 3 | +1 MP. Minimum kiting capability |
| Capital | **25** | 0 | **25 unspent → RES (still cheap at 2:1 ratio)** |

### What Changed Since S25
- **TP 10→14**: Most impactful stat investment. Unlocks full defense+offense+utility rotation. Motivation gives 16 TP turns.
- **HP 319→692**: Base HP grew with levels. Apple component adds 100.
- **Components (4/8)**: Apple (+100HP), Core (+4 cores), Fan (+40 freq), CD (+40 wis)

### Capital Strategy (0 unspent — all invested)

**S35 decision**: 20 capital → RES. S37: 25 more capital available → RES (50 more pts at 2:1 = RES 90 total).

**Spending curves (verified S35)**:
| Stat | Tier 0-199 | Tier 200-399 | Tier 400-599 | Tier 600+ |
|------|-----------|-------------|-------------|----------|
| STR/WIS/AGI/RES | 1 cap = 2 pts | 1 cap = 1 pt | 2 cap = 1 pt | 3 cap = 1 pt |
| HP | 1 cap = 4 HP (0-999 invested) | 1 cap = 3 HP (1000-1999) | 1 cap = 2 HP (2000+) | — |
| TP | 30/35/40/45/50/.../100 cap per point (progressive, expensive) |
| MP | 20/40/60/80/100/120/140/160/180 cap per point (very expensive) |

**Next capital priority**: Spend 25 cap → +25 RES (40→65). Verified via dry-run: 1 cap = 1 RES at current tier. Then continue to 100-150. STR frozen — diminishing at 2:1 cap/pt. HP secondary.

**S37 Ferocity plan**: Buy Ferocity (147,340 habs, have 151K). Equip replacing Motivation (weakest: only fires turn 1-2 at dist >10). Ferocity (+50% STR for 2t, 1CD) = +226 effective STR during burst window. Hard counters RES-heavy opponents (our 35% WR matchup).

**Capital is atomic** — fractional costs round up. E.g., 5 RES at 0.5 cap/pt = 2.5 → 3 cap → 6 RES.

**Respec still unknown** — if available, moving STR 452→300 into RES/HP would likely transform WR.

### Multi-Leek Strategy (S35)

**AnansAI** (ID: 132531) — L1, T100, 50 capital. Purpose: **cattle-over-pets theory testing.**

| Role | IAdonis | AnansAI |
|------|---------|---------|
| **Mission** | Competitive climber | Build theory lab rat |
| **Build** | Proven attrition (STR 452, RES 40) | Experimental — test hypotheses |
| **Risk** | Conservative — protect talent | Disposable — WR doesn't matter |
| **Data** | High-talent bracket insights | Cross-level insights (L1→converge) |

**Why this matters**:
- **2x online data** — both leeks fight daily, doubling our learning rate
- **Cross-level learning** — AnansAI climbs from L1, generating data across ALL talent brackets. Patterns that hold at T100 AND T369 are universal truths; patterns that diverge reveal bracket-specific meta shifts.
- **Hypothesis isolation** — test RES-heavy, WIS-heavy, or pure-HP builds on AnansAI without risking IAdonis's talent. When a theory proves out, migrate the insight to the main.
- **Farmer fights unlocked** — 2 leeks enables 4v4 farmer fights (separate talent + opponents)
- **Convergence horizon** — as AnansAI levels up, the cross-level data window closes. Maximize diverse experiments early.

**AI deployment**: Same v14 Phalanx initially. Diverge when testing AI variants.

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
| Chip | TP | Level | Cost | Why | Status |
|------|-----|-------|------|-----|--------|
| **Ferocity** | 5 | 107 | 147,340 | +50% STR (2t). Anti-RES answer. STR 452 → 678 effective | **CAN BUY NOW (151K habs)** |
| **Regeneration** | 0 | 122 | ~100K? | 500 HP flat heal, once/fight. Panic button | **Already L130 (eligible)** |
| **Drip** | 2 | 56 | 28,080 | 32 heal, CD 1, 2 uses. Replaces Bandage | After Ferocity |
| **Carapace** | 4 | 141 | ~150K? | 55 abs shield, **1 CD** = permanent armor. Replaces Helmet+Shield, frees 2 slots | L141 (11 levels away) |

### Chip Usage Rules (AI logic)
1. **Defense first**: Helmet → Shield → Armor every turn when off cooldown
2. **Flame**: Primary chip damage, always before Tranq
3. **Tranquilizer**: After Flame — damage before debuff (data: 60% vs 33% WR when reversed)
4. **Motivation**: Turn 1 only, when distance > 10. 4 TP → +6 TP over 3 turns
5. **No pre-attack healing**: 10.8% WR. Cure was removed entirely

---

## AI Behavior Strategy

### v14 "Phalanx" — Move→Attack→Defend Attrition + TP Denial + Lifesteal

```
Turn priority (S36 rework — Move→Attack→Defend):
1. EQUIP weapon (once — b_laser preferred by value/TP)
2. BUFF Motivation if turn 1 and distance > 10
3. SPATIAL + STRATEGY (compute distance, select strategy — NO TP spent)
4. MOVE toward enemy (MP only — free, no TP cost)
5. ATTACK:
   - Distance > 7: weapon-first (b_laser reaches where Flame can't)
   - Distance ≤ 7: Flame → weapon → debuff
6. DEFEND: shields with leftover TP (only if dist ≤ 10)
7. CLEANUP: remaining debuff + attack passes

Special modes:
- STALEMATE (3+ turns no damage): force aggro, no retreat
- KITING DETECTED: override retreat, close distance
- ENDGAME (enemy < 30% HP): all-in attack
```

**S36 rework rationale** ([movement_analysis_s36.md](research/movement_analysis_s36.md)):
- Old Defend→Move→Attack: 67% shield waste, weapon fires 3.5% of turns, only 5.1/14 TP used
- New Move→Attack→Defend: **63.8% WR** vs old over 500 sim fights (strongest delta ever)
- Key insight: movement costs 0 TP (MP only). Moving FIRST gets into range without spending TP. Attack gets full budget. Shields get whatever's left.

### Anti-Patterns (proven failures)
| Pattern | WR | Evidence |
|---------|-----|---------|
| **Defend→Move→Attack turn order** | **36.2%** | **S36, 500 sim fights. Shields eat TP, weapon never fires** |
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

### Current Position (S37)
- **Rank ~#8200** in active leaderboard (~10K active players)
- **T377 band**: Climbing steadily. +15 talent since S36 rework deploy.
- Climbed from ~T89 (S25) to T377 (S37) — **+288 talent in 12 sessions**
- S37 validation: 200 online fights at 48% WR = equilibrium at new bracket (higher opponents).
- S34 scouting: bracket meta is RES 50-200, WIS 100-245. We're catching up on RES.

### What We Beat
- **Glass cannons (STR 400+)**: 64% WR (25 fights, S35) — mirror matchups favor our AI/equipment
- **Zero-RES opponents**: 60% WR (15 fights) — STR 452 punches through
- **Magic users**: 75% WR (4 fights) — small sample but physical build counters MAG
- **WIS 0 opponents**: 69% WR (13 fights) — no heals/debuff resist = easy target

### What Beats Us
- **RES 150+ opponents**: 35% WR (20 fights!) — **40% of our matchups**. Kryptonite confirmed.
- **Summon users**: **31% WR** (16 fights, S35) — collapsed from 64% in S30. Needs investigation.
- **WIS 200+**: 40% WR (15 fights) — heal amplification + debuff resistance
- **Balanced builds (STR 200-300 + RES 150+ + WIS 100+)**: The real meta. We can't break them.

### Online Fight Data (S35, 50 fights, pre-RES baseline)
- **Overall WR**: 50% (25W-24L-1D) — equilibrium for T369
- **vs RES 150+**: 35% WR — **biggest matchup problem (20/50 fights)**
- **vs Summons**: 31% WR — **collapsed from 64% in S30, investigate**
- **vs Glass cannons**: 64% WR — our best matchup
- **Fight duration**: Wins avg 8.2t, Losses avg 10.0t

**Evidence**: [s35_50fight_pre_res_analysis.md](research/s35_50fight_pre_res_analysis.md), [v14_3day_overnight_s30.md](research/v14_3day_overnight_s30.md)

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
- [ ] **Ferocity timing**: **CAN BUY NOW (151K habs > 147K needed).** Replaces which chip slot? (6/6 full)
- [ ] **Is MP 5 worth 80 capital?** More MP = better kiting/positioning, fewer 0-damage stalemates
- [ ] **What's our WR ceiling at T377?** AI-limited (getCooldown/getEffects), equipment-limited (Ferocity), or stat-limited (RES 40)?
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
| S34 | Study top climbers for insights | Ad-hoc scraping wastes API calls. Reusable tools > one-off scripts | Built `leek scout` CLI, scouted 10 opponents |
| S34 | Pure STR is king | STR 452 = highest in bracket, but 5/7 losses had RES 50-200 | **RES 0 is the outlier.** Fumetsu model = balanced |
| S35 | More STR always helps | Diminishing at 2:1 cap/pt. RES at 2 pts/cap = 4x more efficient | **Pivot: all capital → RES.** 20 cap → 40 RES |
| S36 | Shields-first is defensive | 67% shields wasted at dist>10, weapon fires 3.5% of turns | **Move→Attack→Defend: 63.8% WR vs old (500 fights)** |
| S37 | S36 rework works online? | 200 fights: 48% WR at T377 (was T362 pre-rework) | **Confirmed: +15 talent = fighting in harder bracket at equilibrium** |
| S37 | Manual cooldown tracking is fine | `getCooldown(chip)` API exists, 30 ops. Manual tracking can desync | **Replace with API calls — eliminates a whole class of bugs** |

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
| S34 | Build `leek scout` CLI | Reusable opponent intelligence > ad-hoc scraping | scout_leek() + scout_batch() + CLI |
| S34 | Scout 10 loss/win opponents | Need data to inform stat allocation | Analysis: RES 0 = glass cannon, Fumetsu = model |
| S35 | Spend 20 capital on RES (0→40) | Scouting proved RES 0 = biggest weakness. 2:1 ratio = best value | First defense investment. Shield stack now -100 |
| S36 | Rework turn order: Move→Attack→Defend | Movement analysis: 67% shield waste, 3.5% weapon fire rate | **63.8% sim WR over 500 fights** — strongest delta ever |
| S36 | Distance gate + dynamic TP reservation | Shields at dist>10 = wasted. b_laser needs 5 TP reserved | Shields skip when far, weapon always gets TP budget |
| S37 | Validate S36 rework online | 200 fights: 48% WR, T362→T377 (+15 talent) | Rework confirmed: same WR but harder bracket = real improvement |
| S37 | AI audit: manual CD tracking = desync risk | `getCooldown(chip)` exists (30 ops). Manual tracking can diverge | Next: replace manual tracking with API calls |
| S35 | Create AnansAI (2nd leek, 10K habs) | 2x online learning rate + cross-level data + theory isolation | farmer_enabled unlocked, L1 T100 50cap |
