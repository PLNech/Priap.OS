# Chip Stats Research (2026-01-23)

> Extracted from `tools/leek-wars/src/model/chips.ts`

## Chips Available at Level 34 or Below

| Name | Type | Level | TP Cost | Cooldown | Min Range | Max Range | Effect | Base Value | Duration |
|------|------|-------|---------|----------|-----------|-----------|--------|------------|----------|
| **shock** | Damage | 2 | 2 | 0 | 0 | 6 | Single target | 7 dmg | Instant |
| **bandage** | Heal | 3 | 2 | 1 | 0 | 6 | Single target | 23 heal | Instant |
| **pebble** | Damage | 4 | 2 | 1 | 0 | 5 | Single target | 2 dmg (high scaling) | Instant |
| **protein** | Buff STR | 6 | 3 | 3 | 0 | 4 | +80 Strength | +80 STR | 2 turns |
| **ice** | Damage | 9 | 4 | 0 | 0 | 8 | Single target | 17 dmg | Instant |
| **helmet** | Shield | 10 | 3 | 3 | 0 | 4 | Relative shield | +15% | 2 turns |
| **rock** | Damage | 13 | 5 | 1 | 2 | 6 | Single target | 38 dmg | Instant |
| **motivation** | Buff TP | 14 | 4 | 6 | 0 | 5 | +2 TP/turn | +2 TP | 3 turns |
| **stretching** | Buff AGI | 17 | 3 | 3 | 0 | 5 | +80 Agility | +80 AGI | 2 turns |
| **wall** | Shield | 18 | 3 | 3 | 0 | 3 | Relative shield | +4% | 2 turns |
| **spark** | Damage | 19 | 3 | 0 | 0 | 10 | **No LoS required** | 8 dmg (high scaling) | Instant |
| **cure** | Heal | 20 | 4 | 2 | 0 | 5 | Single target | 38 heal | Instant |
| **leather_boots** | Buff MP | 22 | 3 | 5 | 0 | 5 | +2 MP/turn | +2 MP | 2 turns |
| **flash** | Damage | 24 | 3 | 1 | 1 | 10 | **AOE (3 cells)** | 32 dmg | Instant |
| **flame** | Damage | 29 | 4 | 0 | 2 | 7 | Single target | 29 dmg | Instant |
| **knowledge** | Buff SCI | 32 | 5 | 4 | 0 | 7 | +250 Science | +250 SCI | 2 turns |

## Effect Type Reference

From `tools/leek-wars/src/model/effect.ts`:

| Type ID | Effect |
|---------|--------|
| 1 | DAMAGE |
| 2 | HEAL |
| 4 | BUFF_AGILITY |
| 5 | RELATIVE_SHIELD (% reduction) |
| 6 | ABSOLUTE_SHIELD (flat reduction) |
| 7 | BUFF_MP |

## Key Observations

### Damage Chips (Priority for STR build)
- **Flash** (L24): Best value - AOE, long range (10), only 3 TP
- **Spark** (L19): No line-of-sight required - hit through obstacles!
- **Flame** (L29): No cooldown, solid damage
- **Rock** (L13): Highest base damage (38), but min range 2

### Healing Chips
- **Cure** (L20): 38 base heal, 2 turn cooldown
- **Bandage** (L3): 23 base heal, 1 turn cooldown (more spammable)

### Utility Chips
- **Leather_boots** (L22): +2 MP is huge for positioning
- **Motivation** (L14): +2 TP lets you attack more
- **Protein** (L6): +80 STR synergizes with our 234 STR build

### Shield Chips
- **Helmet** (L10): Cheap relative shield
- **Wall** (L18): Lower value but short range

## Cooldown Analysis

| Cooldown | Chips |
|----------|-------|
| 0 (spam) | shock, ice, spark, flame |
| 1 | bandage, pebble, rock, flash |
| 2 | cure |
| 3 | protein, helmet, stretching, wall |
| 4+ | motivation (6), leather_boots (5), knowledge (4) |

## Range Tiers

| Range | Chips |
|-------|-------|
| Long (8-10) | ice (8), spark (10), flash (10) |
| Medium (5-7) | shock (6), rock (6), flame (7), knowledge (7) |
| Short (3-5) | pebble (5), cure (5), leather_boots (5), motivation (5) |
| Melee (0-4) | protein (4), helmet (4), wall (3) |

## Source Files
- `/home/pln/Work/Perso/Priap.OS/tools/leek-wars/src/model/chips.ts`
- `/home/pln/Work/Perso/Priap.OS/tools/leek-wars/src/model/effect.ts`
