"""Analysis commands - mine insights from scraped fight data."""

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import click
from ..output import output_json, console


@click.group()
def analyze():
    """Analyze scraped fight data for meta insights.

    Run `leek scrape run` first to build the database.
    """
    pass


@analyze.command("meta")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--min-level", type=int, default=25, help="Minimum level")
@click.option("--max-level", type=int, default=100, help="Maximum level")
@click.option("--output", "-o", type=str, help="Save analysis to markdown file")
@click.pass_context
def meta_analysis(ctx: click.Context, db: str, min_level: int, max_level: int, output: str) -> None:
    """Run full meta analysis on scraped fights.

    Examples:
        leek analyze meta                     # Full L25-100 analysis
        leek analyze meta --min-level 30 --max-level 50
        leek analyze meta -o docs/research/meta.md
    """
    if not Path(db).exists():
        console.print(f"[red]Database not found: {db}[/red]")
        console.print("Run `leek scrape run` first to collect fight data.")
        raise SystemExit(1)

    conn = sqlite3.connect(db)
    results = _run_meta_analysis(conn, min_level, max_level)
    conn.close()

    if ctx.obj.get("json"):
        output_json(results)
        return

    # Pretty print
    _print_meta_analysis(results)

    # Save to file if requested
    if output:
        _save_meta_analysis(results, output)
        console.print(f"\n[green]✓ Saved to {output}[/green]")


@analyze.command("level")
@click.argument("level", type=int)
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--range", "level_range", type=int, default=5, help="Level range (+/-)")
@click.pass_context
def level_analysis(ctx: click.Context, level: int, db: str, level_range: int) -> None:
    """Detailed analysis for a specific level range.

    Examples:
        leek analyze level 34           # Analyze L29-39
        leek analyze level 50 --range 10  # Analyze L40-60
    """
    if not Path(db).exists():
        console.print(f"[red]Database not found: {db}[/red]")
        raise SystemExit(1)

    conn = sqlite3.connect(db)
    results = _run_level_analysis(conn, level, level_range)
    conn.close()

    if ctx.obj.get("json"):
        output_json(results)
        return

    _print_level_analysis(results, level, level_range)


@analyze.command("stats")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def db_stats(ctx: click.Context, db: str) -> None:
    """Show database statistics."""
    if not Path(db).exists():
        console.print(f"[red]Database not found: {db}[/red]")
        raise SystemExit(1)

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row

    stats = {
        "fights": conn.execute("SELECT COUNT(*) FROM fights").fetchone()[0],
        "queue": conn.execute("SELECT COUNT(*) FROM scrape_queue").fetchone()[0],
        "observations": conn.execute("SELECT COUNT(*) FROM leek_observations").fetchone()[0],
        "unique_leeks": conn.execute("SELECT COUNT(DISTINCT leek_id) FROM leek_observations").fetchone()[0],
        "scraped_leeks": conn.execute("SELECT COUNT(*) FROM scraped_players WHERE player_type='leek'").fetchone()[0],
    }

    # Size on disk
    stats["size_mb"] = round(Path(db).stat().st_size / 1024 / 1024, 1)

    conn.close()

    if ctx.obj.get("json"):
        output_json(stats)
        return

    console.print("[bold]Scraper Database Stats[/bold]")
    console.print(f"  Fights: [cyan]{stats['fights']:,}[/cyan]")
    console.print(f"  Observations: [cyan]{stats['observations']:,}[/cyan]")
    console.print(f"  Unique leeks: [cyan]{stats['unique_leeks']:,}[/cyan]")
    console.print(f"  Scraped leeks: [cyan]{stats['scraped_leeks']:,}[/cyan]")
    console.print(f"  Queue: [yellow]{stats['queue']:,}[/yellow]")
    console.print(f"  Size: {stats['size_mb']} MB")


# =============================================================================
# Analysis Functions
# =============================================================================

def _run_meta_analysis(conn: sqlite3.Connection, min_level: int, max_level: int) -> dict:
    """Run full meta analysis and return structured results."""
    leek_stats = []
    fight_data = {"team1_wins": 0, "team2_wins": 0, "draws": 0}

    rows = conn.execute("SELECT json_data, winner FROM fights").fetchall()
    for row in rows:
        data = json.loads(row[0])
        fight = data.get("fight", data)
        winner = row[1]

        if winner == 1:
            fight_data["team1_wins"] += 1
        elif winner == 2:
            fight_data["team2_wins"] += 1
        else:
            fight_data["draws"] += 1

        for leek in fight.get("data", {}).get("leeks", []):
            level = leek.get("level", 0)
            if min_level <= level <= max_level:
                leek_stats.append({
                    "level": level,
                    "str": leek.get("strength", 0),
                    "agi": leek.get("agility", 0),
                    "mag": leek.get("magic", 0),
                    "won": leek.get("team") == winner,
                })

    total_fights = len(rows)

    # First-mover advantage
    first_mover = {
        "attacker_wins": fight_data["team1_wins"],
        "defender_wins": fight_data["team2_wins"],
        "draws": fight_data["draws"],
        "attacker_rate": round(100 * fight_data["team1_wins"] / total_fights, 1) if total_fights else 0,
        "defender_rate": round(100 * fight_data["team2_wins"] / total_fights, 1) if total_fights else 0,
        "draw_rate": round(100 * fight_data["draws"] / total_fights, 1) if total_fights else 0,
    }

    # By level bucket
    by_level = defaultdict(list)
    for s in leek_stats:
        bucket = f"{(s['level'] // 10) * 10}-{(s['level'] // 10) * 10 + 9}"
        by_level[bucket].append(s)

    level_stats = {}
    for bucket, stats in sorted(by_level.items()):
        if len(stats) < 10:
            continue
        n = len(stats)
        level_stats[bucket] = {
            "count": n,
            "avg_str": round(sum(s["str"] for s in stats) / n),
            "avg_agi": round(sum(s["agi"] for s in stats) / n),
            "avg_mag": round(sum(s["mag"] for s in stats) / n),
            "win_rate": round(100 * sum(1 for s in stats if s["won"]) / n, 1),
        }

    # Archetype analysis
    archetypes = defaultdict(lambda: {"wins": 0, "total": 0})
    for s in leek_stats:
        if s["str"] > s["agi"] and s["str"] > s["mag"]:
            arch = "STR"
        elif s["agi"] > s["str"] and s["agi"] > s["mag"]:
            arch = "AGI"
        elif s["mag"] > s["str"] and s["mag"] > s["agi"]:
            arch = "MAG"
        else:
            arch = "Hybrid"
        archetypes[arch]["total"] += 1
        if s["won"]:
            archetypes[arch]["wins"] += 1

    archetype_stats = {}
    for arch, data in archetypes.items():
        archetype_stats[arch] = {
            "count": data["total"],
            "wins": data["wins"],
            "win_rate": round(100 * data["wins"] / data["total"], 1) if data["total"] else 0,
        }

    return {
        "total_fights": total_fights,
        "total_leeks": len(leek_stats),
        "level_range": f"L{min_level}-{max_level}",
        "first_mover": first_mover,
        "by_level": level_stats,
        "archetypes": archetype_stats,
    }


def _run_level_analysis(conn: sqlite3.Connection, level: int, level_range: int) -> dict:
    """Run detailed analysis for specific level range."""
    min_lvl = level - level_range
    max_lvl = level + level_range

    leek_stats = []
    rows = conn.execute("SELECT json_data, winner FROM fights").fetchall()

    for row in rows:
        data = json.loads(row[0])
        fight = data.get("fight", data)
        winner = row[1]

        for leek in fight.get("data", {}).get("leeks", []):
            lvl = leek.get("level", 0)
            if min_lvl <= lvl <= max_lvl:
                leek_stats.append({
                    "level": lvl,
                    "str": leek.get("strength", 0),
                    "agi": leek.get("agility", 0),
                    "mag": leek.get("mag", 0),
                    "res": leek.get("resistance", 0),
                    "life": leek.get("life", 0),
                    "tp": leek.get("tp", 0),
                    "mp": leek.get("mp", 0),
                    "won": leek.get("team") == winner,
                })

    if not leek_stats:
        return {"error": f"No data for L{min_lvl}-{max_lvl}"}

    n = len(leek_stats)
    wins = sum(1 for s in leek_stats if s["won"])

    # STR distribution
    str_values = [s["str"] for s in leek_stats if s["str"] > 0]
    str_buckets = defaultdict(lambda: {"total": 0, "wins": 0})
    for s in leek_stats:
        bucket = (s["str"] // 50) * 50
        str_buckets[bucket]["total"] += 1
        if s["won"]:
            str_buckets[bucket]["wins"] += 1

    return {
        "level_range": f"L{min_lvl}-{max_lvl}",
        "count": n,
        "win_rate": round(100 * wins / n, 1),
        "avg_stats": {
            "str": round(sum(s["str"] for s in leek_stats) / n),
            "agi": round(sum(s["agi"] for s in leek_stats) / n),
            "mag": round(sum(s["mag"] for s in leek_stats) / n),
            "res": round(sum(s["res"] for s in leek_stats) / n),
            "life": round(sum(s["life"] for s in leek_stats) / n),
            "tp": round(sum(s["tp"] for s in leek_stats) / n),
            "mp": round(sum(s["mp"] for s in leek_stats) / n),
        },
        "str_distribution": {
            f"{k}-{k+49}": {"count": v["total"], "win_rate": round(100 * v["wins"] / v["total"], 1) if v["total"] else 0}
            for k, v in sorted(str_buckets.items())
            if v["total"] >= 5
        },
    }


# =============================================================================
# Output Functions
# =============================================================================

def _print_meta_analysis(results: dict) -> None:
    """Pretty print meta analysis results."""
    console.print(f"\n[bold cyan]═══ META ANALYSIS: {results['level_range']} ═══[/bold cyan]")
    console.print(f"Dataset: {results['total_fights']:,} fights | {results['total_leeks']:,} leeks\n")

    # First-mover
    fm = results["first_mover"]
    console.print("[bold]First-Mover Advantage[/bold]")
    console.print(f"  Attacker: {fm['attacker_wins']:4d} ({fm['attacker_rate']}%)")
    console.print(f"  Defender: {fm['defender_wins']:4d} ({fm['defender_rate']}%)")
    console.print(f"  Draws:    {fm['draws']:4d} ({fm['draw_rate']}%)\n")

    # By level
    console.print("[bold]Stats by Level[/bold]")
    console.print(f"{'Level':8} {'N':>6} {'STR':>6} {'AGI':>6} {'MAG':>6} {'WinR':>6}")
    console.print("-" * 45)
    for bucket, stats in results["by_level"].items():
        console.print(
            f"{bucket:8} {stats['count']:6d} {stats['avg_str']:6d} "
            f"{stats['avg_agi']:6d} {stats['avg_mag']:6d} {stats['win_rate']:5.1f}%"
        )

    # Archetypes
    console.print("\n[bold]Archetypes[/bold]")
    console.print(f"{'Type':10} {'N':>6} {'Wins':>6} {'WinR':>6}")
    console.print("-" * 32)
    for arch, stats in sorted(results["archetypes"].items(), key=lambda x: -x[1]["win_rate"]):
        console.print(f"{arch:10} {stats['count']:6d} {stats['wins']:6d} {stats['win_rate']:5.1f}%")


def _print_level_analysis(results: dict, level: int, level_range: int) -> None:
    """Pretty print level analysis results."""
    if "error" in results:
        console.print(f"[red]{results['error']}[/red]")
        return

    console.print(f"\n[bold cyan]═══ LEVEL ANALYSIS: {results['level_range']} ═══[/bold cyan]")
    console.print(f"Sample: {results['count']:,} leeks | Win rate: {results['win_rate']}%\n")

    console.print("[bold]Average Stats[/bold]")
    for stat, val in results["avg_stats"].items():
        console.print(f"  {stat.upper():4}: {val}")

    console.print("\n[bold]STR Distribution (win rate)[/bold]")
    for bucket, data in results["str_distribution"].items():
        bar = "█" * int(data["win_rate"] / 5)
        console.print(f"  {bucket:8} {data['count']:4d}  {bar:20} {data['win_rate']}%")


def _save_meta_analysis(results: dict, path: str) -> None:
    """Save meta analysis to markdown file."""
    lines = [
        f"# Meta Analysis: {results['level_range']}",
        "",
        f"**Dataset**: {results['total_fights']:,} fights, {results['total_leeks']:,} leeks",
        "",
        "## First-Mover Advantage",
        "",
        "| Team | Wins | Rate |",
        "|------|------|------|",
    ]

    fm = results["first_mover"]
    lines.append(f"| Attacker | {fm['attacker_wins']} | {fm['attacker_rate']}% |")
    lines.append(f"| Defender | {fm['defender_wins']} | {fm['defender_rate']}% |")
    lines.append(f"| Draw | {fm['draws']} | {fm['draw_rate']}% |")

    lines.extend([
        "",
        "## Stats by Level",
        "",
        "| Level | N | STR | AGI | MAG | Win% |",
        "|-------|---|-----|-----|-----|------|",
    ])
    for bucket, stats in results["by_level"].items():
        lines.append(
            f"| {bucket} | {stats['count']} | {stats['avg_str']} | "
            f"{stats['avg_agi']} | {stats['avg_mag']} | {stats['win_rate']}% |"
        )

    lines.extend([
        "",
        "## Archetypes",
        "",
        "| Type | Count | Win Rate |",
        "|------|-------|----------|",
    ])
    for arch, stats in sorted(results["archetypes"].items(), key=lambda x: -x[1]["win_rate"]):
        lines.append(f"| {arch} | {stats['count']} | {stats['win_rate']}% |")

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n")


# =============================================================================
# ALPHA STRIKE ANALYSIS (Elite Meta Metrics)
# =============================================================================

@analyze.command("alpha-strike")
@click.argument("fight_id", type=int, required=False)
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--sample", type=int, default=0, help="Analyze N random fights from DB")
@click.pass_context
def alpha_strike_analysis(ctx: click.Context, fight_id: int | None, db: str, sample: int) -> None:
    """Alpha Strike analysis - elite meta metrics.

    Analyzes: TP efficiency, opening buffs, high-win chips, PONR.

    Examples:
        leek analyze alpha-strike 51234567       # Single fight
        leek analyze alpha-strike --sample 100  # Random sample from DB
    """
    from leekwars_agent.fight_parser import parse_fight
    from leekwars_agent.fight_analyzer import analyze_alpha_strike, print_alpha_strike_analysis

    if fight_id:
        # Analyze single fight
        if not Path(db).exists():
            console.print(f"[red]Database not found: {db}[/red]")
            raise SystemExit(1)

        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT json_data FROM fights WHERE fight_id = ?", (fight_id,)
        ).fetchone()
        conn.close()

        if not row:
            console.print(f"[red]Fight {fight_id} not found in database[/red]")
            raise SystemExit(1)

        fight_data = json.loads(row[0])
        fight = fight_data.get("fight", fight_data)
        parsed = parse_fight(fight)
        summary = analyze_alpha_strike(parsed)

        if ctx.obj.get("json"):
            output_json(summary.summary_dict())
        else:
            print_alpha_strike_analysis(summary)

    elif sample > 0:
        # Analyze sample from DB
        if not Path(db).exists():
            console.print(f"[red]Database not found: {db}[/red]")
            raise SystemExit(1)

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT fight_id, json_data, winner FROM fights ORDER BY RANDOM() LIMIT ?",
            (sample,)
        ).fetchall()
        conn.close()

        if not rows:
            console.print("[red]No fights in database[/red]")
            raise SystemExit(1)

        # Aggregate stats
        results = _run_alpha_strike_sample(rows)

        if ctx.obj.get("json"):
            output_json(results)
        else:
            _print_alpha_strike_sample(results, sample)

    else:
        console.print("[yellow]Usage: leek analyze alpha-strike <fight_id>[/yellow]")
        console.print("       leek analyze alpha-strike --sample 100")


def _run_alpha_strike_sample(rows: list) -> dict:
    """Run Alpha Strike analysis on a sample of fights."""
    from leekwars_agent.fight_parser import parse_fight
    from leekwars_agent.fight_analyzer import analyze_alpha_strike

    tp_efficiencies = []
    opening_buff_gaps = []
    ponr_turns = []
    high_win_counts = []
    winners_by_opener = {"better_opener_wins": 0, "worse_opener_wins": 0, "equal": 0}

    for row in rows:
        fight_id, json_data, winner = row
        try:
            fight_data = json.loads(json_data)
            fight = fight_data.get("fight", fight_data)
            parsed = parse_fight(fight)
            summary = analyze_alpha_strike(parsed)

            # Collect stats
            if summary.team1_metrics:
                tp_efficiencies.append(summary.team1_metrics.overall_tp_efficiency)
            if summary.team2_metrics:
                tp_efficiencies.append(summary.team2_metrics.overall_tp_efficiency)

            opening_buff_gaps.append(abs(summary.opening_buff_delta))

            if summary.ponr_turn:
                ponr_turns.append(summary.ponr_turn)

            if summary.team1_metrics:
                high_win_counts.append(len(summary.team1_metrics.high_win_chips_used))
            if summary.team2_metrics:
                high_win_counts.append(len(summary.team2_metrics.high_win_chips_used))

            # Track opener advantage
            if winner == 1 and summary.opening_buff_delta > 0:
                winners_by_opener["better_opener_wins"] += 1
            elif winner == 2 and summary.opening_buff_delta < 0:
                winners_by_opener["better_opener_wins"] += 1
            elif winner == 1 and summary.opening_buff_delta < 0:
                winners_by_opener["worse_opener_wins"] += 1
            elif winner == 2 and summary.opening_buff_delta > 0:
                winners_by_opener["worse_opener_wins"] += 1
            else:
                winners_by_opener["equal"] += 1

        except Exception as e:
            continue  # Skip malformed fights

    n = len(rows)
    return {
        "sample_size": n,
        "avg_tp_efficiency": round(sum(tp_efficiencies) / len(tp_efficiencies), 3) if tp_efficiencies else 0,
        "tp_below_90": sum(1 for e in tp_efficiencies if e < 0.9),
        "avg_opening_buff_gap": round(sum(opening_buff_gaps) / len(opening_buff_gaps), 2) if opening_buff_gaps else 0,
        "avg_ponr_turn": round(sum(ponr_turns) / len(ponr_turns), 1) if ponr_turns else None,
        "ponr_before_turn_3": sum(1 for t in ponr_turns if t <= 3),
        "avg_high_win_chips": round(sum(high_win_counts) / len(high_win_counts), 2) if high_win_counts else 0,
        "opener_advantage": winners_by_opener,
    }


def _print_alpha_strike_sample(results: dict, n: int) -> None:
    """Pretty print Alpha Strike sample analysis."""
    console.print(f"\n[bold cyan]═══ ALPHA STRIKE SAMPLE ANALYSIS ({n} fights) ═══[/bold cyan]\n")

    console.print("[bold]TP Efficiency[/bold] (target: ≥0.9)")
    eff = results["avg_tp_efficiency"]
    status = "[green]✓[/green]" if eff >= 0.9 else "[yellow]⚠[/yellow]"
    console.print(f"  Average: {eff:.3f} {status}")
    console.print(f"  Below 0.9: {results['tp_below_90']} ({100*results['tp_below_90']/n/2:.1f}% of entities)")

    console.print("\n[bold]Opening Buff Gap[/bold]")
    console.print(f"  Average gap: {results['avg_opening_buff_gap']:.2f} buffs")
    oa = results["opener_advantage"]
    total_decided = oa["better_opener_wins"] + oa["worse_opener_wins"]
    if total_decided > 0:
        opener_rate = 100 * oa["better_opener_wins"] / total_decided
        console.print(f"  Better opener wins: {opener_rate:.1f}% of decided fights")

    console.print("\n[bold]Point of No Return (PONR)[/bold]")
    if results["avg_ponr_turn"]:
        console.print(f"  Average PONR turn: {results['avg_ponr_turn']:.1f}")
        console.print(f"  Decided by turn 3: {results['ponr_before_turn_3']} ({100*results['ponr_before_turn_3']/n:.1f}%)")
    else:
        console.print("  [dim]Not enough data[/dim]")

    console.print("\n[bold]High-Win Chips[/bold]")
    console.print(f"  Average per entity: {results['avg_high_win_chips']:.2f}/5")
