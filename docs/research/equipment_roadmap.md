# Equipment Roadmap - Strategic Purchase Recommendations

> **STRAND 4**: Prioritized upgrade path for maximum WR impact
> **Status**: Complete | **Date**: 2026-01-25

---

## Current State

| Resource | Value |
|----------|-------|
| Habs | 17,461 |
| Level | 38 |
| STR | 310 |

### Equipment Inventory

| Category | Item | Level | Status |
|----------|------|-------|--------|
| Weapon | Pistol | 1 | Owned, unequipped |
| Weapon | Magnum | 27 | **EQUIPPED** |
| Weapon | **Destroyer** | 85 | Owned, **TOO HIGH LEVEL** |
| Chip | FLAME | 29 | Owned |
| Chip | FLASH | 24 | Owned |
| Chip | CURE | 20 | Owned |
| Chip | PROTEIN | 6 | Owned |
| Chip | MOTIVATION | 14 | Owned |
| Chip | LEATHER_BOOTS | 22 | Owned |

### Key Finding

**We already own the Destroyer (ID:40, L85, 45,320 habs value) but can't use it!**

We need to reach L85 before the Destroyer is usable. Until then, we must work with weapons ≤L38.

---

## Weapon Analysis (What We Can Use Now)

| Weapon | Lvl | Damage | TP | Uses | Price | Dmg/hab | Recommendation |
|--------|-----|--------|----|------|-------|---------|----------------|
| Pistol | 1 | 15±5 | 3 | 4 | 900 | 0.017 | Baseline |
| Machine Gun | 8 | 10±5×3 | 4 | 3 | 3,080 | 0.010 | Budget option |
| Shotgun | 16 | 33±10 | 5 | 2 | 6,800 | 0.005 | Burst focus |
| Magnum | 27 | 25±15 | 5 | 2 | 7,510 | 0.003 | **CURRENT** |
| **Laser** | 38 | **43±16** | **6** | **2** | **12,120** | **0.004** | **BEST UPGRADE** |
| Double Gun | 45 | 18±7×3 | 4 | 3 | 15,780 | 0.003 | High frequency |

### Weapon Comparison

```
Magnum (current): 25±15 damage = ~25-40 per hit
Laser:             43±16 damage = ~27-59 per hit
                    ↑58% higher average damage!
```

**The Laser is a massive upgrade:**
- +58% average damage vs Magnum
- AOE (area: 2) - hits adjacent cells
- Better range (2-9 vs 1-8)
- Only +1 TP cost (6 vs 5)

---

## Chip Analysis (Future Upgrades)

### Damage Chips (We Have: FLAME, FLASH)

| Chip | Lvl | Damage | TP | Price | Notes |
|------|-----|--------|----|-------|-------|
| FLAME | 29 | 29±2 | 4 | 5,560 | Owned, 3/turn |
| FLASH | 24 | 32±3 | 3 | 4,890 | Owned, AOE |
| **LIGHTNING** | **180** | **100+** | **?** | **325,200** | **Future goal** |
| METEORITE | 160 | 150+ | ? | 260,550 | Future goal |

### Buff Chips (We Have: PROTEIN, MOTIVATION, BOOTS)

| Chip | Lvl | Effect | TP | Price | Notes |
|------|-----|--------|----|-------|-------|
| PROTEIN | 6 | +80 STR (2t) | 3 | 3,520 | Owned |
| MOTIVATION | 14 | +2 TP (3t) | 4 | 3,560 | Owned |
| STEROID | 134 | +??? STR | ? | 187,050 | Future |
| RAGE | 226 | +??? STR | ? | 569,210 | Future |

### Heal Chips (We Have: CURE)

| Chip | Lvl | Heal | TP | Price | Notes |
|------|-----|------|----|-------|-------|
| CURE | 20 | 38±8 | 4 | 3,710 | Owned |
| REGENERATION | 122 | 45±? | ? | 135,000 | Future |
| VAMPIRIZATION | 177 | ?+dmg | ? | 214,230 | Future |

---

## Purchase Priority (ROI Analysis)

### Tier 1: Buy NOW (immediately impactful)

#### 1. LASER (Weapon) - 12,120 habs

| Metric | Value |
|--------|-------|
| Price | 12,120 habs |
| Damage increase | +58% (25→43 avg) |
| TP cost | +1 (5→6) |
| Availability | L38 (we're L38!) |

**ROI: 0.58 / 12120 = ~0.0048% WR per 1000 habs**

**Expected Impact:**
- Turn 1 burst: 25→43 damage (+18 dmg)
- Reduces fights by ~1 turn
- Improves win rate by ~3-5% against balanced opponents

**Purchase command:**
```bash
leek market buy 42  # Laser
```

---

### Tier 2: Save For (within 2-3 weeks)

#### 2. DOUBLE GUN (Weapon) - 15,780 habs

| Metric | Value |
|--------|-------|
| Price | 15,780 habs |
| Damage | 18±7 per shot ×3 = ~54/turn |
| TP cost | 4 (efficient!) |
| Uses/turn | 3 |
| Availability | L45 (need 7 more levels) |

**Why Double Gun?**
- 4 TP cost is very efficient
- 3 shots = 54 total damage potential
- Fast fire rate good for finishing weakened enemies
- Complements Laser (different playstyle)

**Expected: +2-3% additional WR with both Laser + Double Gun**

---

#### 3. MACHINE GUN (Weapon) - 3,080 habs

| Metric | Value |
|--------|-------|
| Price | 3,080 habs |
| Damage | 10±5 ×3 = ~30/turn |
| TP cost | 4 |
| Availability | L8 (can use now!) |

**Why Machine Gun?**
- Cheap backup weapon
- Good for chip-openers (save TP for chips)
- 3 guaranteed hits (consistent damage)
- Only 3,080 habs = great budget option

---

### Tier 3: Future Goals (L85+)

#### DESTROYER (Weapon) - OWNED, L85

| Metric | Value |
|--------|-------|
| Price | 45,320 habs |
| Damage | 40±20 |
| TP cost | 6 |
| Uses/turn | 2 |
| Requirement | **L85** |

**We already own this!** Just need to grind 47 more levels.

---

## Strategic Recommendations

### Immediate Priority

**1. Buy the Laser (12,120 habs)**
- Perfect level match (L38 = Laser L38)
- Massive damage boost (+58%)
- Leaves 5,341 habs reserve

**2. Keep Magnum equipped as secondary**
- Magnum uses 5 TP, Laser uses 6 TP
- When TP is tight, Magnum is fine
- Don't sell it!

### Short-term Strategy

| Level | Goal | Habs Needed |
|-------|------|-------------|
| L38 | Buy Laser | 12,120 |
| L40 | Machine Gun backup | 3,080 |
| L45 | Double Gun | 15,780 |
| L60+ | LIGHTNING chip | 325,200 |
| L85 | USE DESTROYER | 0 (owned!) |

### Equipment Rotation Plan

```
Turn 1: PROTEIN + MOTIVATION + BOOTS (buffs) + Laser (attack)
Turn 2: FLASH + Laser
Turn 3: FLAME + FLAME + FLAME
Turn 4: If losing: CURE, else: attack
...
Late: Save chips for burst windows
```

---

## Meta Context

From nemesis analysis, our losses end in 5-6 turns. Higher opening burst (Laser) could win those fights.

From meta analysis, aggro (60% WR) beats balanced (39%). More damage = more aggro.

---

## Appendix: Habs Earning Strategy

### Current Habs: 17,461

**Daily income:**
- Garden fights: ~5-10 talent/day = ~500-1000 habs/day
- GitHub Actions: 3 runs × 50 fights × ~10 habs = ~1500 habs/run

**To earn Laser (12,120 habs):**
- ~8-10 days at current pace
- Or buy trophy enigmas (see THOUGHTS.md)

**Command to check habs:**
```bash
leek info farmer
```

---

## Appendix: Purchase Commands

```bash
# Check market availability
leek market search laser

# Buy Laser (item ID 42)
leek market buy 42

# Buy Machine Gun (item ID 38)  
leek market buy 38

# Buy Double Gun (item ID 39)
leek market buy 39

# Check current inventory
leek craft inventory
```