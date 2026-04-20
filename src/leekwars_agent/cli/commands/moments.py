"""Decisive-moment detector CLI (#0311)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import click

from ..output import console, output_json
from ... import decisive_moments as dm


@click.group("moments")
def moments_cli() -> None:
    """Detect and query decisive moments in fight replays.

    Commands:
      scan    — run detectors over fights and persist annotations
      list    — show stored moments for a fight
      report  — distribution of moment types across the corpus
    """


@moments_cli.command("scan")
@click.option("--fights-db", type=click.Path(), default="data/fights_meta.db")
@click.option("--context", type=int, default=2,
              help="Fight context to scan (default: 2=matchmaking)")
@click.option("--limit", type=int, default=None,
              help="Limit to N most-recent fights (default: all)")
@click.pass_context
def scan(ctx: click.Context, fights_db: str, context: int, limit: int | None) -> None:
    """Scan fights, detect moments, and persist annotations."""
    summary = dm.scan_and_save(db=Path(fights_db), context=context, limit=limit)
    if ctx.obj.get("json"):
        output_json(summary)
        return
    console.print(f"[bold]Decisive-moment scan[/bold]")
    console.print(f"  Fights scanned: {summary['fights_scanned']}")
    console.print(f"  Fights with moments: {summary['fights_with_moments']}")
    console.print(f"  Moments saved: {summary['moments_saved']}")
    for k, v in summary.items():
        if k.startswith("type_"):
            console.print(f"    {k[5:]}: {v}")


@moments_cli.command("list")
@click.argument("fight_id", type=int)
@click.option("--fights-db", type=click.Path(), default="data/fights_meta.db")
@click.pass_context
def list_cmd(ctx: click.Context, fight_id: int, fights_db: str) -> None:
    """List stored moments for one fight."""
    conn = sqlite3.connect(fights_db)
    try:
        rows = conn.execute(
            "SELECT turn, moment_type, actor, victim, details "
            "FROM decisive_moments WHERE fight_id=? ORDER BY turn",
            (fight_id,),
        ).fetchall()
    finally:
        conn.close()

    if ctx.obj.get("json"):
        output_json([
            {"turn": t, "type": mt, "actor": a, "victim": v,
             "details": json.loads(d) if d else {}}
            for t, mt, a, v, d in rows
        ])
        return

    console.print(f"[bold]Moments for fight {fight_id}[/bold] (n={len(rows)})")
    for turn, mt, actor, victim, details in rows:
        d = json.loads(details) if details else {}
        console.print(f"  t{turn}: {mt} actor={actor} victim={victim} {d}")


@moments_cli.command("report")
@click.option("--fights-db", type=click.Path(), default="data/fights_meta.db")
@click.pass_context
def report(ctx: click.Context, fights_db: str) -> None:
    """Distribution of moment types + per-turn histogram."""
    conn = sqlite3.connect(fights_db)
    try:
        # Ensure the table exists before querying
        dm.ensure_schema(Path(fights_db))
        counts = dict(conn.execute(
            "SELECT moment_type, COUNT(*) FROM decisive_moments GROUP BY moment_type"
        ).fetchall())
        turn_hist = conn.execute(
            "SELECT turn, COUNT(*) FROM decisive_moments "
            "WHERE moment_type='hp_crossover' GROUP BY turn ORDER BY turn"
        ).fetchall()
        n_fights = conn.execute(
            "SELECT COUNT(DISTINCT fight_id) FROM decisive_moments"
        ).fetchone()[0]
    finally:
        conn.close()

    if ctx.obj.get("json"):
        output_json({
            "fights_with_moments": n_fights,
            "counts": counts,
            "hp_crossover_turn_histogram": {t: c for t, c in turn_hist},
        })
        return

    console.print("[bold]Decisive-moments report[/bold]")
    console.print(f"  Fights with moments: {n_fights}")
    for mt, c in sorted(counts.items()):
        console.print(f"  {mt}: {c}")
    if turn_hist:
        console.print("\n  hp_crossover by turn:")
        for turn, c in turn_hist[:20]:
            console.print(f"    t{turn:>2}: {'█' * min(c, 40)} ({c})")
