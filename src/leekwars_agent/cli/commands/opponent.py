"""Opponent database commands - track rematches and hard opponents."""

import click
from ..output import output_json, success, error, console
from leekwars_agent.scraper import FightDB


@click.group()
def opponent():
    """Opponent database - track rematches and identify hard opponents.

    Query our fight history to see how we perform against specific opponents.

    Examples:
        leek opponent stats "DarkVador"     # Stats vs a specific opponent
        leek opponent hardest               # Top 10 hardest opponents
        leek opponent recurring             # Opponents we've faced 3+ times
        leek opponent populate              # Populate DB from fight history
    """
    pass


@opponent.command("stats")
@click.argument("name", nargs=-1)
@click.option("--leek-id", type=int, default=None, help="Look up by leek ID instead of name")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def opponent_stats(ctx: click.Context, name: tuple, leek_id: int | None, db: str) -> None:
    """Show stats against a specific opponent (by name or ID).

    Examples:
        leek opponent stats DarkVador
        leek opponent stats "Super Leek"
        leek opponent stats --leek-id 12345
    """
    fight_db = FightDB(db)

    try:
        if leek_id:
            opp = fight_db.get_opponent(leek_id)
        elif name:
            opp = fight_db.get_opponent_by_name(" ".join(name))
        else:
            error("Provide a name or --leek-id")
            raise SystemExit(1)

        if not opp:
            if leek_id:
                error(f"No record for leek ID {leek_id}")
            else:
                error(f"No opponent found matching: {' '.join(name)}")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json(opp)
            return

        # Display formatted output
        console.print(f"\n[bold]Opponent: {opp['leek_name']}[/bold] (ID: {opp['leek_id']})")

        if opp.get("farmer_name"):
            console.print(f"  Farmer: [cyan]{opp['farmer_name']}[/cyan]")

        console.print(f"\n  [bold]Record:[/bold] {opp['wins']}W - {opp['losses']}L - {opp['draws']}D")
        wr = opp['win_rate'] * 100
        if wr >= 60:
            wr_color = "green"
        elif wr >= 40:
            wr_color = "yellow"
        else:
            wr_color = "red"
        console.print(f"  Win Rate: [{wr_color}]{wr:.1f}%[/]")

        console.print(f"  Fights: {opp['total_fights']}")
        console.print(f"  Avg Duration: {opp['avg_duration']:.1f} turns")

        if opp.get("archetype"):
            console.print(f"  Archetype: [magenta]{opp['archetype']}[/magenta]")

        if opp.get("level_last_seen"):
            console.print(f"  Last Seen: L{opp['level_last_seen']}, Talent {opp['talent_last_seen']}")

        # Common equipment
        chips = opp.get("common_chips", [])
        weapons = opp.get("common_weapons", [])
        if chips or weapons:
            console.print("\n[bold]Common Equipment:[/bold]")
            if chips:
                console.print(f"  Chips: {', '.join(str(c) for c in chips[:5])}")
            if weapons:
                console.print(f"  Weapons: {', '.join(str(w) for w in weapons[:3])}")

        # Hardness assessment
        if opp['total_fights'] >= 3:
            if wr < 40:
                console.print(f"\n  [green]✓ This opponent is BEATABLE[/green]")
            elif wr > 60:
                console.print(f"\n  [red]✗ This opponent is DANGEROUS[/red]")

    finally:
        fight_db.close()


@opponent.command("hardest")
@click.option("--min-fights", type=int, default=3, help="Minimum fights to be considered")
@click.option("--top", type=int, default=10, help="Show top N hardest opponents")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def hardest_opponents(ctx: click.Context, min_fights: int, top: int, db: str) -> None:
    """Show hardest opponents (lowest win rate).

    Examples:
        leek opponent hardest              # Top 10 hardest
        leek opponent hardest --min-fights 5  # Only opponents with 5+ fights
    """
    fight_db = FightDB(db)

    try:
        opponents = fight_db.get_opponents_by_win_rate(
            min_fights=min_fights,
            ascending=True,  # Lowest win rate first
        )[:top]

        if not opponents:
            error(f"No opponents with {min_fights}+ fights found")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json({"opponents": opponents})
            return

        console.print(f"\n[bold]Top {len(opponents)} Hardest Opponents[/bold]")
        console.print(f"  (min {min_fights} encounters, sorted by win rate)\n")

        for i, opp in enumerate(opponents, 1):
            wr = opp['win_rate'] * 100
            if wr < 40:
                wr_color = "red"
            elif wr < 50:
                wr_color = "yellow"
            else:
                wr_color = "green"

            arch = f" [{opp.get('archetype', '?')}]" if opp.get("archetype") else ""
            console.print(
                f"  {i:2}. [cyan]{opp['leek_name']}[/cyan]{arch}\n"
                f"      {opp['wins']}W-{opp['losses']}L ({wr:.0f}% WR), {opp['total_fights']} fights"
            )

        console.print()

    finally:
        fight_db.close()


@opponent.command("easiest")
@click.option("--min-fights", type=int, default=3, help="Minimum fights to be considered")
@click.option("--top", type=int, default=10, help="Show top N easiest opponents")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def easiest_opponents(ctx: click.Context, min_fights: int, top: int, db: str) -> None:
    """Show easiest opponents (highest win rate).

    Examples:
        leek opponent easiest              # Top 10 easiest
        leek opponent easiest --min-fights 5
    """
    fight_db = FightDB(db)

    try:
        opponents = fight_db.get_opponents_by_win_rate(
            min_fights=min_fights,
            ascending=False,  # Highest win rate first
        )[:top]

        if not opponents:
            error(f"No opponents with {min_fights}+ fights found")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json({"opponents": opponents})
            return

        console.print(f"\n[bold]Top {len(opponents)} Easiest Opponents[/bold]")
        console.print(f"  (min {min_fights} encounters, sorted by win rate)\n")

        for i, opp in enumerate(opponents, 1):
            wr = opp['win_rate'] * 100
            if wr >= 70:
                wr_color = "green"
            elif wr >= 60:
                wr_color = "cyan"
            else:
                wr_color = "yellow"

            arch = f" [{opp.get('archetype', '?')}]" if opp.get("archetype") else ""
            console.print(
                f"  {i:2}. [cyan]{opp['leek_name']}[/cyan]{arch}\n"
                f"      {opp['wins']}W-{opp['losses']}L ({wr:.0f}% WR), {opp['total_fights']} fights"
            )

        console.print()

    finally:
        fight_db.close()


@opponent.command("recurring")
@click.option("--min-encounters", type=int, default=3, help="Minimum encounters to show")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def recurring_opponents(ctx: click.Context, min_encounters: int, db: str) -> None:
    """Show opponents we've faced multiple times.

    Examples:
        leek opponent recurring              # All with 3+ encounters
        leek opponent recurring --min-encounters 5
    """
    fight_db = FightDB(db)

    try:
        opponents = fight_db.get_recurring_opponents(min_encounters=min_encounters)

        if not opponents:
            error(f"No opponents with {min_encounters}+ encounters")
            raise SystemExit(1)

        if ctx.obj.get("json"):
            output_json({"opponents": opponents})
            return

        console.print(f"\n[bold]Recurring Opponents[/bold] ({len(opponents)} with {min_encounters}+ encounters)\n")

        for opp in opponents:
            wr = opp['win_rate'] * 100
            arch = f" [{opp.get('archetype', '?')}]" if opp.get("archetype") else ""
            console.print(
                f"  [cyan]{opp['leek_name']}[/cyan]{arch}\n"
                f"      {opp['total_fights']} fights: {opp['wins']}W-{opp['losses']}L ({wr:.0f}% WR)"
            )
            if opp.get("last_seen"):
                from datetime import datetime
                last_date = datetime.utcfromtimestamp(opp['last_seen']).strftime('%Y-%m-%d')
                console.print(f"      Last seen: {last_date}")
            console.print()

    finally:
        fight_db.close()


@opponent.command("archetype")
@click.argument("archetype", type=click.Choice(["rusher", "kiter", "tank", "balanced"]))
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def opponents_by_archetype(ctx: click.Context, archetype: str, db: str) -> None:
    """List opponents by inferred archetype.

    Archetypes are inferred from fight patterns:
    - rusher: High TP, low MP, short fights
    - kiter: High MP, high AGI
    - tank: High frequency, high TP
    - balanced: Middle of everything

    Examples:
        leek opponent archetype kiter
        leek opponent archetype rusher
    """
    fight_db = FightDB(db)

    try:
        conn = fight_db._get_conn()
        opponents = conn.execute(
            "SELECT * FROM opponents WHERE archetype = ? ORDER BY win_rate DESC",
            (archetype,)
        ).fetchall()

        if not opponents:
            console.print(f"  No opponents with archetype '{archetype}'")
            return

        if ctx.obj.get("json"):
            output_json({"archetype": archetype, "opponents": [dict(o) for o in opponents]})
            return

        console.print(f"\n[bold]Opponents: {archetype.upper()}[/bold] ({len(opponents)})\n")

        for opp in opponents:
            wr = opp['win_rate'] * 100
            console.print(
                f"  [cyan]{opp['leek_name']}[/cyan]\n"
                f"      {opp['wins']}W-{opp['losses']}L ({wr:.0f}% WR), {opp['total_fights']} fights"
            )

        console.print()

    finally:
        fight_db.close()


@opponent.command("populate")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--our-leek-id", type=int, default=131321, help="Our leek ID (IAdonis)")
@click.option("--infer-archetype/--no-infer-archetype", default=True, help="Infer archetypes after populating")
@click.pass_context
def populate_opponents(ctx: click.Context, db: str, our_leek_id: int, infer_archetype: bool) -> None:
    """Populate opponent database from fight history.

    Scans all existing fights and builds opponent records.

    Examples:
        leek opponent populate                     # Use default leek ID (131321)
        leek opponent populate --our-leek-id 99999
        leek opponent populate --no-infer-archetype
    """
    fight_db = FightDB(db)

    try:
        console.print(f"[bold]Populating Opponent Database[/bold]")
        console.print(f"  Database: {db}")
        console.print(f"  Our Leek ID: {our_leek_id}")
        console.print()

        # Check existing opponent count
        before_count = fight_db.get_opponent_count()
        console.print(f"  Existing opponents: {before_count}")

        # Populate from history
        updated = fight_db.populate_opponents_from_history(our_leek_id)
        console.print(f"  Updated from history: {updated}")

        if infer_archetype:
            console.print("\n  Inferring archetypes...")
            arch_updated = fight_db.update_archetypes_batch()
            console.print(f"    Updated: {arch_updated}")

        after_count = fight_db.get_opponent_count()
        console.print(f"\n  Total opponents now: {after_count}")

        if ctx.obj.get("json"):
            output_json({
                "before_count": before_count,
                "updated_from_history": updated,
                "archetypes_updated": arch_updated if infer_archetype else 0,
                "after_count": after_count,
            })
        else:
            success(f"Populated {after_count - before_count} new opponents")

    finally:
        fight_db.close()


@opponent.command("infer")
@click.option("--limit", type=int, default=100, help="Max opponents to process")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def infer_archetypes(ctx: click.Context, limit: int, db: str) -> None:
    """Infer archetypes for opponents that don't have one.

    Runs pattern analysis on fight history to classify opponents.

    Examples:
        leek opponent infer                    # Process up to 100
        leek opponent infer --limit 50
    """
    fight_db = FightDB(db)

    try:
        console.print(f"[bold]Inferring Opponent Archetypes[/bold]")
        console.print(f"  Processing up to {limit} opponents...")

        updated = fight_db.update_archetypes_batch(limit=limit)
        console.print(f"  Updated: {updated} opponents")

        if ctx.obj.get("json"):
            output_json({"archetypes_updated": updated})

    finally:
        fight_db.close()


@opponent.command("status")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def opponent_status(ctx: click.Context, db: str) -> None:
    """Show opponent database status."""
    fight_db = FightDB(db)

    try:
        count = fight_db.get_opponent_count()

        # Get archetype breakdown
        conn = fight_db._get_conn()
        archetypes = conn.execute(
            "SELECT archetype, COUNT(*) as count FROM opponents GROUP BY archetype"
        ).fetchall()

        if ctx.obj.get("json"):
            output_json({
                "total_opponents": count,
                "archetype_breakdown": {a["archetype"] or "unknown": a["count"] for a in archetypes},
            })
            return

        console.print(f"[bold]Opponent Database[/bold]: {db}")
        console.print(f"  Total opponents: [green]{count}[/green]")

        if archetypes:
            console.print("\n[bold]Archetype Breakdown:[/bold]")
            for arch in archetypes:
                arch_name = arch["archetype"] or "unknown"
                console.print(f"  {arch_name}: {arch['count']}")

    finally:
        fight_db.close()