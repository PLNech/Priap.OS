# Data Architecture

## Database Overview

This document describes the fight data architecture for Priap.OS.

## Two Databases: Purpose & Status

| Database | Fights | Purpose | Schema |
|----------|--------|---------|--------|
| `data/fights.db` | 133 (L38 era) | Legacy CLI fight history | Minimal, local-only |
| `data/fights_meta.db` | 4,394+ | Scraper + Analytics | Rich (observations, opponents, metrics) |

### Decision: `fights_meta.db` is Canonical

**Rationale:**

1. **Rich schema**: Includes `leek_observations`, `opponents`, `alpha_strike_metrics`
2. **Analytics-ready**: Pre-computed aggregates for level brackets, equipment stats
3. **Opponent tracking**: Full opponent database with archetype inference
4. **Scraper integration**: Designed for the scrape → analyze workflow
5. **Active development**: All new features target this schema

### Note on `fights.db` Backfill

**Status**: BLOCKED - 133 older fights (IDs 50817188-50900766) require authentication.

```bash
$ sqlite3 data/fights.db "SELECT MIN(id), MAX(id) FROM fights;"
50817188|50900766

$ curl https://leekwars.com/api/fight/get/50817188
401 Unauthorized
```

Older fights are only accessible via authenticated session. Options:
1. Keep fights.db as historical reference (read-only)
2. Login to LeekWars to backfill authenticated fights
3. Accept gap in historical data (4,392+ recent fights available)

## Schema Summary

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `fights` | Fight metadata | winner, duration, type, context |
| `leek_observations` | Per-fight stats | tp, mp, strength, agility, frequency, damage |
| `opponents` | Opponent tracking | win_rate, archetype, common_chips/weapons |
| `alpha_strike_metrics` | Opening analysis | tp_efficiency, opening_buffs, ponr_turn |
| `level_stats` | Bracket analytics | fight_count, mean_talent, avg_duration |
| `equipment_stats` | Equipment win rates | item_name, win_count, total_damage |

### Indexes

```sql
-- Fight queries
idx_fights_date, idx_fights_type, idx_fights_context

-- Leek observation queries
idx_leek_obs_level, idx_leek_obs_leek

-- Opponent queries
idx_opponents_name, idx_opponents_last_seen, idx_opponents_archetype
```

## Archetype Inference

Opponents are classified into four archetypes based on fight behavior:

| Archetype | Key Indicators | Typical Behavior |
|-----------|-----------------|------------------|
| `rusher` | STR-focused build, fast fights | Close-combat, wins early |
| `kiter` | AGI-focused build, high MP | Runs away, prolongs fights |
| `tank` | High frequency, long fights | Outlasts opponents via attrition |
| `balanced` | No strong pattern | Flexible, adapts to situation |

### Classification Algorithm

The classifier uses scoring based on:

1. **STR/AGI ratio** (>1.5 = STR build, <0.8 = AGI build)
2. **Fight duration** (<=5 = fast, >=12 = slow)
3. **Frequency** (>1.2x median = high frequency)

**Scoring rules:**

```python
# Rusher: STR-focused + fast fights
if is_str_build: score_rusher += 2
if is_fast: score_rusher += 2

# Kiter: AGI-focused
if is_agi_build: score_kiter += 3
if avg_mp > 8: score_kiter += 1

# Tank: High frequency + slow fights
if is_high_freq: score_tank += 2
if is_slow: score_tank += 2
```

Archetype with score >= 4 wins; otherwise `balanced`.

### Distribution (Current)

```
balanced: 2423 (86%)
rusher:    197 (7%)
kiter:     101 (3.5%)
tank:       98 (3.5%)
```

This distribution is reasonable: most players are balanced, with specialists being less common.

## Usage

### Python API

```python
from src.leekwars_agent.scraper import FightDB

db = FightDB("data/fights_meta.db")

# Query opponent stats
opp = db.get_opponent(leek_id=12345)
print(f"WR: {opp['win_rate']:.1%}, Archetype: {opp['archetype']}")

# List opponents by archetype
rushers = db.get_opponents_by_win_rate(min_fights=3, ascending=True)
```

### CLI Commands

```bash
# Opponent stats
leek opponent stats "OpponentName"
leek opponent hardest --top 10
leek opponent archetype kiter

# Database status
leek opponent status
```

## Maintenance

### Re-run Archetype Inference

If archetype logic changes:

```bash
poetry run python -c "
from src.leekwars_agent.scraper import FightDB
from datetime import datetime

db = FightDB('data/fights_meta.db')
conn = db._get_conn()

for row in conn.execute('SELECT leek_id FROM opponents'):
    arch = db.infer_opponent_archetype(row['leek_id'])
    if arch:
        conn.execute('UPDATE opponents SET archetype = ?, updated_at = ? WHERE leek_id = ?',
            (arch, datetime.utcnow().isoformat(), row['leek_id']))
conn.commit()
db.close()
"
```

### Data Quality Checks

```sql
-- Check for NULL stats (data quality issue)
SELECT COUNT(*) FROM leek_observations WHERE tp IS NULL;

-- Check archetype distribution
SELECT archetype, COUNT(*) FROM opponents GROUP BY archetype;

-- Opponents with 3+ fights against us
SELECT * FROM opponents WHERE total_fights >= 3 ORDER BY win_rate ASC;
```