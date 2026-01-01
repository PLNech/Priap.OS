# LeekWars Game Mechanics & Strategy

## Overview

LeekWars is a multiplayer browser AI programming game where you code AI for leeks that fight autonomously. The game uses **LeekScript**, a custom language similar to JavaScript.

## Game Structure

### Leeks
- Each player has leeks that level up through fights
- Leeks gain XP and capital (stat points) from fights
- Stats: Life, Strength, Agility, Wisdom, Resistance, Magic, Science, TP (Turn Points), MP (Movement Points)

### Fight Types
1. **Solo** - 1v1 leek fights
2. **Farmer** - All your leeks vs opponent's leeks
3. **Team** - Team compositions fight

### Arena/Garden
- Daily fights available in the garden
- Fight count replenishes over time
- Different fight pools for solo/farmer/team

---

## LeekScript Basics

LeekScript is the programming language used to code leek AI.

### Core Functions (examples)

```leekscript
// Movement
moveToward(enemy)
moveAway(enemy)
moveTowardCell(cell)

// Combat
useWeapon(enemy)
useChip(chip, target)

// Information
getLife()
getTP()
getMP()
getEnemies()
getAllies()
getWeapons()
getChips()

// Pathfinding
getCellDistance(cell1, cell2)
getPathLength(cell1, cell2)
getPath(cell1, cell2)

// Registers (persistent storage)
setRegister(key, value)  // Persists between fights
getRegister(key)
```

### Turn Structure
1. Each turn, your AI executes
2. Limited by TP (action points) and MP (movement points)
3. Actions: move, attack, use chips, etc.

---

## Strategy Considerations

### Combat Basics
- **Range**: Weapons/chips have min/max range
- **Line of Sight**: Most attacks need clear LOS
- **Area Effects**: Some attacks hit multiple cells

### Build Types
1. **Tank** - High life/resistance, melee
2. **Shooter** - High strength, ranged weapons
3. **Mage** - High magic, chip-based damage
4. **Support** - Healing, buffs, debuffs

### Advanced Tactics
- **Kiting**: Stay at max range, retreat when approached
- **Positioning**: Use obstacles for cover
- **Resource Management**: Don't waste TP/MP
- **Target Selection**: Prioritize weak/dangerous enemies

---

## Local Development (Fight Generator)

The fight generator allows running fights locally for testing and RL.

### Setup
```bash
git clone https://github.com/leek-wars/leek-wars-generator
cd leek-wars-generator
git submodule update --init
gradle jar
```

### Usage
```bash
# Analyze AI code
java -jar generator.jar --analyze test/ai/basic.leek

# Run a fight scenario
java -jar generator.jar test/scenario/scenario1.json
```

### Scenario Format
```json
{
  "teams": [
    {
      "leeks": [
        {
          "name": "MyLeek",
          "level": 100,
          "ai": "path/to/ai.leek",
          "weapons": [1, 2],
          "chips": [10, 20, 30]
        }
      ]
    },
    {
      "leeks": [
        {
          "name": "Enemy",
          "level": 100,
          "ai": "path/to/enemy.leek"
        }
      ]
    }
  ]
}
```

---

## RL Integration Ideas

### State Space
- Leek positions (grid cells)
- Health/TP/MP of all entities
- Cooldowns on chips
- Obstacles/terrain

### Action Space
- Move to cell (discrete: up/down/left/right or cell selection)
- Use weapon on target
- Use chip on target
- Skip turn

### Reward Shaping
- +1 for damage dealt
- -1 for damage taken
- +10 for kill
- -10 for death
- +100 for win
- -100 for loss

### Training Approach
1. Use fight generator locally
2. Extract state from fight logs
3. Train policy network
4. Convert to LeekScript for deployment

---

## Resources

- [LeekWars Help](https://leekwars.com/help)
- [LeekWars Documentation](https://leekwars.com/help/documentation)
- [LeekScript GitHub](https://github.com/leek-wars/leekscript)
- [Fight Generator](https://github.com/leek-wars/leek-wars-generator)
