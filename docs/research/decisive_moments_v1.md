# Decisive-Moment Detector v1 — HP Crossover

> First-pass corpus scan over 3,091 solo matchmaking fights (fights_meta.db).
> Detector: `leekwars_agent.decisive_moments`. CLI: `leek moments {scan,list,report}`.

## Definition

A `hp_crossover` moment is the turn where:

1. The eventual winner's HP ratio (current/max) first strictly exceeded the eventual loser's, AND
2. This lead held for all subsequent turns, AND
3. At some prior turn, the eventual loser was *strictly* ahead on HP ratio.

Condition (3) is what distinguishes a real momentum flip from a wire-to-wire
win where the winner simply dealt the first damage. Without it, roughly
two-thirds of fights get falsely flagged — most fights start tied at 100%,
so the first damage creates a "crossover" that wasn't really a comeback.

## Corpus results

- **3,091 solo matchmaking fights** scanned.
- **796 (25.7%)** had a crossover moment.
- **2,295 (74.3%)** were wire-to-wire wins (or draws) — the winner never trailed.

### Crossover-turn distribution

| Turn | Count | Share |
|-----:|------:|------:|
| 3    | 72    | 9.0%  |
| 4    | 125   | 15.7% |
| 5    | 200   | 25.1% |
| 6    | 138   | 17.3% |
| 7    | 104   | 13.1% |
| 8    | 61    | 7.7%  |
| 9    | 36    | 4.5%  |
| 10+  | 60    | 7.5%  |

Median crossover: **turn 5**. Mean: ~6.4. Long tail to turn 43 in rare cases.

## Interpretation

- A quarter of fights are actual comebacks. The other 74% are decided by who
  connects first — consistent with LeekWars' first-strike-heavy combat
  (high damage, small HP pools at low-mid levels).
- The turn-5 modal crossover aligns with typical combat pacing: turns 0–2
  are positioning/buffing, turns 3–4 see the first exchanges, and by turn 5
  one side is clearly ahead.
- This detector is the foundation for **#0315 cross-replay diagnostic**:
  when we replay a peer's winning fight with our AI in the peer's slot, the
  question becomes "at the peer's crossover turn, did our AI behave the
  same way, or did it diverge?" Without the annotation, we'd have to compare
  every turn — noise overwhelms signal.

## v2 backlog

Not yet implemented but on the roadmap:

- **shield_depletion** — turn when active absolute shields drop to 0.
  Needs tracking shield applications (chip casts) and expiries (turn counters).
- **tp_shackle** — turn when TP usage is severely constrained (post-Tranq).
- **range_lock** — turn when distance crosses outside weapon min/max range.
- **chip_exhaustion** — turn when a key chip runs out of uses (Shield, Helmet,
  Armor — most have 1–2 uses/fight).

These add context: a crossover at turn 5 "because loser ran out of Shield"
is a different signal than "because winner landed Flame crit."

## Validation

5 random annotated fights manually inspected (see `test_decisive_moments.py`
for synthetic cases). Each annotation's HP snapshot at the crossover turn
matched the action-log reconstruction within 1 HP (rounding from partial
poison ticks).
