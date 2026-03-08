# Opponent Analysis — Session 28
*Generated: 2026-03-08 | DB: 5,704 fights, 1,420 IAdonis observations*

## Executive Summary

We have a **47.8% overall win rate** (679W / 741L from observations). The enemy is not a mystery:
opponents we lose to are **HP-richer and talent-heavier**, but the damage differential tells the real story —
we outgun almost everyone in raw damage output yet still lose ~52% of fights.
The battle is decided by **who gets outranged and kited**, not who hits harder.

---

## 1. Opponent Stats: Wins vs Losses

### Core Stats Comparison (all 1,420 fights)

| Metric | When We Win | When We Lose | Delta |
|--------|-------------|--------------|-------|
| **Opponent HP** | 464 | 540 | +76 HP harder |
| **Opponent STR** | 139 | 163 | +24 STR harder |
| **Opponent RES** | 49 | 40 | (higher RES = easier!) |
| **Opponent TP** | 10.19 | 10.27 | minimal |
| **Opponent MP** | 3.31 | 3.37 | minimal |
| **Opponent Talent** | 60 | 97 | **+37 talent gap** |
| **Opponent Freq** | 98 | 98 | same |
| **Opponent WIS** | 43 | 37 | minimal |

Source: JSON `data.leeks` extraction (correct team assignment via `leek_observations.team`).

**Key finding**: HP gap (+76) and talent gap (+37) are the primary separators.
STR gap is modest. **Resistance actually correlates positively with our wins** (more on this below).

### Our Performance: Wins vs Losses

| Metric | When We Win | When We Lose |
|--------|-------------|--------------|
| **Our damage dealt** | 548 | 451 |
| **Opp damage dealt** | 149 | 325 |
| **Our healing** | 12.5 | 12.3 |
| **Our turns alive** | 7.0 | 6.8 |
| **Our AI errors** | 0.20 | 0.36 |
| **Our ops used** | ~1.1M | ~1.6M |

We consistently deal **100 more damage in wins** and receive **176 less damage**.
The damage differential is the fight — it's a race, and we're slow off the line against strong opponents.

---

## 2. Talent Tier Analysis

| Talent Bracket | Fights | Our WR | Avg HP | Avg STR | Avg TP |
|----------------|--------|--------|--------|---------|--------|
| **<50** | 531 | **74.0%** | 445 | 127 | 10.4 |
| **50-100** | 527 | **27.5%** | 524 | 152 | 10.4 |
| **100-150** | 210 | **61.9%** | 627 | 209 | 10.6 |
| **150-200** | 139 | **7.2%** | 719 | 237 | 11.0 |
| **200+** | 13 | **0%** | varies | varies | 13+ |

The brutal non-linearity: **talent 50-100 (27.5% WR) is harder than talent 100-150 (61.9% WR)**.
This counter-intuitive pattern suggests the talent 50-100 bracket contains a lot of low-level leeks
with *chip-heavy* strategies that are hard to burst down, while mid-talent players may have
less-optimized setups.

Talent 150+ is where we truly collapse: **7.2% WR**. These are the players actively grinding.

---

## 3. HP as Barrier

| Opponent HP | Fights | Our WR | Avg Talent |
|-------------|--------|--------|------------|
| **<300** | 129 | **65.1%** | 44 |
| **300-400** | 275 | **58.5%** | 68 |
| **400-500** | 260 | **52.3%** | 69 |
| **500-600** | 256 | **39.1%** | 79 |
| **600-700** | 164 | **45.1%** | 89 |
| **700-800** | 93 | **43.0%** | 109 |
| **800-1000** | 92 | **25.0%** | 161 |
| **1000-1200** | 27 | **25.9%** | 139 |
| **1200+** | 24 | **25.0%** | 126 |

**The cliff is at 500 HP**: we drop from 52.3% to 39.1% WR.
Above 800 HP, we're at ~25% WR regardless of other stats.

Our current HP: **771** (with components). We frequently face opponents with 800-1200 HP
— many at the same talent range. HP investment is non-negotiable.

---

## 4. Resistance — Counterintuitive Result

| RES Bracket | Fights | Our WR | Notes |
|-------------|--------|--------|-------|
| **0** | 576 | 46.9% | Average |
| **1-99** | 298 | 43.3% | Slightly harder |
| **100-199** | 186 | 50.0% | Even |
| **150-199** | 41 | **61.0%** | We win more! |
| **200+** | 101 | **55.4%** | We win more! |

**High-RES opponents do NOT hurt us**. Our STR (452) deals heavy damage even against RES —
the formula in LeekWars is not a flat reduction; high RES with low STR means they deal minimal damage
to us in return. These opponents often go STR-zero and invest entirely in HP+RES,
making them "tanks" whose damage output is negligible. We out-damage them to death.

Deep dive: vs RES 200+ opponents, we deal avg 821 damage in wins vs 798 in losses.
Our damage is *not* the problem against tanks.

---

## 5. TP and MP Analysis

### Opponent TP vs Our WR

| Opp TP | Fights | Our WR |
|--------|--------|--------|
| **10** | 1,050 | **49.5%** |
| **11** | 50 | **32.0%** |
| **12** | 137 | **40.1%** |
| **13** | 14 | **42.9%** |
| **14** | 48 | **47.9%** |
| **15** | 11 | **63.6%** |
| **16** | 8 | 37.5% |

TP=11 (32% WR) and TP=12 (40% WR) hurt us more than TP=14 (47.9%). This suggests
TP=11-12 opponents use that extra TP *efficiently* for burst chips, while TP=14+ may be
running builds that don't convert TP to damage as effectively (or our matchmaking puts us
against weaker TP=14 opponents).

### Opponent MP vs Our WR

| Opp MP | Fights | Our WR |
|--------|--------|--------|
| **3** | 983 | **49.7%** |
| **4** | 231 | **42.4%** |
| **5** | 76 | **38.2%** |
| **6+** | 22 | ~45% |

**MP=5 opponents are hard for us** (38.2% WR). They can control distance, avoid our
Flame/weapon range, and we can't keep up with MP=3. We have MP=4 now but this is still a
gap vs MP=5 opponents.

---

## 6. Opponent Damage Output — The Decisive Metric

| Opp Damage Dealt | Fights | Our WR | Our Avg Damage |
|------------------|--------|--------|----------------|
| **<100** | 227 | **77.1%** | 590 |
| **100-200** | 414 | **49.3%** | 429 |
| **200-300** | 362 | **25.4%** | 412 |
| **300-400** | 113 | **14.2%** | 478 |
| **400-500** | 61 | **19.7%** | 427 |
| **500-600** | 25 | **0.0%** | 443 |
| **600+** | 5 | 20.0% | 522 |

**The clearest signal in the data**: if an opponent deals >200 damage, our WR crashes to 25%.
If they deal >300 damage, we're at 14%. If they deal >500 damage, we're at 0%.

Notably, *we deal MORE damage in 300-500 opp-dmg buckets*, yet still lose. This confirms
fights are often decided by who gets hit first (alpha strike), not cumulative totals.

---

## 7. Fight Duration

| Turns | Fights | Our WR |
|-------|--------|--------|
| **0** | 100 | 48% (no obs = download error) |
| **2-4** | 195 | 43.4% |
| **5** | 293 | 45.4% |
| **6** | 321 | 40.2% |
| **7** | 168 | 53.0% |
| **8** | 122 | 51.6% |
| **9** | 80 | 58.8% |
| **10** | 47 | 59.6% |
| **11** | 39 | 53.8% |
| **12** | 26 | 73.1% |
| **15** | 7 | 85.7% |

**Longer fights favor us**. Short fights (2-6 turns) are bad for us (40-45% WR).
This is consistent with: we have high damage output but take time to reach optimal
range and execute chip rotation. Opponents who burst us in 3-5 turns bypass our setup.

---

## 8. Chip Meta Analysis

### Opponent Chip Usage (template ID → name, our WR when they use it)

| Template | Chip | Uses | Our WR | Threat Level |
|----------|------|------|--------|--------------|
| 19 | **Helmet** | 628 | 46.2% | Medium |
| 9 | **Spark** | 620 | 41.8% | High |
| 1 | **Bandage** | 451 | 51.7% | Low |
| 2 | **Cure** | 341 | 58.4% | Favorable |
| 24 | **Protein** | 304 | 37.8% | High |
| 27 | **Stretching** | 166 | 50.0% | Neutral |
| 18 | **Shield** | 144 | 41.0% | High |
| 21 | **Wall** | 77 | 37.7% | High |
| 6 | **Shock** | 67 | 50.7% | Neutral |
| 15 | **Ice** | 61 | 41.0% | Medium |
| 12 | **Pebble** | 60 | 38.3% | Medium |
| 33 | **Motivation** | 52 | 34.6% | High |
| 10 | **Flame** | 41 | 36.6% | High |
| 40 | **Puny Bulb** | 36 | 47.2% | Neutral |
| 30 | **Leather Boots** | 35 | 34.3% | High |
| 16 | **Stalactite** | 26 | 26.9% | Very High |
| 7 | **Flash** | 16 | 25.0% | Very High |
| 81 | **Knowledge** | 8 | 12.5% | Extreme |
| 61 | **Venom** | 8 | 12.5% | Extreme |
| 38 | **Armoring** | 6 | 0.0% | Extreme |
| 60 | **Solidification** | 4 | 0.0% | Extreme |

**Most threatening single chips** (low count but devastating WR):
- **Knowledge** (81) + **Venom** (61): 12.5% our WR — these are high-level chips used by top players
- **Armoring** (38) + **Solidification** (60): 0% our WR in those fights (small samples, 6-4 fights)
- **Flash** (7): 25% our WR — 16 uses
- **Stalactite** (16): 26.9% our WR

**Knowledge users profile**: 8 fights, avg T413, HP 789, TP 12.9 — top-tier matchmaking bleed.

### Most Dangerous Combos

**Protein (24)** users are our primary problem archetype:
- 304 fights, 37.8% our WR
- Profile: HP 564, STR 197, RES 53, TP 10.7, MP 3.4, avg talent 119
- These players buff STR before attacking — we have no defense against the buff

**Motivation (33)** users:
- 52 fights, 34.6% our WR
- Profile: HP 615, STR 209, RES 48, TP 11.3, avg talent 183

**Wall (21)** users:
- 77 fights, 37.7% our WR
- 9.1% of those fights = we dealt 0 damage (kited completely)

### Our Own Chip Combos and WR

| Our Chips | Fights | Our WR |
|-----------|--------|--------|
| [Flash(7), Flame(10)] | 306 | 49.0% |
| [Flame(10)] only | 261 | 61.3% |
| [Flash(7)] only | 159 | **15.7%** |
| [Flash, Flame, Shield, Helmet, Motivation] | 139 | 54.0% |
| [Flame, Shield, Helmet, Motivation] | 85 | 63.5% |
| [Cure(2), Flash, Flame] | 42 | **92.9%** |
| [Cure, Flame, Shield, Helmet, Motivation] | 23 | 34.8% |

**Flash alone is catastrophically bad** (15.7% WR). Flame alone (61.3%) is our best single chip.
The `[Cure, Flash, Flame]` combo at 92.9% is tantalizing but 42 fights = early AI era,
not representative.

Current v13 loadout `[Flash(7), Flame(10), Shield(18), Helmet(19), Motivation(33)]` = 54% WR in sample.
`[Flame, Shield, Helmet, Motivation]` = 63.5% WR — dropping Flash improves WR.

---

## 9. 0-Damage Losses — The Kiting Problem

We dealt **0 damage in 95 fights** (4.2% of fights dealt 0, 4% WR vs 50.9% when dealing damage).
Of those 95 fights, **91 losses** — essentially automatic defeats.

Profile of 0-damage losses (89 cases, 0 AI errors):
- Avg opponent HP: **472**, STR: 196, RES: 30, TP: 10.8, **MP: 3.8**, Talent: 128
- Avg turns alive: 5.6, Fight duration: 5.6

The elevated MP (3.8 vs typical 3.3) signals **kiting** — they stay out of range.
Wall chip + high MP = we never get close enough to attack.

Opponents in these fights commonly use: `[9,21]` (Spark+Wall), `[9,19,24]` (Spark+Helmet+Protein).

---

## 10. Temporal Trend

| Period | Fights | Our WR | Opp HP | Opp STR | Opp TP | Opp Talent |
|--------|--------|--------|--------|---------|--------|------------|
| S25-S26 (early) | 507 | 47.7% | 432 | 123 | 10.3 | 48 |
| S26-S28 (recent) | 913 | **47.9%** | **582** | **180** | **10.6** | **97** |

Our WR is **essentially flat** (47.7% → 47.9%) despite dramatically harder opponents:
- Opp HP: +150 (35% harder)
- Opp STR: +57 (46% harder)
- Opp Talent: +49 (2× higher)

This means **our AI improvements have kept pace with climbing talent** — we're on the treadmill.
Breaking out requires > proportional improvement.

Our own stats across periods:
- S25-S26: HP 234, STR 310, TP 10, MP 3
- S26-S28: HP 357, STR 365, TP 10, MP 3

We've grown, opponents have grown proportionally.

---

## 11. Tournament Context

18 tournament fights, **11.1% WR** (2W/16L). Opponent profile:

| Talent | HP | STR | RES | TP | MP |
|--------|----|-----|-----|----|----|
| 1012 | 897 | 250 | 265 | 15 | 5 |
| 924 | 897 | 250 | 265 | 15 | 5 |
| 899 | 854 | 0 | 45 | 13 | 6 |
| 851 | 490 | 220 | 60 | 10 | 4 |
| 812 | 763 | 255 | 230 | 12 | 7 |
| 715 | 1024 | 300 | 10 | 17 | 5 |
| 502 | 883 | 421 | 45 | 16 | 5 |

Tournament = top-tier leeks. HP 800-1000, TP 12-17, MP 4-7. We're completely outmatched.
Not a priority data source — only 18 fights.

---

## 12. Frequent Opponents & Nemeses

**Only one opponent we've faced 3+ times with 0% WR**: leek `131825` (3 fights, 0-3, T929, HP761, STR240, RES197, TP13.3).

Most repeat opponents are L20-70 range leeks we cycle through garden fights.
No single opponent dominates our pool — we face a broad variety.

---

## Strategic Recommendations

### A. Build Priorities (Stat Investment)

1. **HP is the #1 lever.** WR cliff at 500 HP, death zone at 800+.
   We are at 771 HP. Target: 1000+ HP. Every HP point matters more than STR past 452.

2. **Do NOT invest in more STR.** We deal 450-800 damage per fight and still lose.
   More STR doesn't fix the problem — opponents outlasting us does.

3. **MP=4 is good, MP=5 is better.** 38.2% WR vs MP=5 opponents suggests mobility gap.
   If capital allows, MP>4 to avoid being kited.

4. **TP=12+ investment.** We're at TP=14 (current). This should be maintained.
   Opponents with TP=11 hurt us more than TP=14 (likely better chip rotations).

### B. Chip Strategy

1. **Drop Flash (chip 7)**. Our WR with Flash-only = 15.7%. Without Flash = 63.5%.
   Flash is a panic button we're misfiring. It should be conditional, not default.

2. **Keep Flame (chip 10)**. 61.3% WR with Flame as core. It's working.

3. **Protein (24) counter**: We lose to Protein users at 37.8% WR. Our AI should
   detect the HP-boost and prioritize killing before they use it (turn 1 aggression
   when close enough, not after they've buffed).

4. **Wall (21) counter**: We deal 0 damage in 9% of fights vs Wall users.
   Need AI improvement: detect Wall placement, navigate around it.

5. **The Motivation(33) threat** (34.6% WR): Opponents who buff TP mid-fight.
   We need to prioritize attacking before their Motivation stack builds.

### C. AI Improvements

1. **Anti-kite logic**: MP=5 opponents + Wall chip = guaranteed loss currently.
   Need pathfinding that aggressively corners opponents rather than moving in straight lines.

2. **Alpha strike priority**: Fights decided in turns 3-5. Our long-fight WR is much higher
   (73% at 12 turns). We need to *survive the early game* and force it to go long.
   This means: buff/shield first turn, then attack — not attack immediately.

3. **Protein detection**: If opponent chip list contains Protein (template 24), front-load
   damage before they buff. This requires reading `getChips(enemy)` and making STR-state decisions.

4. **0-damage prevention**: 89 fights lost without dealing any damage.
   Root cause: kiting + range issues. Flame range is 2-5; if opponent is at cell 6+ away
   and keeps running, we never get off a shot. Need `moveToward` + weapon range validation
   every turn.

### D. Matchmaking Implications

Our talent hovers around T89-T220. The matchmaking pool increasingly contains T150-T200 opponents
where our WR is 7.2%. This is the primary lever: **not fighting these opponents**.

Options:
- Win more vs T<100 opponents (74% WR potential)
- Tournament registration management (avoid T900+ competition)
- Garden fight timing (avoid peak hours with top players)

---

## Appendix: Chip Template Reference

| Template | Name | Notes |
|----------|------|-------|
| 1 | bandage | Heal self |
| 2 | cure | Heal |
| 6 | shock | Damage |
| 7 | flash | Lightning strike (short range) |
| 9 | spark | Teleportation |
| 10 | flame | Fire damage |
| 12 | pebble | Small damage |
| 15 | ice | Ice damage |
| 16 | stalactite | AoE ice |
| 18 | shield | Defense buff |
| 19 | helmet | Defense buff |
| 21 | wall | Block cell |
| 24 | protein | STR buff |
| 27 | stretching | MP buff |
| 30 | leather_boots | MP buff |
| 33 | motivation | TP buff |
| 40 | puny_bulb | Summon |
| 61 | venom | Poison |
| 81 | knowledge | ? (rare, high-level) |
| 38 | armoring | Defense buff |
| 60 | solidification | Defense buff |
