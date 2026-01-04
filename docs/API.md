# LeekWars API Documentation

Base URL: `https://leekwars.com/api/`

## Authentication

### Token Format (v2.0.2+)
- JWT-based authentication
- Pass token via header: `Authorization: Bearer <token>`

### Login
```
POST /farmer/login
Content-Type: application/x-www-form-urlencoded

login=<username>&password=<password>&keep_connected=true
```

**Response:** Token returned in `Set-Cookie: token=<jwt>` header.
```json
{
  "farmer": {
    "id": 124831,
    "name": "PriapOS",
    "leeks": { "131321": { "id": 131321, "name": "IAdonis", ... } },
    "fights": 99,
    "habs": 5045,
    ...
  }
}
```

### Logout
```
POST /farmer/disconnect
Authorization: Bearer <token>
```

---

## Farmer Endpoints

### Get Farmer
```
GET /farmer/get/<farmer_id>
```

**Response includes `fight_history`** (recent ~50 fights):
```json
{
  "farmer": {
    "fight_history": [
      {
        "id": 50886949,
        "leeks1": [{"id": 131321, "name": "IAdonis"}],
        "leeks2": [{"id": 130254, "name": "MrLeeks"}],
        "winner": 1,           // 1=team1, 2=team2, 0=draw
        "status": 2,           // 2=completed
        "date": 1767539670,    // Unix timestamp
        "result": "win",       // "win"|"defeat"|"draw"
        "context": 2,          // 2=garden
        "type": 0,             // 0=solo
        "chests": 0,
        "trophies": 0,
        "levelups": 0,
        "rareloot": 0
      }
    ],
    "fights": 95  // Remaining garden fights today
  }
}
```

### Get Full Fight History (BETTER!)
```
GET /history/get-farmer-history/{farmer_id}
```

Returns **ALL** fights (not just recent 50). No auth required.
```json
{
  "fights": [
    { "id": 50886949, "result": "win", ... },
    // ALL fights ever
  ]
}
```

**NOTE**: `/farmer/get/{id}` → `fight_history` only returns ~50 recent. Use `/history/get-farmer-history/` for full history.

### Get Connected Farmer (authenticated)
```
GET /farmer/get-connected/<token>
```

### Update Farmer
```
POST /farmer/update
Authorization: Bearer <token>
```

---

## Leek Endpoints

### Get Leek
```
GET /leek/get/<leek_id>
```

### Get Private Leek Data (authenticated)
```
GET /leek/get-private/<leek_id>/<token>
```

### Leek Registers (persistent storage, 100 items max)
```
GET /leek/get-registers/<leek_id>/<token>
POST /leek/set-register/<leek_id>/<key>/<value>/<token>
DELETE /leek/delete-register/<leek_id>/<key>/<token>
```

### Leek Equipment
```
POST /leek/add-chip
POST /leek/add-weapon
POST /leek/remove-chip
POST /leek/remove-weapon
POST /leek/set-ai
POST /leek/set-hat
```

### Tournaments
```
POST /leek/register-tournament/<leek_id>/<token>
```

---

## Garden (Combat Arena)

### Get Garden State
```
GET /garden/get
Authorization: Bearer <token>
```

### Get Opponents
```
GET /garden/get-leek-opponents/<leek_id>
GET /garden/get-farmer-opponents
GET /garden/get-composition-opponents/<compo_id>
Authorization: Bearer <token>
```

**Opponents Response:**
```json
{
  "opponents": [
    { "id": 120294, "name": "Nastyca142010", "level": 1, "talent": 100, ... }
  ]
}
```

### Start Fights (v2.31.0+, POST)
```
POST /garden/start-solo-fight
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

leek_id=<leek_id>&target_id=<target_id>
```

```
POST /garden/start-farmer-fight
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

target_id=<target_id>
```

```
POST /garden/start-team-fight
Authorization: Bearer <token>
Content-Type: application/x-www-form-urlencoded

composition_id=<compo_id>&target_id=<target_id>
```

---

## Fight Endpoints

### Get Fight
```
GET /fight/get/<fight_id>
```

**Response:** Full fight data including replay.
```json
{
  "id": 50854680,
  "winner": 1,        // 1=team1, 2=team2, 0=draw
  "status": 2,        // 2=completed
  "type": 0,          // 0=solo, 1=farmer, 2=team
  "leeks1": [...],
  "leeks2": [...],
  "report": { "duration": 10, "win": 1, ... },
  "data": { "leeks": [...], "map": {...}, "actions": [...] }
}
```

### Fight Data Structure (`data` field)

```json
{
  "leeks": [
    {
      "id": 0,
      "name": "IAdonis",
      "team": 1,
      "cellPos": 525,
      "life": 100, "tp": 10, "mp": 3,
      "strength": 0, "agility": 0, ...
    }
  ],
  "map": {
    "type": 0,
    "width": 18, "height": 18,
    "obstacles": [...]
  },
  "actions": [...],  // Turn-by-turn actions
  "dead": { "131321": false, "120294": true },
  "ops": { "0": 55410, "1": 55410 }
}
```

### Action Encoding

Actions are arrays: `[action_type, entity_id, ...params]`

**Combat Actions:**
| Code | Action | Format |
|------|--------|--------|
| 0 | START_FIGHT | `[0]` |
| 4 | END_FIGHT | `[4]` |
| 5 | PLAYER_DEAD | `[5, entity_id]` |
| 6 | NEW_TURN | `[6, turn_number]` |
| 7 | LEEK_TURN | `[7, entity_id]` |
| 8 | END_TURN | `[8, entity_id, tp, mp]` |
| 9 | SUMMON | `[9, ...]` |
| 10 | MOVE_TO | `[10, entity_id, dest_cell, [path_cells]]` |
| 11 | KILL | `[11, ...]` |
| 12 | USE_CHIP | `[12, entity_id, chip_id, target, ...]` |
| 13 | SET_WEAPON | `[13, entity_id]` |
| 14 | STACK_EFFECT | `[14, ...]` |
| 15 | CHEST_OPENED | `[15, ...]` |
| 16 | USE_WEAPON | `[16, entity_id, target, ...]` |

**Damage/Heal (100-112):**
| Code | Action |
|------|--------|
| 100 | LOST_PT (TP) |
| 101 | LOST_LIFE |
| 102 | LOST_PM (MP) |
| 103 | HEAL |
| 104 | VITALITY |
| 105 | RESURRECT |
| 106 | LOSE_STRENGTH |
| 107 | NOVA_DAMAGE |
| 108 | DAMAGE_RETURN |
| 109 | LIFE_DAMAGE |
| 110 | POISON_DAMAGE |
| 111 | AFTEREFFECT |
| 112 | NOVA_VITALITY |

**Misc (200s):** 201=LAMA, 203=SAY, 205=SHOW_CELL

**Effects (300s):** 301=ADD_WEAPON_EFFECT, 302=ADD_CHIP_EFFECT, 303=REMOVE_EFFECT, 304=UPDATE_EFFECT, 306=REDUCE_EFFECTS, 307=REMOVE_POISONS, 308=REMOVE_SHACKLES

**System (1000s):** 1000=ERROR, 1001=MAP, 1002=AI_ERROR

### Get Fight Logs
```
GET /fight/get-logs/<fight_id>
```

---

## Team Endpoints

### Get Team
```
GET /team/get/<team_id>
```

### Get Private Team Data (authenticated)
```
GET /team/get-private/<team_id>/<token>
```

### Tournament Registration
```
POST /team/register-tournament/<compo_id>/<token>
```

---

## Ranking Endpoints

### Get Rankings
```
GET /ranking/get/<category>/<order>/<page>
```

### Get Farmer Rank
```
GET /ranking/get-farmer-rank/<farmer_id>/<order>
```

### Get Leek Rank
```
GET /ranking/get-leek-rank/<leek_id>/<order>
```

### Fun Rankings
```
GET /ranking/fun/<token>
```

---

## Trophy Endpoints

### Get Farmer Trophies
```
GET /trophy/get-farmer-trophies/<farmer_id>/<lang>/<token>
```

### Get All Trophies
```
GET /trophy/get-all
```

---

## Static Data Endpoints

### Game Constants
```
GET /constant/get-all
```

### Chips
```
GET /chip/get-all
```

### Weapons
```
GET /weapon/get-all
```

### Hats
```
GET /hat/get-all
```

### Potions
```
GET /potion/get-all
```

### Functions (LeekScript API)
```
GET /function/get-all
```

---

## Version & Changelog

### Get Version
```
GET /leek-wars/version
```

### Get Changelog
```
GET /changelog/get/<lang>
```

---

## API Version History

| Version | Changes |
|---------|---------|
| v2.31.0 | `farmer/login`, `farmer/disconnect`, `garden/start-*-fight` changed to POST |
| v2.0.2  | JWT authentication via `Authorization: Bearer <token>` header |
| v1.92   | Added opponent discovery endpoints |
| v1.9.0  | Multiple breaking changes |

---

## Resources

- [Official LeekWars GitHub](https://github.com/leek-wars)
- [Fight Generator (Java)](https://github.com/leek-wars/leek-wars-generator)
- [LeekScript Language](https://github.com/leek-wars/leekscript)
- [Java Utilities (LeBezout)](https://github.com/LeBezout/LEEK-WARS)
- [JavaScript API Wrapper](https://github.com/johnoppenheimer/leek-api)
