# Gantt — IAdonis Roadmap (S30+)

> From T333 to Top 10. As Archimedes said: "Give me a lever long enough and I shall move the world."
> Our lever is data. The world is the leaderboard.

**Current state**: L117 | T333 | STR 452 | TP 14 | MP 4 | HP 692 | Habs 111,990 | Capital 35

## Critical Path

```
                    March                         April                          May
         W2          W3          W4          W1          W2          W3
    ─────┬───────────┬───────────┬───────────┬───────────┬───────────┬──────→

 🔧 INFRA
    ├─[████] Fix daemon crash (S30) ✓
    ├─[████] Fix analyzer filter (S30) ✓
    ├─[████] Add ActionCode/FightContext enums (S30) ✓
    ├─[░░░░] CI/CD: validate AI before deploy (#0103)
    ├─[░░░░░░░░] Py4J simulator as default (#64)
    └─[░░░░░░░░░░░░] Operational dashboard (#0504)

 🎮 EQUIPMENT (immediate ROI — every purchase compounds via overnight fights)
    ├─[████] Buy b_laser (77K habs) ─────────────────────────────→ v15 integration
    ├─[██░░] Buy Drip (28K) ──────→ equip if chip slot found
    ├─[░░░░░░░░░░░░] Save for Ferocity (147K, ~2 weeks) ────────→ +226 STR buff
    └─[░░░░░░░░░░░░░░░░░░░░░░] Carapace (L141, 205K) ──────────→ replaces Helmet+Shield

 🧠 AI STRATEGY (highest WR impact per hour invested)
    ├─[░░░░] v15: Fix 0-damage kiting bug (CRITICAL) ───────────→ eliminate guaranteed losses
    ├─[░░░░░░] v15: Integrate b_laser (attack+heal) ────────────→ sustain in long fights
    ├─[░░░░░░░░] v15: Anti-RES strategy (magic dmg? Ferocity?) ─→ beat 200+ RES opponents
    ├─[░░░░░░░░░░] v16: Adaptive archetype detection ───────────→ counter-play per opponent
    └─[░░░░░░░░░░░░░░░░░░] Study RL/NN from tagadai (#0207) ───→ learning AI

 📊 DATA & ANALYSIS (compounds over time)
    ├─[████] 3-day overnight analysis (S30) ✓
    ├─[░░░░] Fight scraper: expand to peer builds
    ├─[░░░░░░░░] XP curve analysis (#0405) ──→ optimize leveling
    └─[░░░░░░░░░░░░] Competitive intel: top 100 meta analysis

 ⚙️ STATS & BUILD
    ├─[░░░░] Spend 35 capital (HP or save for MP 5)
    ├─[░░░░░░░░░░░░] Level to 122 → Regeneration (135K)
    ├─[░░░░░░░░░░░░░░░░] Level to 141 → Carapace (205K)
    └─[░░░░░░░░░░░░░░░░░░░░░░] Respec evaluation (STR→TP/HP?)
```

## Dependency Graph

```
 Fix daemon crash ──────┐
                        ├──→ Reliable overnight fights ──→ Habs income ──→ Equipment purchases
 Fix analyzer filter ───┘                                      │
                                                                ├──→ Buy b_laser
                                                                │       │
                                                                │       └──→ v15: b_laser integration
                                                                │               │
 Fix kiting bug ────────────────────────────────────────────────┼───────────────┤
                                                                │               │
                                                                │               └──→ Deploy v15
                                                                │                       │
                                                                ├──→ Buy Ferocity ──────┤
                                                                │                       │
                                                                │                       └──→ v16: adaptive
                                                                │
                                                                └──→ Buy Drip (if slot)
```

## Phase Plan

### Phase 1: Quick Wins (S30 — THIS SESSION)
- [x] Fix daemon crash (list vs dict)
- [x] Fix analyzer context filter
- [x] Add ActionCode/FightContext enums
- [x] Analyze 3-day results (52% WR confirmed)
- [ ] **Buy b_laser** (77,490 habs — ready now!)
- [ ] Spend 35 capital on HP (+140 HP → 932 w/Apple)
- [ ] Update THESIS.md

### Phase 2: v15 AI (S31, target: March 15-16)
- [ ] Fix 0-damage kiting bug (anti-kite fallback)
- [ ] Integrate b_laser (attack + self-heal)
- [ ] Target prioritization (main leek > bulbs)
- [ ] Sim validate: v15 vs v14 (500 fights, expect >55%)
- [ ] Deploy, run 20+ online fights, analyze

### Phase 3: Economy (S31-S33, ~2 weeks)
- [ ] Save for Ferocity (need 147K, ~10 days of fights)
- [ ] Buy Drip if chip slot available (28K)
- [ ] CI/CD pipeline for AI validation
- [ ] Evaluate respec: STR 452→300 + TP/HP

### Phase 4: Scaling (S34+, April)
- [ ] Ferocity integration (+50% STR buff)
- [ ] v16: Adaptive opponent classification
- [ ] Py4J simulator (faster iteration)
- [ ] Target: T500+, top 5K

### Phase 5: Endgame (May+)
- [ ] Level 141 → Carapace (permanent armor, replaces Helmet+Shield, frees 2 chip slots)
- [ ] Level 175 → Winged Boots (self-MP chip)
- [ ] RL/NN AI exploration
- [ ] Target: T1000+, top 1K

## Revenue Model

| Source | Habs/day (est) | Notes |
|--------|----------------|-------|
| 50 fights × ~2000 habs/fight | ~100,000 | Main income |
| Battle Royale (10/day) | ~10,000 | Passive daemon |
| Tournament prizes | Variable | Weekly |

**Time to Ferocity (147K)**: ~1.5 days of fights from 0 habs
**Time to Carapace (205K)**: ~2 days of fights from 0 habs

> The bottleneck isn't habs — it's LEVEL (for unlocking chips) and AI QUALITY (for WR).

## Milestones

| Target | Current | ETA | Blocker |
|--------|---------|-----|---------|
| T400 | T333 | ~1 week | v15 AI quality |
| T500 | T333 | ~2-3 weeks | Ferocity + v15 |
| Top 5K | Top 10K | ~1 month | Equipment + AI |
| Top 1K | Top 10K | ~2-3 months | Level + Carapace |
| Top 10 | Top 10K | ~6+ months | Everything + meta mastery |
