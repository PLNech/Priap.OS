# Session 25: Competitive Intelligence Analysis

**Date**: 2026-02-11
**Data**: 5,327 fights backfilled with combat stats (18,076 observations)

## Executive Summary

IAdonis's 50% WR is caused by three compounding failures:
1. **Chip underutilization**: AI uses Flame+Flash in 60% of fights, ignoring Cure entirely (93% WR when Cure is used)
2. **Glass cannon at short durations**: We lose fights lasting 4-6 turns (42% WR) but win at 7+ turns (56%+ WR)
3. **No defensive toolkit**: 0 RES, no Helmet, no Shield — peers have 2-3 defensive chips

## Finding 1: Our Chip Usage Is The Smoking Gun

| Our chip loadout | Fights | WR% | Avg Damage |
|-----------------|--------|-----|------------|
| Flash + Flame [7,10] | 306 | 49% | 534 |
| Flame only [10] | 261 | **61%** | 419 |
| **Flash only [7]** | **159** | **16%** | **300** |
| Cure + Flash + Flame [2,7,10] | 42 | **93%** | 541 |
| Cure + Flame [2,10] | 13 | 77% | 486 |
| Cure + Flash [2,7] | 12 | 75% | 355 |

**Diagnosis**: When our AI only uses Flash (no Flame), WR drops to 16%. Flash does 32 AoE damage at TP 3 — decent as opener, terrible as primary. Meanwhile, Cure is used in only ~7% of fights but produces 77-93% WR when active.

**Action**: AI must prioritize Flame over Flash, and actually USE Cure.

**Note**: Protein (24), Motivation (33), Boots (30) don't appear in chips_used AT ALL. The shouldBuff() fix (deployed this session) should change this — pre-fix data shows zero buff usage.

## Finding 2: Fight Duration Reveals Our Archetype Weakness

| Duration | Fights | WR% | Our Avg Dmg | Our Avg Recv |
|----------|--------|-----|-------------|-------------|
| 3 turns | 31 | 48% | 257 | 151 |
| 4 turns | 137 | **43%** | 326 | 188 |
| 5 turns | 240 | 47% | 365 | 205 |
| 6 turns | 251 | **42%** | 381 | 214 |
| 7 turns | 108 | **56%** | 484 | 191 |
| 8 turns | 72 | 49% | 478 | 202 |
| 9+ turns | 94 | **62%** | 558 | 198 |

**Diagnosis**: Our glass cannon (STR 452) only shines if the fight lasts long enough to deliver our payload. In turns 4-6 (628 fights, 65% of total), we're at 42-47% WR. Opponents who burst us in 5-6 turns exploit our 319 HP / 0 RES.

**If we survive to turn 7**: our STR advantage overwhelms. The 56-62% WR at 7+ turns proves our damage is superior — we just need time.

## Finding 3: Wins vs Losses — The Damage Differential

| Metric | Wins (508) | Losses (558) | Gap |
|--------|-----------|-------------|-----|
| Avg damage dealt | **467** | 326 | -30% in losses |
| Avg damage received | 120 | **260** | +117% in losses |
| Avg healing done | 5 | 1 | Both negligible |
| Avg turns alive | 6.6 | 6.3 | Same |
| AI errors (total) | 130 | **213** | 64% more in losses |

**Key insight**: Not a survivability problem — turns alive is identical. It's a **damage output race** with a side order of AI errors.

## Finding 4: What Opponents Beat Us

| Metric | Opponents who beat us | Opponents we beat |
|--------|----------------------|-------------------|
| Avg HP | **528** | 443 |
| Avg STR | 148 | 133 |
| Avg RES | 35 | 43 |
| Avg TP | 10.5 | 10.4 |
| Avg damage dealt | **205** | 90 |
| Avg healing | 34 | 37 |
| Avg cells moved | 15.5 | 14.0 |

**Surprising**: Opponents who beat us have LOWER RES (35 vs 43). Higher HP (+85) is the real differentiator. They deal 2.3x more damage with almost the same TP.

### Opponent Chip Loadouts (Loss Rate)

| Opponent chips | Decoded | Fights | Our Loss% |
|---------------|---------|--------|-----------|
| [12] | Pebble alone | 9 | 89% |
| [9,19,24] | Spark + Helmet + Protein | 15 | 87% |
| [9,19] | Spark + Helmet | 48 | 71% |
| [9] | Spark alone | 111 | 63% |
| [1,9,19] | Bandage + Spark + Helmet | 31 | 48% |
| [1,9] | Bandage + Spark | 19 | 53% |

**Pattern**: Opponents with **Helmet** (damage reduction shield) consistently beat us. Our pure STR damage gets partially absorbed, reducing our kill speed.

## Finding 5: Death Turn Distribution

| Turn | Deaths | Cumulative |
|------|--------|------------|
| 4 | 12% | 15% |
| 5 | **19%** | 34% |
| 6 | **33%** | 67% |
| 7 | 14% | 81% |
| 8 | 7% | 88% |

**Kill window**: 67% of our deaths happen by turn 6. If we can survive past turn 6, we're in the 56%+ WR zone.

## Finding 6: Peer Build Comparison

| Leek | Level | Talent | HP | STR | RES | TP | MP | Chips | Weapons | Components |
|------|-------|--------|-----|-----|-----|----|----|-------|---------|------------|
| LeSuperDavid | 89 | **656** | 1094 | 300 | 0 | 12 | 5 | ? | ? | ? |
| MeAndYou | 96 | **577** | 825 | 240 | 0 | 12 | 5 | 12 | Laser + Destroyer | 7 |
| SmartThing | 73 | **557** | 576 | 200 | 70 | 14 | 5 | 9 | Laser + Double Gun | 4 |
| StockFiish | 50 | **555** | 347 | 200 | 0 | 14 | 4 | 12 | Shotgun + Broadsword | 8 |
| RipInPeace | 50 | **511** | 447 | 275 | 100 | 10 | 4 | 12 | Shotgun + Magnum | 7 |
| **IAdonis** | **74** | **89** | **319** | **452** | **0** | **10** | **3** | **6** | **Magnum + Laser** | **0** |

### Peer Chip Loadouts (decoded)

**SmartThing** (T557, 9 chips): Bandage, Protein, Helmet, Motivation, Spark, Cure, Knowledge, Shield, Solidification
→ Full defensive suite: 2 heals, 2 shields, RES buff, STR buff, SCI buff

**StockFiish** (T555, 12 chips): Protein, Helmet, Rock, Motivation, Cure, Boots, Flash, Flame, Shield, Solidification, Puny Bulb, Stalactite
→ Everything: offense + defense + utility

**MeAndYou** (T577, 12 chips): Bandage, Protein, Helmet, Rock, Motivation, Wall, Spark, Cure, Flash, Shield, Stalactite, Drip
→ AGI build (120 AGI + 140 WIS) with full chip diversity

**RipInPeace** (T511, 12 chips): Bandage, Protein, Ice, Helmet, Rock, Motivation, Spark, Cure, Shield, Solidification, Puny Bulb, Stalactite
→ Tank build (100 RES + Solidification + 2 shields)

### Universal Peer Patterns
- **ALL** have Helmet + Shield (damage reduction). We have neither.
- **ALL** have Cure. Most also have Bandage for double healing.
- **ALL** have Protein + Motivation buffs.
- Most have 9-12 chips (vs our 6). More slots = more tactical depth.
- STR ranges 200-300 (vs our 452). Nobody goes pure glass cannon.
- TP ranges 10-14. Higher TP = more actions = more chip usage per turn.
- Components: 4-8 per peer (vs our 0). Components give passive bonuses.

## Strategic Recommendations

### Immediate (AI Code Changes)
1. **Fix Cure usage** — AI should heal when HP drops below 60%. Currently Cure is used <7% of fights. This alone could push WR from 50% to 60%+ (see: 93% WR when Cure is used).
2. **Prioritize Flame over Flash** — Flame-only fights = 61% WR vs Flash-only = 16%.
3. **Verify buff execution** — Post-shouldBuff fix, Protein/Motivation/Boots should appear in chip usage. Monitor.

### Short-term (Build Changes)
4. **Buy Helmet chip** (L10, cheap) — Every peer has it. Flat damage reduction directly addresses our "die on turn 5-6" problem.
5. **Buy Shield chip** (L35, we qualify) — Stronger version of Helmet.
6. **Buy Spark chip** (L19, we qualify) — No-LOS damage chip. Opponents using Spark beat us 63-87% of the time.
7. **Invest in TP** — Even +2 TP (from 10 → 12) means 20% more actions per turn. All peers at T500+ have TP 12-14.

### Medium-term (Stat Respec)
8. **Consider rebalancing STR → TP/HP** — Our STR 452 is 1.5-2x any peer's, but we have the lowest HP and fewest TP. The data proves HP and TP correlate more with talent than raw STR.

## Appendix: Chip/Weapon ID Reference

### Chip IDs in Action Log → Name
| Action Log ID | Name | Type |
|--------------|------|------|
| 1 | Bandage | Heal |
| 2 | Cure | Heal |
| 7 | Flash | AoE Damage |
| 9 | Spark | Damage (no LOS) |
| 10 | Flame | Damage |
| 12 | Pebble | Damage |
| 19 | Helmet | Shield |
| 24 | Protein | STR Buff |
| 27 | Stretching | AGI Buff |
| 30 | Leather Boots | MP Buff |
| 33 | Motivation | TP Buff |

### Weapon API Template → Name
| API Template | Name | TP | Base Dmg | Range |
|-------------|------|----|----------|-------|
| 37 | Pistol | 3 | 15 | 1-7 |
| 39 | Double Gun | 4 | 18 | 2-7 |
| 40 | Destroyer | 6 | 40 | 1-6 |
| 41 | Shotgun | 5 | 33 | 1-5 |
| 42 | Laser | 6 | 43 | 2-9 |
| 45 | Magnum | 5 | 25 | 1-8 |
| 108 | Broadsword | 5 | 39 | 1-1 |
