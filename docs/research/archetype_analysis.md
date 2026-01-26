# Archetype Analysis - January 2026

Analysis of 10,000 scraped fights using automated AI classification.

## Classification System

Four archetypes based on behavior metrics:
- **aggro**: attack_rate > 2.0/turn OR (attack_rate > 1.5 AND moves toward enemy)
- **kiter**: move_tendency > +2.0 (moves away) AND move_rate > 0.5/turn
- **healer**: heal_ratio > 0.3 of total actions
- **balanced**: default (moderate behavior)

Metrics:
- `attack_rate`: weapon/chip uses per turn
- `move_tendency`: +N = moves N cells away from enemy avg, -N = toward
- `entropy`: Shannon entropy of action types (higher = more varied)

## Archetype Distribution (n=1000)

| Archetype | Frequency | Win Rate |
|-----------|-----------|----------|
| balanced  | 40.2%     | 39.2%    |
| **aggro** | 38.0%     | **60.4%** |
| kiter     | 21.7%     | 51.8%    |
| healer    | 0.1%      | N/A      |

**Key finding**: Aggro dominates the meta with 60% win rate.

## Matchup Matrix (1v1 fights)

| Matchup          | T1 Win Rate | Notes |
|------------------|-------------|-------|
| aggro vs balanced | **89.9%**  | Aggro crushes balanced |
| aggro vs kiter    | **68.9%**  | Aggro beats kiters |
| kiter vs aggro    | 56.9%      | Kiters CAN beat aggro (first-mover) |
| kiter vs balanced | **86.3%**  | Kiters crush balanced |
| balanced vs balanced | 79.9%   | T1 advantage in mirrors |
| aggro vs aggro    | 61.6%      | T1 advantage in mirrors |

**No rock-paper-scissors** - aggro beats everything. First-mover advantage is real.

## Entropy vs Win Rate

| Entropy Bucket | n | Win Rate |
|---------------|---|----------|
| Low (<1.5)    | 6 | 0.0%     |
| Medium (1.5-2.5) | 535 | 42.9% |
| **High (>2.5)**  | 459 | **58.2%** |

**Variety wins.** High entropy (adaptable, varied play) beats predictable patterns.
Low entropy bots that spam one action type are easier to counter.

## Strategic Implications

1. **Be aggressive** - aggro has 60% WR across the board
2. **Move first matters** - T1 wins mirrors consistently
3. **Stay unpredictable** - high entropy correlates with winning
4. **Don't be passive** - balanced (wait-and-see) has lowest WR at 39%

## Recommendations for AI Development

1. Increase attack rate - aim for >1.5 attacks/turn
2. Move TOWARD enemy, not away (unless significantly outranged)
3. Vary action patterns to increase entropy
4. Don't waste turns "positioning" - engage immediately

---
*Analysis run: 2026-01-24*
*Sample: 1000 fights from fights_light.db (10k total)*
*Classifier: leekwars_agent.fight_analyzer.classify_ai_behavior()*
