"""Capital allocation marginal-return calculator.

Parses the authoritative capital cost curve from `tools/leek-wars/src/model/leek.ts`
(the COSTS object) and computes:

  - max stat points buyable for a given capital budget
  - effect-delta for each candidate allocation (damage multiplier, shield multiplier,
    heal amp, crit rate, lifesteal rate, etc.)

Formulas below match the Java generator's Effect*.java classes:
  - Damage:  (v1 + jet*v2) × (1 + max(0,STR)/100) × aoe × crit × targets × (1 + Power/100)
  - AbsShield: (v1 + jet*v2) × (1 + RES/100) × aoe × crit
  - Heal: (v1 + jet*v2) × (1 + WIS/100) × aoe × crit × targets
  - Lifesteal: damage_dealt × WIS / 1000  (WIS=0 → ZERO lifesteal)
  - Critical rate: AGI / 1000   (AGI 10 → 1%, AGI 92 → 9.2%)
  - ShackleTP scales with CASTER's MAGIC, not target's WIS. Debuff-resistance-via-WIS
    is folklore — verified absent from the Java source.

Parse, don't rewrite: never hand-copy a value that lives in leek.ts or Effect*.java.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_LEEK_TS = Path(__file__).resolve().parents[2] / "tools" / "leek-wars" / "src" / "model" / "leek.ts"

# Stats whose cost curve is "step / capital / sup" (sup = stat points per capital unit)
_TIERED_STATS = {
    "life",
    "strength",
    "wisdom",
    "agility",
    "resistance",
    "science",
    "magic",
    "frequency",
    "cores",
    "ram",
    "tp",
    "mp",
}


@dataclass(frozen=True)
class CostTier:
    step: int  # threshold (stat value or step index) at which this tier starts
    capital: int  # capital per "block"
    sup: int  # stat points delivered per block

    @property
    def cap_per_point(self) -> float:
        return self.capital / self.sup


_cost_cache: dict[str, list[CostTier]] | None = None


def _parse_costs() -> dict[str, list[CostTier]]:
    """Parse the COSTS object from leek.ts into a dict of stat → [CostTier, ...]."""
    text = _LEEK_TS.read_text()
    # Grab the COSTS object body
    m = re.search(r"COSTS[^=]*=\s*\{(.*?)\n\}", text, re.DOTALL)
    if not m:
        raise RuntimeError("Could not locate COSTS block in leek.ts")
    body = m.group(1)

    costs: dict[str, list[CostTier]] = {}
    # Split into stat sections like "strength : [ ... ],"
    for stat_match in re.finditer(r"(\w+)\s*:\s*\[(.*?)\]", body, re.DOTALL):
        stat = stat_match.group(1)
        if stat not in _TIERED_STATS:
            continue
        tiers_raw = stat_match.group(2)
        tiers: list[CostTier] = []
        for t in re.finditer(
            r"\{\s*step\s*:\s*(\d+),\s*capital\s*:\s*(\d+),\s*sup\s*:\s*(\d+)\s*\}",
            tiers_raw,
        ):
            tiers.append(
                CostTier(step=int(t.group(1)), capital=int(t.group(2)), sup=int(t.group(3)))
            )
        if tiers:
            costs[stat] = tiers
    return costs


def get_costs() -> dict[str, list[CostTier]]:
    global _cost_cache
    if _cost_cache is None:
        _cost_cache = _parse_costs()
    return _cost_cache


# ── Budget resolver ────────────────────────────────────────────────


@dataclass(frozen=True)
class BuyResult:
    stat: str
    spent: int
    leftover: int
    points_bought: int
    new_value: int


def _tier_for(tiers: list[CostTier], current: int) -> CostTier:
    """Pick the tier that applies at `current` stat value (for non-staircase stats).

    For tiered stats (STR/RES/WIS/AGI/MAG/SCI/LIFE/FREQ), `step` is a stat-value
    threshold. The applicable tier is the one with the largest step ≤ current.
    """
    applicable = [t for t in tiers if t.step <= current]
    return applicable[-1] if applicable else tiers[0]


def _staircase_step(current: int, stat: str) -> int:
    """For staircase stats (TP/MP/Cores/RAM), the step index is `current - base`.

    Bases (from leek.ts): TP base = 10, MP = 3, cores = 1, ram = 6 (documented in CLAUDE.md
    capital reference). Each tier entry applies to ONE step.
    """
    bases = {"tp": 10, "mp": 3, "cores": 1, "ram": 6}
    return current - bases.get(stat, 0)


def buy_points(stat: str, current: int, budget: int) -> BuyResult:
    """Compute maximum points buyable for `budget` capital at `current` stat value.

    Returns BuyResult with spent/leftover/points_bought/new_value.

    - For tiered stats (STR/RES/WIS/AGI/MAG/SCI/LIFE/FREQ), iterates tier boundaries,
      greedily spending in the cheapest tier first.
    - For staircase stats (TP/MP/Cores/RAM), only the NEXT tier is relevant (they're
      stepwise, one point per tier).
    """
    costs = get_costs()
    if stat not in costs:
        raise ValueError(f"Unknown stat: {stat}")
    tiers = costs[stat]

    if stat in {"tp", "mp", "cores", "ram"}:
        # Staircase: consume one step at a time
        spent = 0
        pts = 0
        val = current
        while True:
            idx = _staircase_step(val, stat)
            if idx >= len(tiers):
                break
            tier = tiers[idx]
            if spent + tier.capital > budget:
                break
            spent += tier.capital
            pts += 1
            val += 1
        return BuyResult(
            stat=stat, spent=spent, leftover=budget - spent, points_bought=pts, new_value=val
        )

    # Tiered stats (STR/RES/WIS/AGI/MAG/SCI/LIFE/FREQ)
    spent = 0
    pts = 0
    val = current
    while spent < budget:
        tier = _tier_for(tiers, val)
        # Next tier threshold (if any) caps how many points we can buy at this tier
        next_boundary: int | None = None
        for t in tiers:
            if t.step > val:
                next_boundary = t.step
                break
        # Room in this tier (stat points):
        room_pts = (next_boundary - val) if next_boundary is not None else 10_000
        # Capital per point at this tier:
        cap_per_block = tier.capital  # capital per block
        sup_per_block = tier.sup  # stat points per block
        # How many blocks fit in remaining budget?
        remaining = budget - spent
        affordable_blocks = remaining // cap_per_block
        # How many blocks fit in remaining tier room?
        room_blocks = (room_pts + sup_per_block - 1) // sup_per_block  # ceil
        blocks = min(affordable_blocks, room_blocks)
        if blocks <= 0:
            break
        # But the LAST block may overshoot tier room — don't buy past boundary
        pts_from_blocks = blocks * sup_per_block
        if next_boundary is not None and val + pts_from_blocks > next_boundary:
            # Clip to exact boundary
            allowed_pts = next_boundary - val
            allowed_blocks = allowed_pts // sup_per_block
            if allowed_blocks == 0:
                break
            blocks = allowed_blocks
            pts_from_blocks = blocks * sup_per_block
        spent += blocks * cap_per_block
        pts += pts_from_blocks
        val += pts_from_blocks
    return BuyResult(
        stat=stat, spent=spent, leftover=budget - spent, points_bought=pts, new_value=val
    )


# ── Effect deltas ────────────────────────────────────────────────


def damage_multiplier(strength: int) -> float:
    """Damage scaling: (1 + max(0, STR)/100). Source: EffectDamage.java."""
    return 1.0 + max(0, strength) / 100.0


def shield_multiplier(resistance: int) -> float:
    """Abs-shield scaling: (1 + RES/100). Source: EffectAbsoluteShield.java."""
    return 1.0 + resistance / 100.0


def heal_multiplier(wisdom: int) -> float:
    """Heal scaling: (1 + WIS/100). Source: EffectHeal.java."""
    return 1.0 + wisdom / 100.0


def lifesteal_rate(wisdom: int) -> float:
    """Lifesteal fraction of damage dealt: WIS/1000. Source: EffectDamage.java lifeSteal."""
    return wisdom / 1000.0


def critical_rate(agility: int) -> float:
    """Crit probability: AGI/1000. Source: State.java generateCritical()."""
    return agility / 1000.0


def expected_crit_damage_boost(agility: int, critical_factor: float = 1.3) -> float:
    """Expected fractional damage increase from crits alone.

    crit_rate × (CRITICAL_FACTOR - 1). At CRITICAL_FACTOR=1.3, AGI 100 → 1% boost.
    """
    return critical_rate(agility) * (critical_factor - 1.0)


# ── Report helpers ───────────────────────────────────────────────


@dataclass
class StatSnapshot:
    strength: int
    resistance: int
    wisdom: int
    agility: int
    life: int
    tp: int
    mp: int
    frequency: int = 100
    science: int = 0
    magic: int = 0

    def with_update(self, **kwargs) -> "StatSnapshot":
        from dataclasses import replace
        return replace(self, **kwargs)


@dataclass(frozen=True)
class Allocation:
    """A candidate allocation: list of (stat, points_to_buy)."""
    legs: tuple[tuple[str, int], ...]

    def apply(self, snap: StatSnapshot, budget: int) -> tuple[StatSnapshot, int, list[BuyResult]]:
        """Apply legs sequentially. Returns (new_snapshot, leftover_capital, buy_results)."""
        remaining = budget
        results: list[BuyResult] = []
        new_snap = snap
        for stat, requested_pts in self.legs:
            if requested_pts == 0 or remaining <= 0:
                continue
            current = getattr(new_snap, "life" if stat == "life" else stat)
            r = buy_points(stat, current, remaining)
            # Clip to requested_pts if less than max affordable
            if r.points_bought > requested_pts:
                r = buy_points(stat, current, _budget_for_points(stat, current, requested_pts))
            results.append(r)
            remaining -= r.spent
            new_snap = new_snap.with_update(**{stat: r.new_value})
        return new_snap, remaining, results


def _budget_for_points(stat: str, current: int, target_pts: int) -> int:
    """Inverse: minimum capital needed to buy `target_pts` stat points at `current` value."""
    # Binary search / direct calc. Simpler: just compute by calling buy_points with ever-larger budgets.
    # For tiered stats this is straightforward because the cost curve is piecewise-linear.
    costs = get_costs()
    tiers = costs[stat]
    if stat in {"tp", "mp", "cores", "ram"}:
        spent = 0
        val = current
        for _ in range(target_pts):
            idx = _staircase_step(val, stat)
            if idx >= len(tiers):
                break
            spent += tiers[idx].capital
            val += 1
        return spent
    # Tiered stat: walk through tiers
    spent = 0
    pts_left = target_pts
    val = current
    while pts_left > 0:
        tier = _tier_for(tiers, val)
        next_boundary = None
        for t in tiers:
            if t.step > val:
                next_boundary = t.step
                break
        room = (next_boundary - val) if next_boundary is not None else pts_left
        pts_here = min(pts_left, room)
        # blocks needed to cover pts_here
        blocks = (pts_here + tier.sup - 1) // tier.sup  # ceil
        spent += blocks * tier.capital
        val += blocks * tier.sup
        pts_left -= blocks * tier.sup
    return spent
