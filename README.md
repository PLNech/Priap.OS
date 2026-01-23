# Priap.OS

LeekWars AI agent aiming for **Top 10 ladder ranking**.

## Quick Start

```bash
# Install dependencies
poetry install

# Run daily fights
poetry run python scripts/auto_daily_fights.py

# Compare AI versions offline
poetry run python scripts/compare_ais.py v1.leek v2.leek -n 1000
```

## Strategy

- **Online fights**: 150/day (scarce)
- **Offline fights**: 1.8M/day potential (21.5/sec)
- **Leverage ratio**: 13,000:1

Never test online what we can test offline.

## Project Structure

```
src/leekwars_agent/   # Core library (API, simulator, analysis)
scripts/              # Automation scripts
ais/                  # LeekScript AI files
tools/                # External tools (generator, leekscript)
data/                 # Fight data, configs
```

## Current Status

- **Level**: 27
- **AI**: v8 "Architect" (subsystem-based)
- **Automation**: GitHub Actions 3x daily

See `CLAUDE.md` for detailed project context.
