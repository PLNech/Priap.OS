# LeekWars API Reference

> Extracted from `leek-wars/leek-wars` frontend source (2026-01-23)
> Base URL: `https://leekwars.com/api`

## Authentication
All authenticated endpoints require `Authorization: Bearer <token>` header.
Token obtained from `POST /farmer/login` response cookies.

---

## Implemented in `api.py`

### Auth & Farmer
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/farmer/login` | Login, returns token in cookie | ✅ |
| POST | `/farmer/disconnect` | Logout | ✅ |
| GET | `/farmer/get/{id}` | Get public farmer data | ✅ |
| GET | `/farmer/get-inventory` | Get all inventory items | ✅ |

### Leek Management
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/leek/get/{id}` | Get public leek data | ✅ |
| GET | `/leek/get-history/{id}/{page}/{count}` | Get fight history | ✅ |
| POST | `/leek/set-ai` | Set leek's AI | ✅ |
| POST | `/leek/add-chip` | Equip chip to leek | ✅ |
| POST | `/leek/add-weapon` | Equip weapon to leek | ✅ |
| DELETE | `/leek/remove-chip` | Remove chip from leek | ✅ |
| POST | `/leek/spend-capital` | Allocate stat points | ✅ |

### Garden (Fights)
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/garden/get` | Get garden state (fights remaining) | ✅ |
| GET | `/garden/get-leek-opponents/{id}` | Get solo fight opponents | ✅ |
| GET | `/garden/get-farmer-opponents` | Get farmer fight opponents | ✅ |
| POST | `/garden/start-solo-fight` | Start solo fight | ✅ |
| POST | `/garden/start-farmer-fight` | Start farmer fight | ✅ |

### Fight Data
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/fight/get/{id}` | Get fight replay data | ✅ |
| GET | `/fight/get-logs/{id}` | Get fight debug logs | 📝 stub |

### AI Management
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/ai/get/{id}` | Get AI code | ✅ |
| GET | `/ai/get-farmer-ais` | List farmer's AIs | ✅ |
| POST | `/ai/save` | Save AI code | ✅ |
| POST | `/ai/new` | Create new AI | ✅ |
| POST | `/ai/rename` | Rename AI | ✅ |

### Market & Crafting
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/market/get-items` | Get market listings | ✅ |
| GET | `/market/get-item-templates` | Get all item templates | ✅ |
| POST | `/market/buy-habs-quantity` | Buy items (fight packs) | ✅ |
| POST | `/market/sell-habs` | Sell items for habs | 📝 stub |
| GET | `/scheme/get-all` | Get all crafting recipes | ✅ |
| POST | `/item/craft` | Craft item from scheme | ✅ |

### Game Data
| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/constant/get-all` | Get game constants | ✅ |
| GET | `/chip/get-all` | Get all chips | ✅ |
| GET | `/weapon/get-all` | Get all weapons | ✅ |
| GET | `/function/get-all` | Get LeekScript functions | ✅ |

---

## Not Yet Implemented (Prioritized)

### Tournament (🔴 High Priority - #0110)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/leek/register-tournament` | Register leek for tournament |
| POST | `/leek/unregister-tournament` | Unregister from tournament |
| POST | `/farmer/register-tournament` | Register farmer for tournament |
| POST | `/farmer/unregister-tournament` | Unregister farmer |
| GET | `/tournament/range-br/{range}` | Get battle royale brackets |

### Garden Extensions (🟡 Medium Priority - #0109)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/garden/start-solo-challenge` | Start solo challenge fight |
| POST | `/garden/start-farmer-challenge` | Start farmer challenge |
| POST | `/garden/start-team-fight` | Start team fight |
| GET | `/garden/get-solo-challenge/{id}` | Get challenge details |
| GET | `/garden/get-composition-opponents/{id}` | Get team opponents |

### Leek Extensions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/leek/add-component` | Add component to leek |
| POST | `/leek/move-component` | Rearrange components |
| POST | `/leek/set-hat` | Set cosmetic hat |
| POST | `/leek/use-potion` | Use potion item |
| POST | `/leek/register-auto-br` | Auto-register for BR |
| GET | `/leek/get-level-popup/{id}` | Get level-up rewards |

### Team
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/team/register-tournament` | Register team for tournament |
| POST | `/team/create-composition` | Create team composition |
| POST | `/team/move-leek` | Move leek between comps |

### Ranking
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ranking/{type}/{page}` | Get leaderboard page |
| GET | `/ranking/fun` | Get fun rankings |
| POST | `/ranking/search` | Search rankings |
| GET | `/talent/leek` | Get talent rankings |
| GET | `/talent/farmer` | Get farmer talent rankings |

### Testing/Simulation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/test-scenario` | Run AI in test scenario |
| POST | `/test-scenario/new` | Create test scenario |
| GET | `/test-scenario/get-all` | Get all test scenarios |
| POST | `/test-leek/new` | Create test leek |
| POST | `/test-map/new` | Create test map |

---

## Request Formats

### Login
```python
POST /farmer/login
data={"login": email, "password": pass, "keep_connected": "true"}
# Token returned in Set-Cookie header
```

### Craft Item
```python
POST /item/craft
data={"scheme_id": 15}  # Scheme IDs 1-60
# Returns: {id, template, time, quantity}
```

### Spend Capital
```python
POST /leek/spend-capital
data={"leek_id": 131321, "characteristics": '{"strength": 10}'}
# Note: characteristics is JSON string, not object!
```

### Start Fight
```python
POST /garden/start-solo-fight
data={"leek_id": 131321, "target_id": 123456}
# Returns: {"fight": fight_id}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request / limit reached |
| 401 | Unauthorized / token expired |
| 402 | Not enough habs/crystals |
| 404 | Resource not found |
| 429 | Rate limited |

---

## Notes

- Crafting recipes are in `tools/leek-wars/src/model/schemes.ts`
- Item templates are in `tools/leek-wars/src/model/items.ts`
- All timestamps are Unix epoch seconds
- Habs item ID = 148 (used in recipes)
