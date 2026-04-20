# Session 53 Critical Path — Sim as Lab, Reality as Oracle

> Framing: PySim correlation study (#120) capped at 54% agreement. The proxy-AI
> hypothesis (#128) was falsified at 46%. We've exhausted the cheap sim
> fidelity wins. **Next lane: extract higher-quality signal from real game
> data, gate ship decisions on real A/B, and keep sim strictly as iterative
> A/B lab between our own AIs.**

## The Three Lanes

### Lane A — Ship Gate (blocks v15 decision)
**#0316** Real v14 vs v15 A/B framework ⚙️

The only gate that actually predicts ladder outcome. Alternating-day deployment,
sequential stopping at 95% CI excluding zero, minimum 200 fights.

Dependencies: v15 exists (#57 in progress), deploy tooling (mature).
ETA to ship signal: **~4 days of 50/day fight budget** once running.

### Lane B — Foundation (enables everything else)
**#0311** Decisive-moment detector 📊

Parse 5,960 existing fights for HP crossover, shield depletion, TP shackle,
range lock, chip exhaustion. Store annotations joined to `fights_meta`.

No dependencies. Unblocks #0314, #0315, and informs #0316 metric design.

### Lane C — New Signal (the peer-intelligence bet)
**#0312** Neighborhood tracker + peer fight ingestion 📊
→ **#0315** Cross-replay diagnostic 📊

Track rank-neighborhood climbers (±2000, L140-180). Ingest their winning
fights. Replay with v14 in their slot — see where our AI diverges from
climber behavior at decisive moments.

**Critical safety check**: before trusting cross-replay on peer fights, run it
on 20 of OUR own wins. If PySim can't reproduce our wins ≥70%, the tool is
unsafe for peer diagnosis. Build on rock, not sand.

### Lane D — Deferred (expensive, not gating)
**#0317** v14 execution fidelity audit 🔧

Quantify PySim↔real per-turn gap in ops/TP/chips/moves. Only worth doing if
someone needs PySim as an *absolute* oracle, not a relative A/B lab. Not on
S53 critical path.

## Dependency Graph

```
#0311 (detector) ─┐
                  ├─→ #0315 (cross-replay)
#0312 (peers) ────┘
                      
#0316 (A/B) ────── independent, runs in parallel

#0317 (fidelity audit) ───── deferred, optional
```

## Proposed Session 53 Schedule

| Slot | Task | Why this slot |
|------|------|---------------|
| AM-1 | **#0316** A/B framework scaffolding (half day) | Start accumulating real data ASAP — every day delayed is a day of noise |
| AM-2 | **#0311** decisive-moment detector v1 (half day) | Parallel lane, no shared resources |
| PM-1 | **#0311** validation on 10 manually-inspected fights | Gate before scale |
| PM-2 | **#0312** tracker extension — identify 20 climbers | Unblock Lane C |
| End  | **#0315** cross-replay prototype on 3 OUR wins | Smoke-test baseline before peer work |

**Success criteria for S53**:
- A/B test running (or ready to deploy next fight batch)
- Decisive-moment detector producing annotations for 80% of fights
- 20 climbers identified with 30d rank trajectories
- Cross-replay prototype reproduces our wins on ≥2/3 smoke tests

## What NOT to Do Next Session

- **Don't** write more proxy AIs for PySim correlation. Falsified path (#128).
- **Don't** deep-dive #0317 fidelity audit. Cheap hypotheses exhausted; deeper work costs more than the benefit.
- **Don't** design v15 further in isolation. Gate it on A/B signal (#0316).
- **Don't** scrape all top-1000 peers — throttle to neighborhood L140-180, ~50 climbers max.

## Statistical Reality Check

200 A/B fights with true WR delta 7pp has 95% CI ≈ ±7pp. **We may need 500 fights for decisive signal.** Design #0316 to stop early on big deltas but continue on small ones; don't ship on the first significant peek.

## The Strategic Frame (one paragraph)

We've proven the sim is a *lab*, not an *oracle*. Use it for rapid A/B between
our own AIs — cheap, parallel, directional. Use real fights (gated by A/B) for
ship decisions. Use real peer fights (mined via #0311→#0315) to learn what
climbers do differently *in the moments that matter*, without ever reading
their source. That's the system. Session 53 builds its scaffolding.

> *"Ụwa bụ ahịa, onye zụta ọnụ nke ya, ọ laa."* — Igbo: "The world is a
> marketplace; each buys what they can and goes home." We trade sim cycles
> and context for measurement; measurement buys us direction.
