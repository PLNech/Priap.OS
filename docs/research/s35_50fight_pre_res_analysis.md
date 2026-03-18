# S35 Fight Analysis — 50 Fights Pre-RES Baseline (2026-03-18)

Data: 50 solo garden fights run by cron at 20:00. **This is the LAST pre-RES batch** — RES was 0 during these fights. RES 40 was invested post-fights. Tomorrow = first RES 40 data.

## Overall: 25W-24L-1D (50% WR)

Consistent with S30 analysis (52% WR over 50 fights). We're at equilibrium for our talent band.

---

## Key Findings

### 1. RES is STILL the dividing line

| Opponent RES | Record | WR | Fights | Verdict |
|-------------|--------|-----|--------|---------|
| **0** | 9W-6L | **60%** | 15 | We dominate zero-RES |
| **1-49** | 4W-1L | **80%** | 5 | Low RES = easy prey |
| **50-99** | 2W-3L | 40% | 5 | Tipping point |
| **100-149** | 3W-2L | 60% | 5 | Sample too small |
| **150+** | 7W-13L | **35%** | 20 | **Kryptonite confirmed** |

**40% of opponents (20/50) have RES 150+.** That's our biggest matchup problem.
With our new RES 40, we'll absorb 40 more damage per hit — but won't change this dynamic much. We need Ferocity (+50% STR) to punch through high RES.

### 2. Counter-intuitive STR finding

| Opponent STR | Record | WR | Fights |
|-------------|--------|-----|--------|
| 200-299 | 4W-9L | **31%** | 13 |
| 300-399 | 5W-7L | 42% | 12 |
| **400+** | **16W-9L** | **64%** | 25 |

**We beat high-STR opponents more often!** Why? Because STR 400+ means they went glass cannon like us — low RES/WIS. Our mirror image. It's the **balanced builds (STR 200-300 + RES 150+ + WIS 100+)** that destroy us.

### 3. Summon matchup REVERSED from S30

| Matchup | Record | WR | Fights |
|---------|--------|-----|--------|
| vs Summons | **5W-11L** | **31%** | 16 |
| vs No Summons | 20W-14L | **59%** | 34 |

S30 showed 64% WR vs summoners. Now 31%. The anti-bulb fix might have regressed, OR the summon users at T369 are stronger than at T350. **This needs investigation.**

### 4. WIS predicts our losses

| Opponent WIS | Record | WR | Fights |
|-------------|--------|-----|--------|
| **0** | **9W-4L** | **69%** | 13 |
| 1-99 | 5W-4L | 56% | 9 |
| 100-199 | 5W-8L | 38% | 13 |
| **200+** | 6W-9L | **40%** | 15 |

WIS 0 = 69% WR. WIS 200+ = 40% WR. High WIS opponents heal more, resist debuffs, and out-sustain us. Our WIS is effectively 40 (from CD component only).

### 5. HP isn't a strong predictor

| Opponent HP | Record | WR | Fights |
|-------------|--------|-----|--------|
| <500 | 1W-1L | 50% | 2 |
| 500-799 | 7W-5L | 58% | 12 |
| 800-999 | 4W-6L | 40% | 10 |
| 1000-1299 | 8W-11L | 42% | 19 |
| **1300+** | **5W-2L** | **71%** | 7 |

High HP alone doesn't beat us — it's HP + RES + WIS that creates the unbeatable combo.
Interestingly, 1300+ HP opponents = 71% WR for us. Possibly because extreme HP investment means less RES.

### 6. Fight Duration

| Outcome | Avg Turns | Range |
|---------|-----------|-------|
| Wins | **8.2** | 4-17 |
| Losses | **10.0** | 4-30 |

Losses drag on longer. The 30-turn loss (GraceLeek: RES 250, WIS 250) = classic stalemate we can't break.

### 7. Equipment Usage (our AI)

**Weapons** (properly tracked via SET_WEAPON):
- **b_laser**: 68% of fights (primary, as intended)
- **magnum**: 48% (fallback)
- **laser**: 8% (rare fallback)

Note: Other weapons appearing (shotgun, axe, etc.) are entity-tracking noise from opponent actions leaking — needs fix in parser.

**Chips** (ours):
- helmet: 88%, shield: 82%, armor: 82% — defensive core working
- motivation: 70% — buff usage healthy
- flame: 68% — primary chip damage
- tranquilizer: 58% — TP denial active

---

## Compared to S30 Analysis (50 fights)

| Metric | S30 (T350) | S35 (T369) | Change |
|--------|-----------|-----------|--------|
| Overall WR | 52% | 50% | -2% (within noise) |
| vs RES 0 | ~70% | 60% | -10% |
| vs Summons | 64% | **31%** | **-33%!!** |
| vs No Summons | 47% | 59% | +12% |

The talent climb (T350→T369) means harder opponents. Our WR staying at 50% while facing stronger opponents is actually NEUTRAL — not a decline.

The summon WR collapse is alarming and needs investigation.

---

## Actionable Insights

1. **RES 40 won't be enough** — 40% of opponents have RES 150+. We need Ferocity (+50% STR).
2. **Summon matchup regression** — investigate anti-bulb code. May need to adapt to T369 summoners.
3. **Glass cannons are free wins** — 64% WR vs STR 400+ opponents. The meta is balanced builds.
4. **WIS investment worth considering** — WIS 0 opponents = 69% WR for us. When we FACE high WIS, we lose. What if we HAD WIS?
5. **Tomorrow's 50 fights** = first RES 40 test. Compare vs this baseline.

---

## Movement Analysis (20 fights deep-dive)

### b_laser almost never fires
- **Weapon fired: 13% of turns** (26/204). Our 20 value/TP weapon is a decoration.
- **Chip-only turns: 71%** — defensive chips eat all TP budget.
- **Move-only turns: 16%** — pure waste. 19% in losses, 13% in wins.

### The TP Budget Problem
With TP 14 (16 with Motivation):
- Shield (4) + Armor (6) + Helmet (3) = **13 TP on defense** when all need refreshing
- Leaves 3 TP — not enough for Flame (4), Tranq (3), OR b_laser (5)
- Cooldowns mean not all 3 refresh every turn, but the priority system burns TP on defense before even considering the weapon

### Root Cause
The AI executes in strict priority order: **Defense → Debuff → Chip damage → Weapon → Move**. By the time it reaches the weapon step, TP is gone. Combined with 4-5 turns of approach distance, the weapon never enters the combat equation.

### Recommendation
Rework AI to **guarantee weapon usage** when in range. Possible approaches:
1. **Reserve TP**: Set aside 5 TP for b_laser before spending on optional shields
2. **Weapon-first at range 8**: Already partially implemented but clearly not working
3. **Skip lowest-value shield**: If TP < 8, skip Helmet (3 TP, -15 dmg) to ensure b_laser (5 TP, 50 dmg + 50 heal = 100 total value)
4. **Movement rework**: Better approach pathing to reach weapon range faster

User + experienced player ("sensei") confirmed: movement/positioning AI is fundamentally weak.

---

## Build: IAdonis at time of fights
- L125 | T369 | HP 1030 | STR 452 | **RES 0** | TP 14 | MP 4 | WIS 40 (CD component)
- Weapons: b_laser, Laser, Magnum
- Chips: Flame, Tranquilizer, Motivation, Helmet, Shield, Armor
- AI: v14_flat "Phalanx"
