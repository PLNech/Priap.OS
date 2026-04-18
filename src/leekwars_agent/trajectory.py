"""Talent / level trajectory model.

Reads `data/rankings.db` (our leek's talent+level+rank time series) and
`data/fights_meta.db` (fight-level WR baseline). Projects when we reach
top-N ranks at current velocity, and how WR changes that projection.

The projection is deliberately naive (linear extrapolation) — its purpose
is to convert gut-feel "are we climbing?" into a defensible number.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Iterable

OUR_LEEK_ID = 131321  # IAdonis — primary competitive leek

# Ranks we care about projecting
DEFAULT_TARGET_RANKS = (10, 100, 1000)

# Windows (days) over which to fit velocity
DEFAULT_WINDOWS_DAYS = (7, 30, 90)


# --- Data classes ---

@dataclass
class Snapshot:
    timestamp: datetime
    talent: int
    level: int
    rank: int


@dataclass
class Velocity:
    window_days: int
    n_points: int
    talent_per_day: float
    level_per_day: float
    rank_per_day: float       # negative = improving (lower rank is better)


@dataclass
class Threshold:
    rank: int
    talent: int
    level: int


@dataclass
class WRScenario:
    wr_pct: float
    talent_per_day_est: float
    days_to_top_1000: float | None
    days_to_top_10: float | None


@dataclass
class TrajectoryReport:
    as_of: datetime
    current: Snapshot
    fight_count: int
    fight_wins: int
    wr_pct: float
    velocities: list[Velocity]
    thresholds: list[Threshold]
    projections: dict[int, dict[str, float | None]]  # rank -> {talent_days, level_days}
    wr_scenarios: list[WRScenario]
    data_quality: dict[str, str] = field(default_factory=dict)


# --- Loaders ---

def load_snapshots(
    rankings_db: Path | str,
    leek_id: int = OUR_LEEK_ID,
) -> list[Snapshot]:
    """Load all ranking snapshots for a leek, oldest first.

    Prefers the `rankings` table (populated from bulk snapshot) because
    `leek_ranks.talent/level` was buggy pre-2026-04-18.
    """
    conn = sqlite3.connect(rankings_db)
    rows = conn.execute(
        """
        SELECT s.timestamp, r.talent, r.level, r.rank
        FROM rankings r
        JOIN snapshots s ON s.id = r.snapshot_id
        WHERE r.leek_id = ?
        ORDER BY s.timestamp ASC
        """,
        (leek_id,),
    ).fetchall()
    conn.close()
    out: list[Snapshot] = []
    for ts, talent, level, rank in rows:
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue
        out.append(Snapshot(timestamp=dt, talent=talent, level=level, rank=rank))
    return out


def load_thresholds(
    rankings_db: Path | str,
    target_ranks: Iterable[int] = DEFAULT_TARGET_RANKS,
) -> list[Threshold]:
    """For the latest snapshot, return the (talent, level) at each target rank."""
    conn = sqlite3.connect(rankings_db)
    latest = conn.execute("SELECT MAX(id) FROM snapshots").fetchone()[0]
    out: list[Threshold] = []
    for rank in target_ranks:
        row = conn.execute(
            "SELECT talent, level FROM rankings WHERE snapshot_id=? AND rank=?",
            (latest, rank),
        ).fetchone()
        if row:
            out.append(Threshold(rank=rank, talent=row[0], level=row[1]))
    conn.close()
    return out


def load_wr(
    fights_db: Path | str,
    leek_id: int = OUR_LEEK_ID,
    context: int | None = 2,  # matchmaking only; None = all contexts
) -> tuple[int, int]:
    """Return (fights, wins) from leek_observations.

    Matchmaking context (2) is the only one that affects talent.
    """
    conn = sqlite3.connect(fights_db)
    if context is None:
        row = conn.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN won=1 THEN 1 ELSE 0 END)
            FROM leek_observations WHERE leek_id=?
            """,
            (leek_id,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT COUNT(*), SUM(CASE WHEN lo.won=1 THEN 1 ELSE 0 END)
            FROM leek_observations lo
            JOIN fights f ON f.fight_id = lo.fight_id
            WHERE lo.leek_id=? AND f.context=?
            """,
            (leek_id, context),
        ).fetchone()
    conn.close()
    fights = row[0] or 0
    wins = row[1] or 0
    return fights, wins


def load_latest_fight_date(
    fights_db: Path | str,
    leek_id: int = OUR_LEEK_ID,
) -> datetime | None:
    """Most recent fight we have for this leek. Exposes data staleness."""
    conn = sqlite3.connect(fights_db)
    row = conn.execute(
        """
        SELECT MAX(f.fight_date) FROM leek_observations lo
        JOIN fights f ON f.fight_id = lo.fight_id WHERE lo.leek_id=?
        """,
        (leek_id,),
    ).fetchone()
    conn.close()
    if row and row[0]:
        return datetime.fromtimestamp(row[0])
    return None


# --- Math ---

def linear_slope(xs: list[float], ys: list[float]) -> float:
    """Ordinary-least-squares slope (dy/dx). 0 if undetermined."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return num / den


def compute_velocity(
    snapshots: list[Snapshot],
    window_days: int,
    as_of: datetime,
) -> Velocity:
    """Fit a linear slope to the last `window_days` of data."""
    cutoff = as_of - timedelta(days=window_days)
    window = [s for s in snapshots if s.timestamp >= cutoff]
    if len(window) < 2:
        return Velocity(window_days=window_days, n_points=len(window),
                        talent_per_day=0.0, level_per_day=0.0, rank_per_day=0.0)
    t0 = window[0].timestamp
    xs = [(s.timestamp - t0).total_seconds() / 86400.0 for s in window]
    return Velocity(
        window_days=window_days,
        n_points=len(window),
        talent_per_day=linear_slope(xs, [s.talent for s in window]),
        level_per_day=linear_slope(xs, [s.level for s in window]),
        rank_per_day=linear_slope(xs, [float(s.rank) for s in window]),
    )


def project_days(current: float, target: float, velocity: float) -> float | None:
    """Days to reach `target` from `current` at constant `velocity`.

    Returns None if velocity is zero or moving away from target.
    """
    gap = target - current
    if velocity == 0:
        return None
    days = gap / velocity
    return days if days >= 0 else None


def estimate_wr_to_talent_velocity(
    wr_pct: float,
    fights_per_day: float,
    avg_talent_gain_per_win: float = 6.0,
    avg_talent_loss_per_loss: float = 6.0,
) -> float:
    """Rough estimator — talent delta per day as a function of WR.

    LeekWars talent follows an Elo-like update. Exact formula is opaque,
    but a simple symmetric model (±k per result, k~6) is good enough to
    illustrate *relative* sensitivity — the message is directional.
    """
    wr = wr_pct / 100.0
    per_fight = wr * avg_talent_gain_per_win - (1 - wr) * avg_talent_loss_per_loss
    return per_fight * fights_per_day


# --- Orchestration ---

def build_report(
    rankings_db: Path | str = "data/rankings.db",
    fights_db: Path | str = "data/fights_meta.db",
    leek_id: int = OUR_LEEK_ID,
    target_ranks: Iterable[int] = DEFAULT_TARGET_RANKS,
    windows_days: Iterable[int] = DEFAULT_WINDOWS_DAYS,
    wr_scenario_pcts: Iterable[float] = (48.0, 50.0, 52.0, 55.0, 60.0),
    fights_per_day_assumed: float = 50.0,
) -> TrajectoryReport:
    snapshots = load_snapshots(rankings_db, leek_id)
    if not snapshots:
        raise ValueError(f"No ranking snapshots for leek {leek_id}")

    as_of = snapshots[-1].timestamp
    current = snapshots[-1]
    fights, wins = load_wr(fights_db, leek_id, context=2)
    wr_pct = 100.0 * wins / fights if fights else 0.0
    latest_fight = load_latest_fight_date(fights_db, leek_id)

    velocities = [compute_velocity(snapshots, w, as_of) for w in windows_days]
    thresholds = load_thresholds(rankings_db, target_ranks)

    # Use the 30-day window as the "primary" velocity for projections.
    # Too-short window: noisy. Too-long: washes out recent trend.
    primary = next((v for v in velocities if v.window_days == 30), velocities[0])

    projections: dict[int, dict[str, float | None]] = {}
    for th in thresholds:
        projections[th.rank] = {
            "talent_days": project_days(current.talent, th.talent, primary.talent_per_day),
            "level_days": project_days(current.level, th.level, primary.level_per_day),
        }

    # WR sensitivity: holds level velocity constant, scales talent velocity.
    top_1000 = next((t for t in thresholds if t.rank == 1000), None)
    top_10 = next((t for t in thresholds if t.rank == 10), None)
    scenarios: list[WRScenario] = []
    for pct in wr_scenario_pcts:
        est_vel = estimate_wr_to_talent_velocity(pct, fights_per_day_assumed)
        scenarios.append(WRScenario(
            wr_pct=pct,
            talent_per_day_est=est_vel,
            days_to_top_1000=project_days(current.talent, top_1000.talent, est_vel) if top_1000 else None,
            days_to_top_10=project_days(current.talent, top_10.talent, est_vel) if top_10 else None,
        ))

    data_quality = {}
    if latest_fight:
        stale_days = (as_of - latest_fight).days
        data_quality["fights_latest"] = latest_fight.isoformat()
        data_quality["fights_stale_days"] = str(stale_days)
        if stale_days > 7:
            data_quality["fights_staleness_warning"] = (
                f"Fight DB is {stale_days} days stale — WR baseline is historical, not recent."
            )
    data_quality["rankings_points"] = str(len(snapshots))
    data_quality["rankings_span_days"] = str((snapshots[-1].timestamp - snapshots[0].timestamp).days)

    return TrajectoryReport(
        as_of=as_of,
        current=current,
        fight_count=fights,
        fight_wins=wins,
        wr_pct=wr_pct,
        velocities=velocities,
        thresholds=thresholds,
        projections=projections,
        wr_scenarios=scenarios,
        data_quality=data_quality,
    )


# --- Rendering ---

def _fmt_days(days: float | None) -> str:
    if days is None:
        return "unreachable at current pace"
    if days > 9999:
        return "∞"
    if days > 365:
        return f"{days/365:.1f} years ({days:.0f} days)"
    if days > 30:
        return f"{days/30:.1f} months ({days:.0f} days)"
    return f"{days:.1f} days"


def render_markdown(report: TrajectoryReport) -> str:
    lines: list[str] = []
    lines.append("# IAdonis Trajectory Model")
    lines.append("")
    lines.append(f"> Generated {report.as_of.isoformat()} from `rankings.db` + `fights_meta.db`")
    lines.append("")

    lines.append("## Current state")
    lines.append("")
    lines.append(f"- **Rank**: #{report.current.rank}")
    lines.append(f"- **Talent**: T{report.current.talent}")
    lines.append(f"- **Level**: L{report.current.level}")
    lines.append(f"- **WR** (matchmaking, all-time): {report.wr_pct:.1f}% ({report.fight_wins}/{report.fight_count})")
    lines.append("")

    lines.append("## Velocities")
    lines.append("")
    lines.append("| Window | Points | Talent/day | Level/day | Rank/day (− = improving) |")
    lines.append("|--------|--------|-----------:|----------:|-------------------------:|")
    for v in report.velocities:
        lines.append(
            f"| {v.window_days}d | {v.n_points} "
            f"| {v.talent_per_day:+.2f} | {v.level_per_day:+.2f} | {v.rank_per_day:+.1f} |"
        )
    lines.append("")

    lines.append("## Targets (latest snapshot)")
    lines.append("")
    lines.append("| Rank | Talent needed | Level needed | Talent gap | Level gap |")
    lines.append("|-----:|--------------:|-------------:|-----------:|----------:|")
    for th in report.thresholds:
        lines.append(
            f"| #{th.rank} | T{th.talent} | L{th.level} "
            f"| {th.talent - report.current.talent:+d} | {th.level - report.current.level:+d} |"
        )
    lines.append("")

    lines.append("## Projection at current (30d) velocity")
    lines.append("")
    lines.append("| Rank | Days to reach talent | Days to reach level |")
    lines.append("|-----:|:---------------------|:--------------------|")
    for th in report.thresholds:
        p = report.projections.get(th.rank, {})
        lines.append(
            f"| #{th.rank} | {_fmt_days(p.get('talent_days'))} | {_fmt_days(p.get('level_days'))} |"
        )
    lines.append("")
    lines.append("> Projections are naive linear extrapolation. Thresholds are *static* snapshots; ")
    lines.append("> they will move as other leeks level up. Treat as a lower bound on required pace, not a schedule.")
    lines.append("")

    lines.append("## WR sensitivity")
    lines.append("")
    lines.append("> Assumes 50 fights/day, symmetric ±6 talent per result (approximate Elo).")
    lines.append("")
    lines.append("| WR | Talent/day (est) | Days to top-1000 | Days to top-10 |")
    lines.append("|---:|-----------------:|:-----------------|:---------------|")
    for sc in report.wr_scenarios:
        lines.append(
            f"| {sc.wr_pct:.0f}% | {sc.talent_per_day_est:+.1f} "
            f"| {_fmt_days(sc.days_to_top_1000)} | {_fmt_days(sc.days_to_top_10)} |"
        )
    lines.append("")

    lines.append("## Data quality")
    lines.append("")
    for k, v in report.data_quality.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")

    lines.append("## Verdict")
    lines.append("")
    lines.extend(_render_verdict(report))
    lines.append("")
    return "\n".join(lines)


def _render_verdict(report: TrajectoryReport) -> list[str]:
    """Short, blunt interpretation of the numbers."""
    out: list[str] = []
    primary = next((v for v in report.velocities if v.window_days == 30), report.velocities[0])
    top_1000 = next((t for t in report.thresholds if t.rank == 1000), None)
    top_10 = next((t for t in report.thresholds if t.rank == 10), None)

    # Level vs talent — which pillar is moving?
    if primary.level_per_day > 0.5 and abs(primary.talent_per_day) < 3:
        out.append(
            "- **Level is climbing, talent is flat.** We are grinding XP but staying "
            "bracket-average (~48% WR). Leveling alone does not move rank — we get matched "
            "against higher-talent opponents as we level up."
        )
    elif primary.talent_per_day > 5:
        out.append("- **Talent is climbing.** Current strategy is working — stay the course.")
    elif primary.talent_per_day < -5:
        out.append("- **Talent is falling.** Something recently regressed — investigate last deploy or opponent meta shift.")
    else:
        out.append("- **Neither talent nor level is moving materially.** Flywheel stalled.")

    # Level gap to top-1000
    if top_1000 and top_1000.level > report.current.level:
        gap_levels = top_1000.level - report.current.level
        days_if_pace_holds = (
            gap_levels / primary.level_per_day if primary.level_per_day > 0 else None
        )
        if days_if_pace_holds:
            out.append(
                f"- **Level ceiling**: top-1000 is L{top_1000.level}; we are L{report.current.level} "
                f"(gap {gap_levels}). At {primary.level_per_day:.1f} levels/day, "
                f"that is ~{days_if_pace_holds:.0f} days ({days_if_pace_holds/30:.1f} months)."
            )
    # WR leverage
    base = next((s for s in report.wr_scenarios if abs(s.wr_pct - report.wr_pct) < 3), None)
    high = next((s for s in report.wr_scenarios if s.wr_pct >= 55.0), None)
    if base and high and base.days_to_top_1000 and high.days_to_top_1000:
        out.append(
            f"- **WR leverage**: at {base.wr_pct:.0f}% WR, top-1000 talent takes "
            f"{_fmt_days(base.days_to_top_1000)}; at 55% it takes {_fmt_days(high.days_to_top_1000)}. "
            "Every % WR point compresses the timeline materially."
        )
    # Top-10 honesty
    if top_10:
        out.append(
            f"- **Top-10 reality**: needs T{top_10.talent} and L{top_10.level}. "
            f"Even at 60% WR, this is measured in *years* without a level breakthrough."
        )
    out.append(
        "- **Implication**: P1 (level + equipment) is the binding pillar. P2 (AI iteration) "
        "contributes only via its effect on WR — which P0 must validate before we trust it."
    )
    return out
