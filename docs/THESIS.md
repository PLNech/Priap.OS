# The Thesis — How IAdonis Wins

> A living strategy document. Updated as data proves or disproves hypotheses.
> Every claim links to evidence. Every change records what we learned.

**Last updated**: Session 47 (2026-04-09)
**Current Talent**: 328 | **Rank**: ~#8404 | **Level**: 146
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

### Current Build (S47)
| Stat | Value | S25 Value | Assessment |
|------|-------|-----------|------------|
| STR | 452 | 452 | Highest in bracket. Diminishing returns vs RES opponents |
| HP | 1099 (999+Apple) | 319 | +780 HP total. Apple component = free 100 HP |
| RES | **219** | 0 | **S35-S39: 25 cap → 219 RES across 4 sessions** |
| TP | 14 | 10 | +4 TP. Full rotation fits in one turn |
| MP | 4 | 3 | +1 MP. Minimum kiting capability |
| Capital | **6** | 0 | **5 from level-up, ~1 residual. RES spend nearly complete** |

### What Changed Since S25
- **TP 10→14**: Most impactful stat investment. Unlocks full defense+offense+utility rotation.
- **HP 319→999**: Base HP grew with levels. Apple component adds 100.
- **RES 0→219**: Major S35-S39 investment. Now above bracket average (meta avg 142 in losses, 84 in wins).
- **Components (4/8)**: Apple (+100HP), Core (+4 cores), Fan (+40 freq), CD (+40 wis)

### Capital Strategy (6 unspent)

**S35→S39**: 45+ capital → RES. S35: RES 0→40. S38: RES 40→66. S39: RES 66→219 (87 capital spend). RES spend now nearing first diminishing-returns boundary (200+).

**Spending curves (verified S35)**:
| Stat | Tier 0-199 | Tier 200-399 | Tier 400-599 | Tier 600+ |
|------|-----------|-------------|-------------|----------|
| STR/WIS/AGI/RES | 1 cap = 2 pts | 1 cap = 1 pt | 2 cap = 1 pt | 3 cap = 1 pt |
| HP | 1 cap = 4 HP (0-999 invested) | 1 cap = 3 HP (1000-1999) | 1 cap = 2 HP (2000+) | — |
| TP | 30/35/40/45/50/.../100 cap per point (progressive, expensive) |
| MP | 20/40/60/80/100/120/140/160/180 cap per point (very expensive) |

**Current capital**: 6 unspent. RES 219 — first tier of diminishing returns approaching. Consider HP or future chip unlocks (Carapace L141, Regeneration L122).

**S38 Ferocity**: Bought (147,340 habs). Equipped, replaced Motivation. **S39**: Replaced by Whip (L119, +60% TP to ally/self, 1CD) — strictly better for solo 1v1 TP management. Ferocity sold or banked.

**Capital is atomic** — fractional costs round up. E.g., 5 RES at 0.5 cap/pt = 2.5 → 3 cap → 6 RES.

**Respec still unknown** — if available, moving STR 452→300 into RES/HP would likely transform WR.

### Multi-Leek Strategy (S35)

**AnansAI** (ID: 132531) — L1, T100, 50 capital. Purpose: **cattle-over-pets theory testing.**

| Role | IAdonis | AnansAI |
|------|---------|---------|
| **Mission** | Competitive climber | Build theory lab rat |
| **Build** | Proven attrition (STR 452, RES 219) | Experimental — test hypotheses |
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

### Equipped (6/6 slots) — Updated S47
| Chip | TP | Role | Since |
|------|-----|------|-------|
| **Flame** | 4 | Primary chip damage (29 dmg, range 2-7) | S1 |
| **Tranquilizer** | 3 | TP denial (50% TP shackle, 1t, 0 CD, 4 uses) | S29 |
| **Whip** | 4 | +60% TP to self/ally (1 turn), CD 1, range 0-6 | S39 |
| **Helmet** | 3 | -15 abs shield (2t, CD 3) | S26 |
| **Shield** | 4 | -20 abs shield (3t, CD 4) | S26 |
| **Armor** | 6 | -25 abs shield (4t, CD 5) | S28 |

**Defense budget**: When all shields active, -60 damage per hit. At TP 14, we apply defense AND offense each turn. Whip on alternating turns bumps effective TP to ~22 every 2 turns.

**Chip history**: Motivation (S1-S38) → Ferocity (S38-S39) → Whip (S39+). Each replaced the weakest turn-1 passive.

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
| **Drip** | 2 | 56 | 28,080 | 32 heal, CD 1, 2 uses. Better than Bandage | **CAN BUY (93K habs)** |
| **Regeneration** | 0 | 122 | ~100K? | 500 HP flat heal, once/fight. Panic button | **Already L146 (eligible!)** |
| **Carapace** | 4 | 141 | ~150K? | 55 abs shield, **1 CD** = permanent armor. Replaces Helmet+Shield, frees 2 slots | L141 — eligible |

### Chip Usage Rules (AI logic)
1. **Defense first**: Helmet → Shield → Armor every turn when off cooldown
2. **Flame**: Primary chip damage, always before Tranq
3. **Tranquilizer**: After Flame — damage before debuff (data: 60% vs 33% WR when reversed)
4. **Whip**: Use early when off CD — TP boost enables bigger attack rotation same turn
5. **No pre-attack healing**: 10.8% WR. Cure was removed entirely

---

## AI Behavior Strategy

### v14 "Phalanx" — Move→Attack→Defend Attrition + TP Denial + Lifesteal (deployed S39)

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

### Current Position (S47)
- **Rank ~#8404** in active leaderboard (~10K active players)
- **T328 band**: Peaked T413 mid-period, fell back. Tournaments = pure talent drain (0% WR).
- Climbed from ~T89 (S25) to T377 (S37) to T413 peak — then T328 after tournament losses.
- **Tournaments disabled** (S39): 0W-14L = 70 talent lost. No upside until AI improves.
- S34 scouting: bracket meta is RES 50-200, WIS 100-245. We're now at RES 219 — above average.

### What We Beat
- **Glass cannons (STR 400+)**: 64% WR (25 fights, S35) — mirror matchups favor our AI/equipment
- **Zero-RES opponents**: 60% WR (15 fights) — STR 452 punches through
- **Aggressive archetypes**: 55% WR (S39, 710-fight analysis)
- **Balanced archetypes**: 56% WR (S39)

### What Beats Us
- **Kiting opponents**: **25% WR** (S39, 710-fight analysis) — our #1 nemesis archetype
- **RES 150+ opponents**: 35% WR (20 fights, S35) — still kryptonite even with our RES 219
- **WIS 200+**: 40% WR — heal amplification + debuff resistance
- **Balanced builds (STR 200-300 + RES 150+ + WIS 100+)**: The real meta. We can't break them.
- **Healer/sustain builds**: ~50% (draws toward stalemate)
- **Persistent nemeses (S39)**: ArrnArchi, TerenceMyleek, GeekOfSmourad, ElCarotte, Spounleek, aarya — all 0W-3L

### Online Fight Data (S39, 710 fights — most recent batch)
- **Overall WR**: 48.2% (342W-350L-18D) over Mar 22–Apr 4
- **Matchmaking only**: 49.1% WR (342W-336L-18D, n=696) — true signal
- **Tournament**: 0% WR (0W-14L, n=14) — **disabled S39, was draining 70 talent**
- **Draws**: 18 total (~1.3/day). Draw rate warrants v15 anti-stalemate work.
- **Archetype WR**: aggro 55%, balanced 56%, **kiter 25%**, healer ~draws

**Evidence**: [project_s39_fight_audit.md](memory/project_s39_fight_audit.md), [s35_50fight_pre_res_analysis.md](research/s35_50fight_pre_res_analysis.md)

### PySim Tournament Results (S47 — 23-AI round-robin, 10,120 fights)
| Rank | AI | ELO | WR% | Notes |
|------|-----|-----|-----|-------|
| #1 | ck_magnum1 | 2237 | 82.3% | Magnum specialist, #1 by ELO |
| #2 | ck_magnum12 | 2198 | 76.6% | Magnum-12 variant |
| #3 | ck_pistol1 | 2037 | 69.4% | Pistol specialist |
| #4 | ck_pistol_sg | 1972 | 66.7% | Pistol-shotgun variant |
| **#5** | **v14** | **1895** | **91.2%** | **803W-3L-74D (8.4% draws!)** |
| #6 | tagada_nn | 1827 | ~55% | #1 ranked player's NN AI |
| #7 | pbondoer | 1726 | ~45% | |
| #8 | ck_flamethrower | 1688 | ~40% | |

**v14 draw sources**: arch_burst `20-20-0`, tagada_nn `21-19-0`, arch_rusher `21-19-0`, ck_magnum_sword `26-14-0`.
**Key finding**: 9/23 AIs broken/passive (0 wins — shup1, galiroe, yaelmagnier, tankyx, chinafred, fauconv, ck_venom_sg, tagada_legacy). True competitive field is ~8 functional AIs. **Draw rate 8.4% is the primary bottleneck** — converting 74 draws to wins is higher leverage than improving wins vs already-losing opponents.

**Evidence**: [pysim_elo_tournament.md](research/pysim_elo_tournament.md)

---

## Open Questions

### Open
- [ ] **Can we respec stats?** Moving STR 452→300 into HP/TP would transform matchups
- [ ] **What controls max_chips?** 6 slots, peers have 9-12. Server-side formula unknown
- [ ] **Is MP 5 worth 80 capital?** More MP = better kiting/positioning, fewer 0-damage stalemates
- [ ] **Carapace (L141) as endgame pivot?** 1 CD = permanent 55 abs shield. Frees 2 chip slots
- [ ] **Draw conversion**: arch_burst 50% draw rate in PySim tournament. v15 all-in mode needed? Detect low DPS by turn 10, drop shields entirely.
- [ ] **Kiter problem at T328**: 25% WR vs kiters (S39). arch_kiter 40W in tournament is static kiter; real kiters adapt. Does tracking distance delta solve it?
- [ ] **Why are 9/23 PySim AIs broken?** OOP dispatch failures, missing mechanics. Fix would give cleaner ELO signal.

### Resolved
- [x] **shouldBuff fix produces buff usage?** Yes — Motivation used consistently with TP 14 budget (S28)
- [x] **What are components?** Craftable items. 4/8 equipped: Apple, Core, Fan, CD (S27)
- [x] **Flash vs Flame priority?** Flame always primary. Flash removed entirely, replaced by Armor (S28)
- [x] **Is Cure useful?** No — 0 heals in 12+ fights. Replaced by Tranquilizer (S29)
- [x] **Ferocity timing**: Bought S38 (147,340 habs). Replaced by Whip S39 — strictly better for solo 1v1.
- [x] **What's our WR ceiling at T377?** Confirmed 48-49% matchmaking WR across S37-S39 (900+ fights). AI+draws are the remaining gap.
- [x] **Tournaments worth it?** No — 0W-14L = 70 talent lost. Disabled S39.

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
| S38 | RES 66 + Ferocity will break RES-heavy matchups | Ferocity bought (147K habs), RES 66. Still 48% WR — no visible jump | Ferocity not enough alone. RES investment is slow (25 cap = 50 pts) |
| S39 | Ferocity is the right chip for burst dmg | Whip (L119, +60% TP) is strictly better for solo 1v1 TP management | **Ferocity → Whip swap.** RES 219 via continued capital spend. Tournaments disabled (0W-14L). |
| S40 | Offline simulator gives reliable WR numbers | S40 audit: sim emits no combat actions — all prior WR estimates were noise | **Sim broken.** Rebuilt from scratch as PySim. |
| S41-S45 | PySim: build a faithful game engine in Python | 60+ APIs, ops model, real maps, OOP support. 19 opponents integrated. | PySim v1 at 5.5 fights/sec. First trustworthy offline WR signal. |
| S46 | 20/21 AIs can run without errors | Runtime error fixes: ternary parse, null coercion, recursion depth, sum builtin | 20/21 AIs error-free. Only tagada_legacy excluded for format issues. |
| S47 | v14 is competitive in PySim tournament | 23-AI round-robin confirmed: v14 ELO 1895 (#5/23), 91.2% WR, **74 draws** | **Draw rate 8.4% = primary bottleneck**. 9/23 AIs broken. True peer set ~8 AIs. |

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
| S38 | Buy Ferocity (147,340 habs) | 710 online fights proved RES opponents are kryptonite; +50% STR addresses it | Equipped, replaced Motivation. RES 40→66 same session |
| S38 | Spend 25 capital on RES (40→66) | Best value at current tier (2 pts/cap). Approaching RES 200 target | RES 66 → continued spend each session |
| S39 | Replace Ferocity with Whip | Whip +60% TP to self (1CD) = more total damage than +50% STR (Ferocity, 2CD). Strictly better 1v1 | Whip deployed. TP budget on Whip turn: effectively 14×1.6 = 22 TP |
| S39 | Disable tournament participation | 0W-14L = 70 talent lost with zero upside at current AI quality | Tournaments off. Matchmaking only: 49.1% WR signal clear |
| S39 | Spend remaining capital on RES | 25 capital → RES 66→219 across S38-S39 | RES 219: above bracket average (meta avg 142 in losses) |
| S40-S45 | Build PySim from scratch | Offline sim proved unreliable (no combat actions). Need trustworthy WR signal | PySim: 60+ APIs, ops model, OOP, real maps, 21-AI tournament |
| S47 | Run 23-AI ELO tournament | Need to understand where v14 stands vs competitive field | v14 ELO 1895 #5/23 (91.2% WR). **74 draws = primary target for v15** |
