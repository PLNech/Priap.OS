# Trophy Hunter AIs 🏆

Specialized AIs designed to unlock specific trophies through in-fight behavior.

## Available AIs

| AI | Trophy | Reward | Strategy |
|----|--------|--------|----------|
| `mathematician.leek` | Mathematician (#87) | 250,000 | Walk on 50 prime cells (2,3,5,7,11...) |
| `wanderer.leek` | Wanderer (#80) | 2,500 | Travel 100m in one fight |
| `executor.leek` | Executor (#77) | 400 | Win in < 5 turns (alpha strike) |
| `patient.leek` | Patient (#78) | 2,500 | Win in > 60 turns (kite forever) |
| `static.leek` | Static (#76) | 10,000 | Win without moving |
| `pacifist.leek` | Pacifist (#23) | 10,000 | Win without dealing damage |
| `xii_ops.leek` | XII (#188) | 810,000 | Consume exact op count (experimental) |

## Usage

```bash
# Test locally first
poetry run python scripts/compare_ais.py trophy_hunters/mathematician.leek fighter_v10.leek -n 10

# Deploy to hunt
leek ai deploy ais/trophy_hunters/mathematician.leek
```

## Progress Tracking

Check trophy progress with:
```bash
leek trophy status
```

## Notes

- **mathematician**: Cumulative across fights. Deploy and let it farm.
- **wanderer**: Single-fight achievement. May take several attempts.
- **static/pacifist**: Requires favorable matchups. Test in challenges first.
- **xii_ops**: Unknown exact requirement. Experimental.

## Trophy Combinations

Some trophies conflict - you can't be static AND wanderer. Plan your farming sessions!

Good combo: `mathematician` + regular combat (primes visited as side effect)
