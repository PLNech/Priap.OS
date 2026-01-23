# Ground Truth Reference

> **Claude**: ALWAYS read this before reasoning about combat math or game values.
> **Source**: `tools/leek-wars/src/model/*.ts` (authoritative)

---

## TP Budget (L34)

| Resource | Value | Notes |
|----------|-------|-------|
| Base TP | **10** | At level 34 |
| `setWeapon()` | **-1 TP** | Hidden cost! Only call once |
| Available after equip | **9 TP** | For attacks/chips |

---

## Our Weapons

| Weapon | TP Cost | Uses/Turn | Range | Item ID | Level | Damage |
|--------|---------|-----------|-------|---------|-------|--------|
| **Pistol** | 3 | 4 | 1-7 | 37 | 1 | 15±5 |
| **Magnum** | 5 | 2 | 1-8 | 45 | 27 | 25±15 |
| Destroyer | 6 | 2 | 1-6 | 40 | 85 | 40±20 |

**Source**: `tools/leek-wars/src/model/weapons.ts`

---

## Our Chips

| Chip | ID | TP | Uses/Turn | CD | Range | Effect |
|------|-----|-----|-----------|-----|-------|--------|
| **FLAME** | 5 | 4 | **3** | 0 | 2-7 | 29±2 dmg |
| **FLASH** | 6 | 3 | ∞ | 1 | 1-10 | 32±3 dmg (AOE) |
| **CURE** | 4 | 4 | ∞ | 2 | 0-5 | 38±8 heal |
| **PROTEIN** | 8 | 3 | ∞ | 3 | 0-4 | +80±20 STR (2t) |
| **BOOTS** | 14 | 3 | ∞ | 5 | 0-5 | +2 MP (2t) |
| **MOTIVATION** | 15 | 4 | ∞ | 6 | 0-5 | +2 TP (3t) |

**Source**: `tools/leek-wars/src/model/chips.ts`

**Note**: `max_uses: -1` = unlimited per turn; `max_uses: 3` = max 3 per turn

---

## Common TP Calculations

### With Pistol (3 TP, already equipped)
| Actions | TP Cost | Remaining | Valid? |
|---------|---------|-----------|--------|
| 3x Pistol | 9 | 1 | ✅ |
| 1x FLASH + 2x Pistol | 3+6=9 | 1 | ✅ |
| 3x FLAME | 12 | -2 | ❌ |
| 2x FLAME + 1x FLASH | 8+3=11 | -1 | ❌ |
| 2x FLAME | 8 | 2 | ✅ |
| MOTIVATION + 2x Pistol | 4+6=10 | 0 | ✅ |

### With Magnum (5 TP, needs equip)
| Actions | TP Cost | Remaining | Valid? |
|---------|---------|-----------|--------|
| setWeapon + 1x Magnum | 1+5=6 | 4 | ✅ |
| setWeapon + 1x Magnum + 1x FLASH | 1+5+3=9 | 1 | ✅ |
| setWeapon + 2x Magnum | 1+10=11 | -1 | ❌ |

---

## LeekScript Constants (from FightConstants.java)

```java
// Weapons (ITEM IDs, not template IDs!)
WEAPON_PISTOL = 37
WEAPON_MAGNUM = 45
WEAPON_DESTROYER = 40  // NOT magnum!

// Attack results
USE_SUCCESS = 1
USE_FAILED = 0
USE_INVALID_TARGET = -1
USE_NOT_ENOUGH_TP = -2
USE_INVALID_COOLDOWN = -3
USE_MAX_USES = -7
```

**Source**: `tools/leek-wars-generator/src/main/java/com/leekwars/generator/FightConstants.java`

---

## Effect Type IDs

| ID | Effect Type |
|----|-------------|
| 1 | DAMAGE |
| 2 | HEAL |
| 3 | BUFF_STRENGTH |
| 5 | RELATIVE_SHIELD |
| 6 | ABSOLUTE_SHIELD |
| 7 | BUFF_MP |
| 8 | BUFF_TP |
| 13 | POISON |

**Source**: `tools/leek-wars-generator/src/main/java/com/leekwars/generator/FightConstants.java`

---

## Quick Validation Checklist

Before proposing any combat sequence:

1. [ ] Sum all TP costs
2. [ ] Check total ≤ available (usually 9-10)
3. [ ] Account for `setWeapon()` if switching
4. [ ] Verify chip cooldowns (can't use same chip twice if CD>0)
5. [ ] Check max_uses (FLAME = 3/turn max)
6. [ ] Verify range requirements

---

## How to Update This Doc

```bash
# Regenerate from submodules
python scripts/parse_ground_truth.py --output docs/GROUND_TRUTH.md
```

---

*Last updated: 2026-01-23*
*Ground truth sources: tools/leek-wars (frontend), tools/leek-wars-generator (simulator)*
