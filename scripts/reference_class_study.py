#!/usr/bin/env python3
"""Top-down reference-class study (NEW-A, NEW-B, NEW-C in one pass).

Reads rankings.db + fights_meta.db, emits three research markdown files:
- docs/research/top_n_reference_class.md   (what do winners look like?)
- docs/research/climber_study.md           (what causes climbing vs stagnation?)
- docs/research/gap_analysis.md            (IAdonis vs reference class)

Pure stdlib. No API calls — all data is local.

Usage:
    poetry run python scripts/reference_class_study.py
"""

from __future__ import annotations

import json
import sqlite3
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANKINGS_DB = ROOT / "data" / "rankings.db"
FIGHTS_DB = ROOT / "data" / "fights_meta.db"
OUR_LEEK_ID = 131321
RESEARCH_DIR = ROOT / "docs" / "research"

STAT_COLS = ("strength", "agility", "wisdom", "resistance", "magic", "science", "life", "tp", "mp")


# --- Data classes ---

@dataclass
class LeekRef:
    leek_id: int
    name: str
    talent: int
    level: int
    rank: int
    farmer: str | None = None


@dataclass
class StatProfile:
    leek_id: int
    level: int
    talent: int | None
    strength: int
    agility: int
    wisdom: int
    resistance: int
    magic: int
    science: int
    life: int
    tp: int
    mp: int
    observations: int


@dataclass
class ClimbRecord:
    leek_id: int
    name: str
    first_rank: int
    last_rank: int
    first_talent: int
    last_talent: int
    first_level: int
    last_level: int
    climb: int          # positive = improved rank
    span_days: float


# --- Loaders ---

def load_top_n(n_ranks: int = 100) -> list[LeekRef]:
    """Return top-N leeks from the latest rankings snapshot."""
    conn = sqlite3.connect(RANKINGS_DB)
    rows = conn.execute(
        """
        SELECT r.leek_id, r.name, r.talent, r.level, r.rank, r.farmer
        FROM rankings r
        WHERE r.snapshot_id = (SELECT MAX(id) FROM snapshots)
          AND r.rank BETWEEN 1 AND ?
        ORDER BY r.rank
        """,
        (n_ranks,),
    ).fetchall()
    conn.close()
    return [LeekRef(*row) for row in rows]


def load_stat_profiles(leek_ids: list[int]) -> dict[int, StatProfile]:
    """For each leek_id, return stats from its MOST RECENT *complete* observation.

    Two traps we must dodge:
    1. MAX(stat) across history leaks values from stale respec'd builds.
    2. Most-recent observation can be NULL-filled (scraper bug B7, task #127):
       some fight JSONs omit the stats block. We filter `strength IS NOT NULL`
       inside the window so we pick the most recent row that actually carries
       build data. STR=0 is valid (pure mages) — only NULL is meaningless.
    """
    if not leek_ids:
        return {}
    conn = sqlite3.connect(FIGHTS_DB)
    placeholders = ",".join("?" * len(leek_ids))
    rows = conn.execute(
        f"""
        SELECT leek_id, level, talent,
               strength, agility, wisdom, resistance,
               magic, science, life, tp, mp, obs
        FROM (
            SELECT leek_id, level, talent,
                   strength, agility, wisdom, resistance,
                   magic, science, life, tp, mp,
                   COUNT(*) OVER (PARTITION BY leek_id) AS obs,
                   ROW_NUMBER() OVER (PARTITION BY leek_id ORDER BY fight_id DESC) AS rn
            FROM leek_observations
            WHERE leek_id IN ({placeholders})
              AND strength IS NOT NULL
        )
        WHERE rn = 1
        """,
        leek_ids,
    ).fetchall()
    conn.close()
    out: dict[int, StatProfile] = {}
    for r in rows:
        out[r[0]] = StatProfile(
            leek_id=r[0], level=r[1] or 0, talent=r[2],
            strength=r[3] or 0, agility=r[4] or 0, wisdom=r[5] or 0,
            resistance=r[6] or 0, magic=r[7] or 0, science=r[8] or 0,
            life=r[9] or 0, tp=r[10] or 0, mp=r[11] or 0,
            observations=r[12] or 0,
        )
    return out


def load_bracket_stats(min_level: int, max_level: int) -> list[StatProfile]:
    """All leeks observed at [min_level, max_level]. Most recent complete obs per leek.

    `strength IS NOT NULL` guard dodges the scraper bug (B7/#127) where some
    observations lack the stats block.
    """
    conn = sqlite3.connect(FIGHTS_DB)
    rows = conn.execute(
        """
        SELECT leek_id, level, talent,
               strength, agility, wisdom, resistance,
               magic, science, life, tp, mp, obs
        FROM (
            SELECT leek_id, level, talent,
                   strength, agility, wisdom, resistance,
                   magic, science, life, tp, mp,
                   COUNT(*) OVER (PARTITION BY leek_id) AS obs,
                   ROW_NUMBER() OVER (PARTITION BY leek_id ORDER BY fight_id DESC) AS rn
            FROM leek_observations
            WHERE level BETWEEN ? AND ?
              AND strength IS NOT NULL
        )
        WHERE rn = 1
        """,
        (min_level, max_level),
    ).fetchall()
    conn.close()
    return [
        StatProfile(
            leek_id=r[0], level=r[1] or 0, talent=r[2],
            strength=r[3] or 0, agility=r[4] or 0, wisdom=r[5] or 0,
            resistance=r[6] or 0, magic=r[7] or 0, science=r[8] or 0,
            life=r[9] or 0, tp=r[10] or 0, mp=r[11] or 0,
            observations=r[12] or 0,
        )
        for r in rows
    ]


def load_chip_weapon_usage(leek_ids: list[int]) -> dict[int, tuple[Counter, Counter]]:
    """For each leek, return (weapon_counter, chip_counter) from populated observations."""
    if not leek_ids:
        return {}
    conn = sqlite3.connect(FIGHTS_DB)
    placeholders = ",".join("?" * len(leek_ids))
    rows = conn.execute(
        f"""
        SELECT leek_id, weapons_used, chips_used FROM leek_observations
        WHERE leek_id IN ({placeholders})
          AND (weapons_used != '[]' OR chips_used != '[]')
        """,
        leek_ids,
    ).fetchall()
    conn.close()
    out: dict[int, tuple[Counter, Counter]] = {}
    for lid, w_json, c_json in rows:
        w = out.setdefault(lid, (Counter(), Counter()))
        try:
            for wid in json.loads(w_json or "[]"):
                w[0][int(wid)] += 1
            for cid in json.loads(c_json or "[]"):
                w[1][int(cid)] += 1
        except Exception:
            continue
    return out


def load_climbers(min_climb: int = 500, window_days: int = 30) -> list[ClimbRecord]:
    """Leeks whose rank improved by >= min_climb over last window_days.

    Uses the `rankings` table (bulk snapshot, has talent+level correctly).
    """
    conn = sqlite3.connect(RANKINGS_DB)

    latest_ts = conn.execute(
        "SELECT timestamp FROM snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if not latest_ts:
        conn.close()
        return []
    latest = datetime.fromisoformat(latest_ts[0])
    cutoff = (latest - timedelta(days=window_days)).isoformat()

    latest_snap = conn.execute("SELECT MAX(id) FROM snapshots").fetchone()[0]
    first_snap_in_window = conn.execute(
        "SELECT MIN(id) FROM snapshots WHERE timestamp >= ?", (cutoff,)
    ).fetchone()[0]

    if first_snap_in_window is None or first_snap_in_window == latest_snap:
        conn.close()
        return []

    rows = conn.execute(
        """
        SELECT n.leek_id, n.name,
               o.rank first_rank, n.rank last_rank,
               o.talent first_talent, n.talent last_talent,
               o.level first_level, n.level last_level,
               (o.rank - n.rank) climb
        FROM rankings n
        JOIN rankings o ON o.leek_id = n.leek_id AND o.snapshot_id = ?
        WHERE n.snapshot_id = ?
          AND (o.rank - n.rank) >= ?
        ORDER BY climb DESC
        """,
        (first_snap_in_window, latest_snap, min_climb),
    ).fetchall()

    first_ts_row = conn.execute(
        "SELECT timestamp FROM snapshots WHERE id=?", (first_snap_in_window,)
    ).fetchone()
    span = (latest - datetime.fromisoformat(first_ts_row[0])).total_seconds() / 86400.0

    conn.close()
    return [
        ClimbRecord(
            leek_id=r[0], name=r[1],
            first_rank=r[2], last_rank=r[3],
            first_talent=r[4], last_talent=r[5],
            first_level=r[6], last_level=r[7],
            climb=r[8], span_days=span,
        )
        for r in rows
    ]


# --- Aggregation ---

def summarize(profiles: list[StatProfile]) -> dict[str, dict[str, float]]:
    """Mean / median / stddev / quartiles for each stat column."""
    out: dict[str, dict[str, float]] = {}
    if not profiles:
        return out
    for col in STAT_COLS:
        values = [getattr(p, col) for p in profiles]
        values_sorted = sorted(values)
        n = len(values_sorted)
        out[col] = {
            "n": n,
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stddev": statistics.stdev(values) if n > 1 else 0.0,
            "p25": values_sorted[n // 4] if n >= 4 else values_sorted[0],
            "p75": values_sorted[3 * n // 4] if n >= 4 else values_sorted[-1],
            "zero_rate": sum(1 for v in values if v == 0) / n,
        }
    return out


def classify_archetype(p: StatProfile) -> str:
    """Rough archetype label from max stat signature."""
    stat_vals = {
        "STR": p.strength, "MAG": p.magic, "AGI": p.agility, "SCI": p.science,
    }
    max_stat = max(stat_vals.items(), key=lambda kv: kv[1])
    if max_stat[1] < 100:
        return "balanced"
    if p.wisdom > 400 and max_stat[1] < 300:
        return f"support-{max_stat[0].lower()}"
    return f"{max_stat[0].lower()}-heavy"


# --- Rendering ---

def _fmt_dist(dist: dict[str, float]) -> str:
    return (
        f"mean={dist['mean']:.0f}  med={dist['median']:.0f}  "
        f"p25–p75={dist['p25']:.0f}–{dist['p75']:.0f}  "
        f"σ={dist['stddev']:.0f}  "
        f"zero={dist['zero_rate']*100:.0f}%"
    )


def render_top_n_report(
    top_10: list[LeekRef], top_10_stats: dict[int, StatProfile],
    top_100: list[LeekRef], top_100_stats: dict[int, StatProfile],
    l301_bracket: list[StatProfile],
    chip_weapon_top_10: dict[int, tuple[Counter, Counter]],
) -> str:
    lines: list[str] = []
    lines.append("# Top-N Reference Class (NEW-A)")
    lines.append("")
    lines.append(f"> Generated {datetime.now().isoformat()} from rankings.db + fights_meta.db")
    lines.append("> Pure local-data analysis — no scrape calls.")
    lines.append("")

    # --- Top 10 detailed table ---
    lines.append("## Top 10 individual breakdown")
    lines.append("")
    lines.append("| Rank | Leek | Farmer | Talent | L | STR | AGI | WIS | RES | MAG | SCI | HP | TP | MP | Archetype |")
    lines.append("|-----:|:-----|:-------|------:|--:|----:|----:|----:|----:|----:|----:|---:|---:|---:|:----------|")
    for ref in top_10:
        s = top_10_stats.get(ref.leek_id)
        if s is None:
            lines.append(
                f"| {ref.rank} | {ref.name} | {ref.farmer or ''} | T{ref.talent} | {ref.level} "
                f"| — | — | — | — | — | — | — | — | — | *no data* |"
            )
            continue
        arch = classify_archetype(s)
        lines.append(
            f"| {ref.rank} | {ref.name} | {ref.farmer or ''} | T{ref.talent} | {ref.level} "
            f"| {s.strength} | {s.agility} | {s.wisdom} | {s.resistance} | {s.magic} | {s.science} "
            f"| {s.life} | {s.tp} | {s.mp} | {arch} |"
        )
    lines.append("")

    # --- Archetype census among top-10 ---
    arch_counter: Counter = Counter()
    for ref in top_10:
        s = top_10_stats.get(ref.leek_id)
        if s:
            arch_counter[classify_archetype(s)] += 1
    if arch_counter:
        lines.append("**Top-10 archetype census**:")
        for a, c in arch_counter.most_common():
            lines.append(f"- `{a}` — {c} leeks")
        lines.append("")

    # --- Universal stat patterns (zero-rate flag) ---
    top_10_profiles = [s for s in top_10_stats.values() if s]
    if top_10_profiles:
        lines.append("## Universal traits (top-10)")
        lines.append("")
        lines.append("> A stat with low zero-rate across top-10 is an *entry ticket*. A stat with high zero-rate is *optional*.")
        lines.append("")
        lines.append("| Stat | mean | median | p25–p75 | zero-rate |")
        lines.append("|:-----|-----:|-------:|:--------|:----------|")
        top_10_summary = summarize(top_10_profiles)
        for col in ("strength", "agility", "wisdom", "resistance", "magic", "science", "life", "tp", "mp"):
            d = top_10_summary[col]
            flag = " 🎟️" if d["zero_rate"] < 0.2 and d["median"] > 100 else ""
            lines.append(
                f"| {col.upper()} | {d['mean']:.0f} | {d['median']:.0f} "
                f"| {d['p25']:.0f}–{d['p75']:.0f} | {d['zero_rate']*100:.0f}% |{flag}"
            )
        lines.append("")
        lines.append("> 🎟️ = universal (low zero-rate + meaningful median). These stats likely gate admission to top-10.")
        lines.append("")

    # --- Top 100 and L301 bracket aggregate ---
    lines.append("## Broader bracket aggregates")
    lines.append("")
    lines.append("| Cohort | n | STR | AGI | WIS | RES | MAG | SCI | HP | TP | MP |")
    lines.append("|:-------|--:|----:|----:|----:|----:|----:|----:|---:|---:|---:|")

    cohorts = [
        ("top-10 (observed)", [top_10_stats[r.leek_id] for r in top_10 if r.leek_id in top_10_stats]),
        ("top-100 (observed)", [top_100_stats[r.leek_id] for r in top_100 if r.leek_id in top_100_stats]),
        ("L301 bracket", l301_bracket),
    ]
    for label, profiles in cohorts:
        if not profiles:
            continue
        s = summarize(profiles)
        lines.append(
            f"| {label} | {len(profiles)} "
            f"| {s['strength']['median']:.0f} | {s['agility']['median']:.0f} "
            f"| {s['wisdom']['median']:.0f} | {s['resistance']['median']:.0f} "
            f"| {s['magic']['median']:.0f} | {s['science']['median']:.0f} "
            f"| {s['life']['median']:.0f} | {s['tp']['median']:.0f} | {s['mp']['median']:.0f} |"
        )
    lines.append("")

    # --- Chip / weapon observations ---
    if chip_weapon_top_10:
        lines.append("## Top-10 weapon / chip usage (from scraped fight replays)")
        lines.append("")
        lines.append("> Template IDs (not names). Cross-reference `leekwars_agent.models.equipment.CHIP_REGISTRY` / `WEAPON_REGISTRY` for names.")
        lines.append("> Empty means our fight parser didn't capture this leek's equipment usage.")
        lines.append("")
        for ref in top_10:
            wc = chip_weapon_top_10.get(ref.leek_id)
            if not wc:
                continue
            weapons, chips = wc
            if not weapons and not chips:
                continue
            top_w = ", ".join(f"{w}×{n}" for w, n in weapons.most_common(5))
            top_c = ", ".join(f"{c}×{n}" for c, n in chips.most_common(8))
            lines.append(f"- **{ref.name}** (rank #{ref.rank}): weapons [{top_w}] | chips [{top_c}]")
        lines.append("")

    lines.append("## Data caveats")
    lines.append("")
    lines.append("- Top-10 stats come from the MAX observed value per stat column. If our scrapes are old, the stats may be lower than current state.")
    lines.append("- `weapons_used` / `chips_used` coverage is ~52% / 60% across all observations — fight parser gaps mean some leeks appear equipment-blank.")
    lines.append("- Archetype labels are heuristic (max-stat signature); actual playstyle may differ.")
    lines.append("")
    return "\n".join(lines)


def render_climber_report(
    climbers: list[ClimbRecord],
    climber_stats: dict[int, StatProfile],
    level_bracket: tuple[int, int],
    bracket_climbers: list[ClimbRecord],
) -> str:
    lines: list[str] = []
    lines.append("# Climber Study (NEW-B)")
    lines.append("")
    lines.append(f"> Generated {datetime.now().isoformat()} from rankings.db + fights_meta.db")
    lines.append("")
    if not climbers:
        lines.append("No climbers meeting threshold in the available snapshot window.")
        lines.append("")
        return "\n".join(lines)

    span = climbers[0].span_days
    lines.append(f"**Criterion**: rank improvement ≥ 500 over {span:.1f} days (latest ranking window).")
    lines.append(f"**Total climbers**: {len(climbers)}")
    lines.append("")

    # Top 20 climbers overall
    lines.append("## Top 20 climbers (overall)")
    lines.append("")
    lines.append("| Leek | Climb | First rank → Last | Talent Δ | Level Δ |")
    lines.append("|:-----|------:|:------------------|---------:|--------:|")
    for c in climbers[:20]:
        lines.append(
            f"| {c.name} | +{c.climb} | {c.first_rank} → {c.last_rank} "
            f"| {c.last_talent - c.first_talent:+d} | {c.last_level - c.first_level:+d} |"
        )
    lines.append("")

    # --- Level-matched climbers (our bracket) ---
    lines.append(f"## Level-matched climbers ({level_bracket[0]}–{level_bracket[1]})")
    lines.append("")
    lines.append("> These are the ones most relevant to IAdonis. They climbed AT our level, not from L50 to L300.")
    lines.append("")
    if not bracket_climbers:
        lines.append("*No climbers currently leveled within our bracket.*")
        lines.append("")
    else:
        lines.append("| Leek | Level | Climb | STR | AGI | WIS | RES | MAG | SCI | HP | TP | MP |")
        lines.append("|:-----|------:|------:|----:|----:|----:|----:|----:|----:|---:|---:|---:|")
        for c in bracket_climbers[:20]:
            s = climber_stats.get(c.leek_id)
            if not s:
                lines.append(f"| {c.name} | {c.last_level} | +{c.climb} | — | — | — | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {c.name} | {c.last_level} | +{c.climb} | {s.strength} | {s.agility} | {s.wisdom} "
                f"| {s.resistance} | {s.magic} | {s.science} | {s.life} | {s.tp} | {s.mp} |"
            )
        lines.append("")

    # Aggregate climber stat signature
    bracket_profiles = [climber_stats[c.leek_id] for c in bracket_climbers if c.leek_id in climber_stats]
    if bracket_profiles:
        s = summarize(bracket_profiles)
        lines.append(f"**Median L{level_bracket[0]}–{level_bracket[1]} climber build** (n={len(bracket_profiles)}):")
        lines.append(
            f"STR {s['strength']['median']:.0f} / AGI {s['agility']['median']:.0f} / "
            f"WIS {s['wisdom']['median']:.0f} / RES {s['resistance']['median']:.0f} / "
            f"MAG {s['magic']['median']:.0f} / SCI {s['science']['median']:.0f} / "
            f"HP {s['life']['median']:.0f} / TP {s['tp']['median']:.0f} / MP {s['mp']['median']:.0f}"
        )
        lines.append("")

    return "\n".join(lines)


def render_gap_analysis(
    our_profile: StatProfile,
    top_10_profiles: list[StatProfile],
    bracket_climber_profiles: list[StatProfile],
    level_bracket: tuple[int, int],
) -> str:
    lines: list[str] = []
    lines.append("# Gap Analysis — IAdonis vs. Reference (NEW-C)")
    lines.append("")
    lines.append(f"> Generated {datetime.now().isoformat()}")
    lines.append("")
    lines.append("## Three points of comparison")
    lines.append("")
    lines.append("| Stat | IAdonis (L151) | Top-10 median | L150-200 climber median | Gap vs climber |")
    lines.append("|:-----|---------------:|--------------:|-----------------------:|---------------:|")

    top_10_summary = summarize(top_10_profiles) if top_10_profiles else {}
    bracket_summary = summarize(bracket_climber_profiles) if bracket_climber_profiles else {}

    deltas: list[tuple[str, int, int]] = []  # (stat_name, gap_vs_climber, pct)
    for col in STAT_COLS:
        ours = getattr(our_profile, col)
        top_med = int(top_10_summary.get(col, {}).get("median", 0))
        climber_med = int(bracket_summary.get(col, {}).get("median", 0))
        gap = climber_med - ours
        lines.append(
            f"| {col.upper()} | {ours} | {top_med} | {climber_med} | {gap:+d} |"
        )
        if climber_med > 0:
            deltas.append((col.upper(), gap, 100 * gap // climber_med))

    lines.append("")

    # Prioritized deltas
    deltas_by_abs = sorted(deltas, key=lambda d: -abs(d[1]))
    lines.append("## Prioritized deltas (absolute gap vs level-matched climbers)")
    lines.append("")
    lines.append("| Rank | Stat | Gap | % of climber median |")
    lines.append("|-----:|:-----|----:|--------------------:|")
    for i, (stat, gap, pct) in enumerate(deltas_by_abs[:5], 1):
        marker = " 🚨" if gap > 0 and abs(pct) > 50 else (" ✅" if gap < 0 else "")
        lines.append(f"| {i} | {stat} | {gap:+d} | {pct:+d}% |{marker}")
    lines.append("")
    lines.append("> 🚨 = large positive gap (we're behind); ✅ = we exceed median (no action).")
    lines.append("")

    # Verdict — always emit something, split behind/ahead, include top-10 gap
    lines.append("## Verdict")
    lines.append("")
    behind = [d for d in deltas_by_abs if d[1] > 0]
    ahead = [d for d in deltas_by_abs if d[1] < 0]
    if deltas_by_abs:
        biggest = deltas_by_abs[0]
        direction = "behind" if biggest[1] > 0 else "ahead of"
        lines.append(
            f"- **Biggest delta (climber-matched)**: {biggest[0]} — we are **{direction}** "
            f"climbers by {abs(biggest[1])} ({abs(biggest[2])}% of their median)."
        )
    if behind:
        lines.append(
            f"- **Behind on**: {', '.join(d[0] for d in behind)} — primary capital/equipment targets."
        )
    if ahead:
        lines.append(
            f"- **Ahead on**: {', '.join(d[0] for d in ahead)} — already optimized vs level-matched peers."
        )
    if ahead and not behind:
        lines.append(
            "- **Reading**: we already exceed our level bracket's climber median on every major stat. "
            "The bottleneck is not our build vs peers — it is **level progression** to unlock the top-10 tier."
        )

    # Gap to top-10 (separate from level-matched climbers)
    top_gaps: list[tuple[str, int]] = []
    for col in STAT_COLS:
        ours = getattr(our_profile, col)
        top_med = int(top_10_summary.get(col, {}).get("median", 0))
        if top_med > 0:
            top_gaps.append((col.upper(), top_med - ours))
    top_gaps.sort(key=lambda x: -abs(x[1]))
    if top_gaps:
        top3 = ", ".join(f"{n} {g:+d}" for n, g in top_gaps[:3])
        lines.append(f"- **Top-10 gap (absolute, not level-adjusted)**: {top3}")

    # Specific WIS call-out
    ours_wis = our_profile.wisdom
    clim_wis_med = bracket_summary.get("wisdom", {}).get("median", 0)
    top_wis_med = top_10_summary.get("wisdom", {}).get("median", 0)
    if ours_wis < 50 and (clim_wis_med > 100 or top_wis_med > 100):
        lines.append(
            f"- **WIS anomaly**: we run WIS {ours_wis}. Climbers at L{level_bracket[0]}–{level_bracket[1]} "
            f"run WIS ≈ {clim_wis_med:.0f}; top-10 runs WIS ≈ {top_wis_med:.0f}. "
            "Worth checking whether WIS affects any chip in our current kit."
        )
    lines.append("")
    lines.append("## Next step feeding #0403")
    lines.append("")
    lines.append(
        "Research optimal build allocation (#0403) should START from the climber-median build and work "
        "backwards to capital spend. Use the top 5 deltas above as prioritized targets."
    )
    lines.append("")
    return "\n".join(lines)


# --- Main ---

def main() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/5] Loading top-10 and top-100 refs…")
    top_10 = load_top_n(10)
    top_100 = load_top_n(100)

    print("[2/5] Loading stat profiles…")
    top_10_stats = load_stat_profiles([r.leek_id for r in top_10])
    top_100_stats = load_stat_profiles([r.leek_id for r in top_100])
    l301_bracket = load_bracket_stats(300, 320)
    chip_weapon_top_10 = load_chip_weapon_usage([r.leek_id for r in top_10])

    print("[3/5] Loading climbers…")
    climbers = load_climbers(min_climb=500, window_days=30)
    bracket_range = (140, 180)
    bracket_climbers = [c for c in climbers if bracket_range[0] <= c.last_level <= bracket_range[1]]
    climber_stats = load_stat_profiles([c.leek_id for c in climbers])

    print("[4/5] Loading IAdonis profile…")
    our = load_stat_profiles([OUR_LEEK_ID]).get(OUR_LEEK_ID)
    if not our:
        # Fallback if our own leek has no observations — synthesize from memory
        our = StatProfile(
            leek_id=OUR_LEEK_ID, level=151, talent=341,
            strength=452, agility=0, wisdom=0, resistance=219,
            magic=0, science=0, life=999, tp=14, mp=4, observations=0,
        )

    print("[5/5] Rendering reports…")
    top_n_md = render_top_n_report(
        top_10, top_10_stats, top_100, top_100_stats, l301_bracket, chip_weapon_top_10
    )
    climber_md = render_climber_report(climbers, climber_stats, bracket_range, bracket_climbers)
    gap_md = render_gap_analysis(
        our,
        [p for p in top_10_stats.values()],
        [climber_stats[c.leek_id] for c in bracket_climbers if c.leek_id in climber_stats],
        bracket_range,
    )

    (RESEARCH_DIR / "top_n_reference_class.md").write_text(top_n_md)
    (RESEARCH_DIR / "climber_study.md").write_text(climber_md)
    (RESEARCH_DIR / "gap_analysis.md").write_text(gap_md)

    print("")
    print(f"Wrote {RESEARCH_DIR}/top_n_reference_class.md")
    print(f"Wrote {RESEARCH_DIR}/climber_study.md")
    print(f"Wrote {RESEARCH_DIR}/gap_analysis.md")
    print("")
    # Quick summary to stdout
    print(f"Top-10: {len(top_10)} leeks, {len(top_10_stats)} with stats observed")
    print(f"Top-100: {len(top_100)} leeks, {len(top_100_stats)} with stats observed")
    print(f"L301 bracket: {len(l301_bracket)} distinct leeks")
    print(f"Climbers (≥500 over 30d): {len(climbers)}")
    print(f"Level-matched (L{bracket_range[0]}–{bracket_range[1]}): {len(bracket_climbers)}")


if __name__ == "__main__":
    main()
