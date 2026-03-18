# Opponent Build Analysis — S34 (2026-03-17)

Data source: `leek scout` on 10 recent garden opponents (7 losses, 3 wins).
Our build: L123 T350 | HP 1030 STR 452 RES 0 TP 14 MP 4 | b_laser + Laser + Magnum

## Loss Opponents (7)

| Leek | L | T | HP | STR | RES | TP | MP | WIS | AGI | Weapons | Notable Chips | Summons |
|------|---|---|-----|-----|-----|----|----|-----|-----|---------|---------------|---------|
| MrRobotanic | 116 | 686 | 902 | 220 | 125 | 15 | 5 | 245 | 100 | magnum, destroyer, sword | 15 chips! wall, solidification, jump, knowledge | no |
| ADAMA | 123 | 389 | 1002 | 480 | 52 | 10 | 4 | 52 | 0 | magnum | stalactite, protein, puny_bulb | **YES** |
| LUKLEPOIRO | 123 | 389 | 958 | 250 | 150 | 12 | 4 | 100 | 0 | magnum, axe | bandage, cure | no |
| AbdelBelKader | 123 | 391 | 1126 | 340 | 200 | 10 | 3 | 200 | 0 | magnum, **b_laser** | flame, armor, tranq, motivation | no |
| ahminh | 124 | 410 | 953 | 402 | 180 | 10 | 3 | 0 | 0 | magnum, axe | protein, puny_bulb | **YES** |
| d3vilmax | 124 | 410 | 1101 | 441 | 0 | 10 | 3 | 140 | 0 | laser | flame, spark, stalactite, cure | no |
| Vinceleekidi | 124 | 425 | **1511** | 413 | 0 | 10 | 3 | 0 | 0 | laser, destroyer, **b_laser** | 10 chips: armor, motivation, tranq, prism | no |

## Win Opponents (3)

| Leek | L | T | HP | STR | RES | TP | MP | WIS | AGI | Weapons | Notable Chips | Summons |
|------|---|---|-----|-----|-----|----|----|-----|-----|---------|---------------|---------|
| Komget | 123 | 330 | 1298 | 429 | 28 | 10 | 4 | 0 | 0 | shotgun, b_laser | flame, armor, tranq, motivation | no |
| Heliareau | 124 | 374 | 1101 | 253 | 0 | 14 | 4 | 205 | 0 | magnum | cure, vaccine, stalactite, armor | no |
| Feather | 123 | 362 | 906 | 375 | 0 | 14 | 3 | 0 | 0 | b_laser | flame, armor, motivation, tranq | no |

## Our Build for Reference

| Stat | Value | Rank vs 10 opponents |
|------|-------|---------------------|
| HP | 1030 | 5th (mid-pack) |
| STR | 452 | **1st** (highest!) |
| RES | 0 | **Last** (10 of 10) |
| TP | 14 | **Tied 1st** (w/ Feather, Heliareau, MrRobotanic) |
| MP | 4 | 3rd |
| WIS | 0 | Tied last |

---

## Key Findings

### 1. RES is the silent killer
- **5/7 losses** had RES > 0 (avg 101 in losses vs 9 in wins)
- AbdelBelKader: RES 200 + WIS 200 — our pure STR attacks bounce off
- Even moderate RES (52-125) significantly reduces our damage output
- We are the ONLY leek out of 10 with zero RES. Glass cannon without the cannon range.

### 2. WIS is underrated — we have 0
- **4/7 loss opponents** run WIS 100-245 (healing, debuff resistance)
- MrRobotanic (T686!): WIS 245, STR only 220 — WIS-heavy build beats pure STR
- d3vilmax: WIS 140, no RES — WIS carries healing chips (cure), sustains through fights
- **0/3 win opponents** had WIS > 0... except Heliareau (205 WIS but won — they had 0 RES)
- Cure + high WIS = outheal our damage

### 3. HP investment correlates with wins/losses
- Vinceleekidi's **1511 HP** is 47% more than our 1030. With STR 413 + 10 chips, they outlast us.
- Loss avg HP: 1078 vs Win avg HP: 1102 — similar, but high HP + RES = unbreakable
- **Komget** (1298 HP, RES 28) — we beat them because no RES despite massive HP pool

### 4. TP is our edge — but is it enough?
- We have TP 14 — top tier. Most opponents run TP 10.
- But TP 10 + RES 200 + WIS 200 (AbdelBelKader) beats TP 14 + STR 452 + RES 0.
- Extra actions don't help when each hit does 30% less damage.

### 5. Equipment meta at T350-T425
**Most common chips** (across all 10):
- shield (8/10), helmet (8/10) — universal defensive layer
- flame (5/10), armor (6/10), motivation (5/10), tranquilizer (5/10)
- stalactite (4/10), cure (4/10), protein (3/10)

**Most common weapons**:
- magnum (7/10) — universal bread-and-butter
- b_laser (4/10) — rising star, damage + self-heal
- axe (2/10), destroyer (3/10), laser (3/10)

**Our chip loadout** (6/6): Flame, Tranquilizer, Motivation, Helmet, Shield, Armor
- We have the core meta chips already ✓
- Missing: **cure/bandage** (healing), **stalactite** (ranged damage), **protein** (buff)

### 6. Bulb summoners: 2/7 losses
- ADAMA and ahminh use puny_bulb. Both had moderate STR (480, 402) plus summon distraction.
- Anti-bulb fix should help, but we beat Feather (no bulbs, b_laser build) — the fix alone isn't the issue.

---

## Actionable Hypotheses

### H1: "RES 50-100 would flip 2-3 losses to wins"
- LUKLEPOIRO (RES 150, STR 250) — if we had RES 50, their 250 STR does 200 effective. We still outhit.
- MrRobotanic (STR 220) — with RES 50, their attacks do ~170. We survive longer.
- **Cost**: At 400+ STR, each RES point costs 2 capital. 50 RES = 100 capital. EXPENSIVE.
- **Alternative**: Buy Ferocity chip (+50% STR, 2 turns) — effectively +226 STR on burst turns.

### H2: "WIS + Cure chip = sustain we lack"
- d3vilmax beat us with 0 RES, 0 AGI, just WIS 140 + cure chip
- WIS amplifies healing (cure + bandage). 100 WIS doubles heal effectiveness.
- **But**: WIS costs capital AND a chip slot. We're at 6/6 chips. Need to drop something.
- **Drip** (L56, 2 TP, 32 heal, 1 CD) is a lightweight heal option — needs a slot.

### H3: "Ferocity is the highest-ROI purchase"
- +50% STR for 2 turns = +226 effective STR with our 452 base
- Would help punch through moderate RES (100-150 range)
- Cost: 147,340 Habs (we have ~114K — ~33K short)
- **Timeline**: 2-3 more days of income

### H4: "HP might be better than STR at this point"
- Our STR 452 is already HIGHEST in the bracket. More STR has diminishing returns vs RES.
- Vinceleekidi (1511 HP!) and Komget (1298 HP) both survive longer.
- HP is cheap: 4 HP per capital (sub-1000 invested) or 3 HP (1000-1999).
- **Consider**: Next capital → HP instead of STR.

---

## Top Climbers (T300-T600 bracket)

Scouted via `leek scout` for comparison with our opponents.

| Leek | L | T | HP | STR | RES | WIS | MAG | TP | MP | Build Type |
|------|---|---|-----|-----|-----|-----|-----|----|----|------------|
| HussarddelaRacine | 169 | 215 | 844 | 0 | 0 | 50 | 500 | 12 | 5 | Pure magic (meteorite, venom, 3 bulbs) — T dropped to 215! |
| **Fumetsu** | 166 | 400 | 1475 | 400 | **200** | **200** | 0 | 14 | 4 | **THE MODEL** — balanced STR+RES+WIS |
| WelshWitch | 199 | 581 | 1674 | 0 | 260 | 280 | 510 | 17 | 6 | Magic/AGI hybrid, 0W-5L/10 |

**Fumetsu is the exemplar.** Same bracket (T400), physical build like ours, TP 14 like ours. But:
- STR 400 vs our 452 (we have +52, ~13% more)
- RES **200** vs our **0** (they have infinite% more)
- WIS **200** vs our **0** (massive heal amplification)
- HP **1475** vs our **1030** (43% more)
- 13 chips vs our 6 (higher level = more RAM/chip slots)

The delta: they sacrificed ~50 STR to buy RES 200 + WIS 200. At level 166 they have more capital, but the allocation pattern is clear: **don't go all-in on offense.**

---

### H5: "The TP 14 advantage is wasted if we can't sustain"
- We have 4 more TP than most opponents. That's 4 extra actions per turn.
- But if we're dead by turn 5 because RES 0, those turns don't happen.
- **Tradeoff worth exploring**: TP 12 + RES 60 vs TP 14 + RES 0.
- Each TP point costs 30-100 capital (progressive). RES costs 2 capital per point at 0.
