# Capital Allocation Audit — IAdonis L153, 41 unspent capital (S53)

**Date**: 2026-04-20 · **Budget**: 41 capital · **Baseline**: STR 452, RES 219, WIS 0, AGI 10, HP 1020, TP 14, MP 4

## Executive summary (TL;DR)

Compare the candidate 41-cap allocations against theory (formula-grounded marginal ROI) and peer empirics (leek_observations). Synthesis recommends a specific allocation after the sim-validation phase.

---

## Phase 1 — Theory (top-down)

### Formulas (parsed from Effect*.java)

- Damage: `(v1 + jet×v2) × (1 + max(0,STR)/100) × aoe × crit × targets × (1 + Power/100)`
- Abs Shield: `(v1 + jet×v2) × (1 + RES/100) × aoe × crit`
- Heal: `(v1 + jet×v2) × (1 + WIS/100) × aoe × crit × targets`
- Lifesteal: `damage_dealt × WIS/1000` — **ZERO at WIS=0**
- Crit rate: `AGI/1000` — AGI 10 → 1.0%, AGI 92 → 9.2%
- ShackleTP scales with CASTER's MAGIC — **WIS does NOT grant debuff resistance** (folklore busted; confirmed absent from Java source)

### Candidate allocations (41 cap)

| Candidate | Spend | Leftover | Stat delta | Effect delta |
|-----------|-------|----------|------------|--------------|
| **all_strength** | 40 | 1 | +20 STR → 472 | dmg_mult=5.72, dmg_mult_delta_pct=3.62 |
| **all_resistance** | 41 | 0 | +41 RES → 260 | shield_mult=3.6, shield_mult_delta_pct=12.85, shield_stack_abs=216.7 |
| **all_wisdom** | 41 | 0 | +82 WIS → 82 | heal_mult=1.82, lifesteal_rate_pct=8.2 |
| **all_agility** | 41 | 0 | +82 AGI → 92 | crit_rate_pct=9.2, exp_dmg_boost_pct=2.76 |
| **all_life** | 41 | 0 | +123 HP → 1143 | hp_total=1143, hp_delta_pct=12.06 |
| **mp_jump** | 40 | 1 | MP 4→5 (40 cap) + 1 cap leftover | mp=5 |
| **tp_jump** | 0 | 41 | TP 14→14 — UNAFFORDABLE (50 cap > 41 budget) | tp=14, affordable=False |
| **mix_mp_and_res** | 41 | 0 | MP 4→5 + RES 219→220 (1 residual) | mp=5, res=220 |
| **mix_res_and_wis** | 41 | 0 | +20 RES (20 cap) + +42 WIS (21 cap) | res=239, wis=42, shield_stack_abs=204.0, lifesteal_rate_pct=4.2 |
| **mix_res_and_agi** | 41 | 0 | +20 RES (20 cap) + +42 AGI (21 cap) | res=239, agi=52, crit_rate_pct=5.2, exp_dmg_boost_pct=1.56 |
| **mix_wis_and_agi** | 41 | 0 | +40 WIS (20 cap) + +42 AGI (21 cap) | wis=40, agi=52, lifesteal_rate_pct=4.0, crit_rate_pct=5.2 |

### Critical checks

**Stalemate-breaker**: NO — need 176 cap (have 41). Pure STR cannot break stalemates at our budget.
- Current Flame raw: 165.6
- To exceed 192 peer shield stack, need STR 540 (+88 pts = 176 cap).
- **Implication**: Pure-STR allocation does NOT fix the stalemate problem. The gap is 2.1× our budget.

**RES marginal return**: Linear returns; 12.9% stack increase. Each cap buys 1 RES at tier 200-400.
- Current shield stack: 192
- After +41 RES: 216.7 (+24.7 abs, +12.85%)

### Theory interpretation per stat

- **STR** (+20 → 472): damage mult 5.52→5.72 = **+3.6% damage/hit**. Flame goes 166→172. Tiny. Cost-per-point tier (2 cap/pt) makes STR the worst per-capital damage lever at our tier.
- **RES** (+41 → 260): shield stack 192→216 = **+12.9%**. Linear, predictable. Each +1 RES adds ~0.6 abs shield.
- **WIS** (0→82): heal amp +82%, **lifesteal 0%→8.2%**. Unlocks a mechanic that currently doesn't exist for us. Over a fight dealing 720 damage, +59 HP via lifesteal.
- **AGI** (10→92): crit rate 1%→9.2%. Expected damage boost **+2.76%** (crit × (1.3-1)). Also scales damage-return chips if we ever use them.
- **LIFE** (+123 HP → 1143): +12% raw HP. Corrects earlier plan error (3 HP/cap in 1000-1999 tier, not 2).
- **FREQ** (+41 → 141): longer chip buff durations. Small incremental value; low priority.
- **TP** (14→15 costs **50 cap** > 41 budget): UNAFFORDABLE.
- **MP** (4→5 costs 40 cap → 1 leftover): positional lever; question is whether v15 AI uses extra MP.

---

## Phase 2 — Empirics (bottom-up)

**Sample**: `leek_observations` filtered to L150-170, T350-500, observed within 60 days.
**N peers (distinct leeks)**: 10

### Peer stat distribution (L150-170, T350-500)

| Stat | n | min | p25 | median | p75 | max | mean | **IAdonis** | vs median |
|------|---|-----|-----|--------|-----|-----|------|-------------|-----------|
| life | 10 | 577 | 884 | 1121.5 | 1371 | 1682 | 1113.7 | **1020** | -101.5 |
| strength | 10 | 176 | 312 | 500.0 | 512 | 563 | 415.6 | **452** | -48.0 |
| resistance | 10 | 0 | 0 | 0.0 | 42 | 217 | 40.9 | **219** | +219.0 |
| wisdom | 10 | 0 | 0 | 45.0 | 108 | 502 | 98.2 | **0** | -45.0 |
| agility | 10 | 0 | 0 | 0.0 | 0 | 108 | 11.8 | **10** | +10.0 |
| magic | 10 | 0 | 0 | 0.0 | 10 | 202 | 22.2 | **0** | +0.0 |
| science | 10 | 0 | 0 | 0.0 | 0 | 110 | 17.0 | **0** | +0.0 |
| tp | 10 | 10 | 10 | 10.0 | 15 | 18 | 12.0 | **14** | +4.0 |
| mp | 10 | 3 | 3 | 3.5 | 5 | 6 | 4.0 | **4** | +0.5 |
| talent | 10 | 368 | 374 | 386.5 | 402 | 494 | 396.5 | **314** | -72.5 |
| level | 10 | 150 | 150 | 153.0 | 154 | 158 | 152.9 | **153** | +0.0 |

### Top-10 by talent in band

| leek_id | level | talent | LIFE | STR | RES | WIS | AGI | MAG | SCI | TP | MP |
|---------|-------|--------|------|-----|-----|-----|-----|-----|-----|-----|-----|
| 34706 | 158 | 494 | 577 | 317 | 217 | 176 | 0 | 10 | 0 | 18 | 5 |
| 9564 | 150 | 403 | 1371 | 511 | 0 | 0 | 0 | 10 | 0 | 10 | 5 |
| 29394 | 153 | 402 | 1682 | 500 | 38 | 48 | 0 | 0 | 0 | 10 | 3 |
| 3832 | 153 | 400 | 884 | 512 | 0 | 0 | 0 | 0 | 0 | 10 | 3 |
| 66062 | 154 | 387 | 1195 | 312 | 0 | 106 | 0 | 0 | 0 | 17 | 4 |
| 17350 | 153 | 386 | 1048 | 563 | 0 | 0 | 0 | 0 | 0 | 10 | 3 |
| 20743 | 150 | 379 | 1403 | 500 | 42 | 42 | 0 | 0 | 0 | 10 | 5 |
| 597 | 150 | 374 | 979 | 548 | 0 | 0 | 0 | 0 | 0 | 10 | 3 |
| 12377 | 155 | 372 | 1214 | 176 | 0 | 502 | 10 | 0 | 60 | 10 | 3 |
| 91277 | 153 | 368 | 784 | 217 | 112 | 108 | 108 | 202 | 110 | 15 | 6 |

### Peer signal interpretation (n=10, L150-170 T350-500)

Key findings from the actual peer distribution:

- **Our RES 219 is OUTLIER-HIGH**: 7/10 peers run RES 0. Median peer RES = 0. Only one peer (34706, T494, rank #1 in band) has RES 217 — same as us. Our defensive investment is already atypically deep. **Peer signal for more RES: negative**.
- **Our LIFE 1020 is BELOW median 1121.5**: we're -102 HP below peers. LIFE lever is validated.
- **Our WIS 0 is BELOW median 45**: 3/10 peers have meaningful WIS (176, 502, 108). The #1-talent peer (34706) runs WIS 176. Pure-STR glass-cannons (7/10) run WIS 0. **The archetype that climbs in this band includes WIS**.
- **Our TP 14 is ABOVE median 10**: only 2 peers match (15, 17) and one beats us (18). This is a rare advantage — don't dilute it.
- **Our AGI 10 is AT the median (0) +10**: only 1/10 has positive AGI (108). AGI is **not** a meta lever at our level.
- **Our STR 452 is BELOW median 500**: we're behind by ~48 STR. But closing this gap fully needs 96 cap (2× budget).

**The #1-talent in our band (34706, T494, L158)**: STR 317, RES **217**, WIS **176**, TP **18**, LIFE 577. A "fortress-magus" hybrid. Our RES already matches; **WIS 176 is the missing ingredient** that separates us from this archetype.

---

## Phase 3 — Synthesis

### Theory × Peer 2×2 grid (updated with real peer data)

| Stat | Theory | Peer signal | Verdict |
|------|--------|-------------|---------|
| **STR** | Weak (+3.6% dmg at 2 cap/pt) | We're -48 below median; closing needs 96 cap | Deprioritize at this budget |
| **RES** | Moderate (+12.9% shield stack, 24 abs) | **We're already an outlier at +219 over median** | Skip — diminishing returns, peer-inefficient |
| **WIS** | **Strong** (unlocks lifesteal 0→8.2%, heal amp +82%) | **#1 peer runs WIS 176; 3/10 peers invest** | **Top candidate** |
| **AGI** | Weak (+2.76% dmg via crit) | Peers overwhelmingly at 0 | Skip |
| **LIFE** | Moderate (+123 HP, 3 HP/cap tier) | We're -102 below median | Secondary candidate |
| **TP** | Strong (+1 whole chip/turn) | We're ABOVE median; rare advantage | Can't afford (50 cap > 41) |
| **MP** | Conditional on AI | Peers at median 3-4; we're fine | Skip |

### Candidate ranking (pre-sim)

1. **Pure WIS (+82)** — Strongest theory+peer convergence. Unlocks a mechanic we don't have (lifesteal). Matches the #1-talent peer archetype. Our 720-damage average → +59 HP/fight self-heal. Heal chips (Drip when bought, Bandage now) amplify 1.82×.
2. **WIS+LIFE mix** (+40 WIS at 20 cap + +63 HP at 21 cap=wait, LIFE tier 1000-1999 is 3 HP/cap → 21 cap = 63 HP. Total: WIS 40, LIFE +63 → 1083) — hedges between new mechanic (WIS) and peer-median gap (LIFE).
3. **Pure LIFE (+123 HP)** — closes the median gap, low-risk. But doesn't unlock any new capability.
4. **Pure RES** — peer-signal negative; skip.

### Sim validation (pending, next session)

Run 200-fight `compare_ais.py` for variants:
- A. Baseline (WIS 0) vs Pure-WIS (WIS 82)
- B. Baseline vs WIS+LIFE mix (WIS 40, LIFE 1083)
- C. Baseline vs Pure-LIFE (LIFE 1143)

Fixed opponent pool: ck_magnum1, ck_venom_sg, ck_flamethrower, pbondoer, arch_burst.

Gate: variant ≥ baseline WR (or tie). PySim is directional (46% real-game fidelity), so we accept "no regression" as green.

### Decision (pending sim validation)

**Current leaning**: **Pure WIS +82**. Theory+peer both point here. Fallback: if sim shows regression (e.g., lifesteal doesn't trigger enough in v15's force_engage mode), switch to **WIS 40 + LIFE +63 mix**.

---

## Phase 4 — Execute (pending user approval after sim)

Once decided, execution pattern:
```bash
leek build spend wisdom 82 --dry-run   # preview: expect 41 cap, RES unchanged
leek build spend wisdom 82             # commit (irreversible!)
leek build show                        # verify: capital 0, WIS 82
leek info leek 131321                  # confirm full new build
```

Post-spend snapshot → `data/monitoring/post_capital_audit_s53.json`.
One smoke fight with new build (ASK USER FIRST per Online Fight Protocol) → verify no regression.

---

## Notes & corrections from plan

- **HP cost was wrong in plan**: corrected to 3 HP/cap (not 2) until LIFE 2000 — changes `all_life` from +82 to +123.
- **TP 14→15 is unaffordable**: costs 50 cap, we have 41. The "TP jump" variant is a 2026-Q3 consideration, not now.
- **WIS does NOT give debuff resistance**: folklore busted by reading `EffectShackleTP.java` directly — it scales with caster's MAGIC, not target's WIS. WIS only amplifies heals + grants lifesteal.
- **AGI scales EffectDamageReturn**: if we ever equip a thorn/counter chip, AGI would compound. Not in our kit.

## Reproducibility

Re-run anytime with:
```bash
poetry run python scripts/capital_audit.py
poetry run pytest tests/test_capital_audit.py -v
```
Module: `src/leekwars_agent/capital_audit.py`. All cost curves parsed from `tools/leek-wars/src/model/leek.ts`. All effect formulas parsed from `tools/leek-wars-generator/.../Effect*.java`. Parse, don't rewrite.
