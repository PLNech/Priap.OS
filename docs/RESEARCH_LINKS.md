# LeekWars Research Links

Status legend: ⏳ pending | ✅ fetched | ❌ failed | 🔒 requires auth

---

## Game Mechanics (Official)

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 1 | https://leekwars.com/encyclopedia/en/Turn_Points | 🔒 | JS-rendered, needs browser |
| 2 | https://leekwars.com/encyclopedia/en/Characteristics | ✅ | 12 stats: Life, Strength, Wisdom, Resistance, Agility, Science, Magic, Frequency, Cores (more ops), RAM (more chips/vars), TP, MP. Build diversity is key. |
| 3 | https://leekwars.com/encyclopedia/en/Weapons | ⏳ | |
| 4 | https://leekwars.com/encyclopedia/en/Hide-and-seek | ✅ | **CRITICAL**: Find cells where enemy has NO LOS even after moving. Algorithm: 1) Get your accessible cells, 2) Get enemy accessible cells, 3) For each your cell, test LOS vs ALL enemy cells. No LOS to any = safe. Can compute "danger score" for partial safety. |
| 5 | https://leekwars.com/encyclopedia/en/Accessible_cells | ✅ | **CRITICAL**: Neighbor propagation algorithm. Naive: getPathLength per cell (expensive). Better: go neighbor-to-neighbor, count down MP. Optimizations: 1) Associative array (cell as key), 2) Cache neighbors at turn 1, 3) Binary representation (4 bits per cell = 1 op each!), 4) Degrade resolution (even MP only, interpolate). Forum benchmark exists. |
| 6 | https://leekwars.com/encyclopedia/en/Tournaments | ⏳ | |
| 7 | https://leekwars.com/encyclopedia/en/Resources | ⏳ | |
| 8 | https://leekwars.com/encyclopedia/fr/La_map_de_d%C3%A9g%C3%A2ts | ✅ | **CRITICAL**: Danger map algorithm. Naive: for each my_cell → for each enemy → for each enemy_cell → for each weapon → if can_shoot: add_danger. EXTREMELY EXPENSIVE! Optimizations: 1) Check getOperations() and exit early, 2) Cache enemy stats outside loops, 3) Degrade resolution (even MP cells, interpolate = 4x savings), 4) "Once and for all" - precompute at turn 1: count cells that can shoot each cell. |
| 9 | https://leekwars.com/encyclopedia/fr/advanced_fight_description | ⏳ | |
| 10 | https://leekwars.com/help/documentation/getCellDistance | ⏳ | |
| 11 | https://leekwars.com/changelog | ✅ | **v2.42 (July 2024)**: WEAPON/CHIP USAGE LIMITS - `getWeaponMaxUses()`, `getChipMaxUses()`, `getItemUses(item)`. Forces multi-tool rotation! New effects on teleport/antidote/grapple. Java 17→21. **v2.43 (Dec 2025)**: Quantum Rifle. **v2.40 (Dec 2023)**: Bosses, Components, Crafting. Cores=more ops, RAM=more chips. |

## Leaderboards & Rankings

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 12 | https://leekwars.com/ranking/farmer/trophies | ⏳ | |
| 13 | https://leekwars.com/ranking?country=ie | ⏳ | |
| 14 | https://leekwars.com/team/1 | ⏳ | |
| 15 | https://leekwars.com/team/10000 | ⏳ | |
| 16 | https://leekwars.com/trophies/76155 | ⏳ | |
| 17 | https://leekwars.com/trophy/treasure | ⏳ | |

## Community Strategy Guides

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 18 | http://automacile.fr/apprenez-a-programmer-jouant-leekwars/ | ❌ | ECONNREFUSED - site down |
| 19 | https://carina.forumgaming.fr/t1782-leek-wars-guide-strategique-tank-spe-fuite-en-cours | ✅ | **CRITICAL**: Tank/Escape build: 75% HP, 20% STR, 5% AGI. Spark chip at 10-range for kiting. Levels 7-9: distance management. Level 10+: Bandage healing (2TP). Level 11+: Helmet shield (4TP, forces attack/heal tradeoff). Manual cooldown tracking. |
| 20 | https://carina.forumgaming.fr/t1772-leek-wars-jeu-de-combat-de-poireaux-et-de-prog-par-navigateur | ⏳ | |
| 21 | https://forums.jeuxonline.info/sujet/1260640/jeu-web-leek-wars-programmation-d-ia | ✅ | **CRITICAL**: Confirmed 1000+ lines needed for high-level AI. Top AIs use "arbres de possibilités" (decision trees), long-term strategies, and complex spell placement. Skill ceiling rivals Dofus PvP. |
| 22 | https://openclassrooms.com/forum/sujet/jeu-html5-php-leek-wars-programmation-d-ia | ⏳ | |

## GitHub Code & Tools

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 23 | https://github.com/pbondoer/leekwars | ⏳ | |
| 24 | https://github.com/pbondoer/leekwars/blob/master/main.leek | ✅ | **GOLDMINE**: "Silly Lemon 0.0.3" - Full 200-line AI with phases: movement, action, flee. Key patterns: getBestWeapon() calculates DPT across all weapons, inWeaponRange() checks LOS+distance, chipOrder priority array, life% threshold for healing (<30%), enemy life ratio comparison, flee phase with min-range counter tactics. |
| 25 | https://github.com/LeBezout/LEEK-WARS | ✅ | Java utility toolkit (v1.9.0): Auth, fight automation, register management, tournament enrollment, ranking retrieval. Uses REST endpoints like garden/start-solo-fight. Good for understanding API patterns. |

## Reddit Discussions

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 26 | https://www.reddit.com/r/reinforcementlearning/comments/xqbtmr/can_anyone_please_explain_modelfree_and/ | 🔒 | Blocked by WebFetch |
| 27 | https://www.reddit.com/r/gamedev/comments/1e07bow/turning_an_ais_existing_fsm_into_a_behavior_tree/ | ✅ | **ARCHITECTURE**: FSM 40 states = nightmare. BT: break into modular nodes, reuse as building blocks. One dev: 3-4 megalithic states → 10-12 BT nodes in 4 days. State is "implicit" in BT. Book ref: arxiv 1709.00084v6.pdf Section 2.2.3. Also mentions Utility AI - score behaviors, highest executes. |
| 28 | https://www.reddit.com/r/IndieGaming/comments/12izdvc/leek_wars_ai_programming_game_for_leeks/ | 🔒 | Blocked by WebFetch |

## YouTube Tutorials

| # | URL | Status | Summary |
|---|-----|--------|---------|
| 29 | https://www.youtube.com/watch?v=uKZuEGlXOUg | ⏳ | Summoner/bulb strategy tutorial |
| 30 | https://www.youtube.com/watch?v=UFkjGnWo_pk | ⏳ | Behavior tree AI patterns |
| 31 | https://www.youtube.com/watch?v=3y2ahAvV6XY | ⏳ | General LeekWars gameplay |

---

*Last updated: 2026-01-18*
