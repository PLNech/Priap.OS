"""Trajectory CLI — project when we reach top-N ranks at current pace."""

from pathlib import Path

import click

from ..output import console, output_json
from ... import trajectory as traj


@click.command("trajectory")
@click.option("--rankings-db", default="data/rankings.db", help="Rankings SQLite DB path")
@click.option("--fights-db", default="data/fights_meta.db", help="Fights SQLite DB path")
@click.option("--leek-id", type=int, default=traj.OUR_LEEK_ID, help="Leek ID to project")
@click.option("--write", "out_path", type=click.Path(), default=None,
              help="Write markdown report to this path (e.g. docs/research/trajectory_s52.md)")
@click.pass_context
def trajectory(ctx: click.Context, rankings_db: str, fights_db: str,
               leek_id: int, out_path: str | None) -> None:
    """Project talent/level trajectory toward top-10 / top-100 / top-1000.

    Reads local SQLite databases — no API call required. Projection is a
    linear extrapolation from the last 30 days of ranking snapshots. Also
    shows WR sensitivity so you can see what each % of WR is worth in days.
    """
    report = traj.build_report(
        rankings_db=rankings_db,
        fights_db=fights_db,
        leek_id=leek_id,
    )

    if ctx.obj.get("json"):
        output_json({
            "as_of": report.as_of.isoformat(),
            "current": {
                "rank": report.current.rank,
                "talent": report.current.talent,
                "level": report.current.level,
            },
            "wr_pct": report.wr_pct,
            "fights": report.fight_count,
            "wins": report.fight_wins,
            "velocities": [
                {"window_days": v.window_days, "n": v.n_points,
                 "talent_per_day": v.talent_per_day,
                 "level_per_day": v.level_per_day,
                 "rank_per_day": v.rank_per_day}
                for v in report.velocities
            ],
            "thresholds": [
                {"rank": t.rank, "talent": t.talent, "level": t.level}
                for t in report.thresholds
            ],
            "projections": report.projections,
            "wr_scenarios": [
                {"wr_pct": s.wr_pct, "talent_per_day": s.talent_per_day_est,
                 "days_to_top_1000": s.days_to_top_1000,
                 "days_to_top_10": s.days_to_top_10}
                for s in report.wr_scenarios
            ],
            "data_quality": report.data_quality,
        })
        return

    md = traj.render_markdown(report)
    console.print(md)

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(md)
        console.print(f"\n[green]Wrote[/green] {out_path}")
