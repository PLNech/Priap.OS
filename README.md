# Priap.OS

An experiment in automated game-playing: can we reach **Top 10** in [LeekWars](https://leekwars.com) through systematic iteration rather than grinding?

[→ See current rank](https://leekwars.com/farmer/124831)

## The Hypothesis

Online fights are scarce (~50/day free). Offline simulation is unlimited (~20 fights/sec).

**If we can validate strategies 13,000x faster offline, we should climb faster than manual players.**

## The Flywheel

```
Fight Online → Collect Data → Analyze Losses → Improve AI Offline → Deploy
     ↑                                                              ↓
     └──────────────────────────────────────────────────────────────┘
```

Every online fight is data collection, not experimentation. Experimentation happens offline.

## The Method: AGORA

Complex problems decompose into parallel workstreams. Workers coordinate via `AGORA.md`:

1. Orchestrator defines strands (self-contained tasks)
2. Workers claim strands, report progress
3. Workers mark **VERIFY** when done
4. Orchestrator tests, then marks **DONE**

No heroics. Small steps. Compound progress.

## Getting Started

```bash
# Install
poetry install

# Offline A/B test (unlimited)
poetry run python scripts/compare_ais.py ais/fighter_v11.leek ais/archetype_rusher.leek -n 100

# CLI for online operations
poetry run leek --help
poetry run leek info leek          # Stats
poetry run leek fight status       # Fights remaining
```

## Project Layout

```
ais/                    # LeekScript AI files
src/leekwars_agent/     # Core library (api, simulator, parser)
scripts/                # Automation tools
AGORA.md                # Multi-agent coordination
CLAUDE.md               # Developer guide
docs/research/          # Analysis, findings, meta studies
```

## Philosophy

- **Offline-first**: Never test online what you can test offline
- **Data over intuition**: Every claim needs evidence
- **Small commits**: Ship fast, iterate faster
- **Tooling compounds**: Time spent on infrastructure pays dividends

## License

MIT
