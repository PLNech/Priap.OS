"""Scraper commands - download fights for meta analysis."""

import click
from ..output import output_json, success, error, console
from leekwars_agent.auth import login_api
from leekwars_agent.scraper import FightDB, FightScraper


@click.group()
def scrape():
    """Scrape fights for meta analysis.

    Download fight data from LeekWars API for offline analysis.
    """
    pass


@scrape.command("run")
@click.option("--count", "-n", type=int, default=100, help="Target number of fights")
@click.option("--min-level", type=int, default=25, help="Minimum leek level")
@click.option("--max-level", type=int, default=100, help="Maximum leek level")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--tournaments", "-t", type=int, default=3, help="Tournaments to explore")
@click.option("--leek-id", type=int, default=131321, help="Bootstrap leek ID (default: IAdonis)")
@click.pass_context
def run_scraper(ctx: click.Context, count: int, min_level: int, max_level: int, db: str, tournaments: int, leek_id: int) -> None:
    """Run the fight scraper.

    Downloads fights from tournaments and player histories,
    filtering by level range.

    Examples:
        leek scrape run -n 500                    # Download 500 fights
        leek scrape run -n 1000 --min-level 30    # L30+ fights
        leek scrape run -t 20                     # Explore 20 tournaments
    """
    api = login_api()
    fight_db = FightDB(db)

    def progress(stats):
        console.print(
            f"  [cyan]{stats.fights_downloaded}[/cyan] downloaded, "
            f"[yellow]{stats.fights_queued}[/yellow] queued, "
            f"[dim]{stats.fights_skipped} skipped[/dim] "
            f"({stats.fights_per_minute:.1f}/min)",
            end="\r",
        )

    try:
        console.print(f"[bold]Fight Scraper[/bold] (L{min_level}-{max_level})")
        console.print(f"  Target: {count} fights")
        console.print(f"  Database: {db}")
        console.print()

        scraper = FightScraper(
            api=api,
            db=fight_db,
            min_level=min_level,
            max_level=max_level,
        )

        stats = scraper.scrape(
            target_count=count,
            bootstrap_leek_id=leek_id,
            discover_tournaments=tournaments,
            progress_callback=progress,
        )

        console.print()  # Clear progress line
        console.print()

        if ctx.obj.get("json"):
            output_json({
                "downloaded": stats.fights_downloaded,
                "skipped": stats.fights_skipped,
                "queued": stats.fights_queued,
                "errors": stats.errors,
                "rate_limits": stats.rate_limits,
                "runtime_seconds": stats.runtime_seconds,
            })
        else:
            success(f"Downloaded {stats.fights_downloaded} fights in {stats.runtime_seconds:.1f}s")
            if stats.errors > 0:
                console.print(f"  [yellow]Errors: {stats.errors}[/yellow]")
            if stats.rate_limits > 0:
                console.print(f"  [yellow]Rate limits hit: {stats.rate_limits}[/yellow]")

    finally:
        api.close()
        fight_db.close()


@scrape.command("status")
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.pass_context
def scrape_status(ctx: click.Context, db: str) -> None:
    """Show scraper database status."""
    fight_db = FightDB(db)

    try:
        stats = fight_db.get_stats_summary()
        levels = fight_db.get_level_distribution()

        if ctx.obj.get("json"):
            output_json({
                "stats": stats,
                "level_distribution": levels,
            })
            return

        console.print(f"[bold]Scraper Database[/bold]: {db}")
        console.print(f"  Fights: [green]{stats['fights']}[/green]")
        console.print(f"  Queue: [yellow]{stats['queue']}[/yellow]")
        console.print(f"  Observations: {stats['observations']}")

        if levels:
            console.print("\n[bold]Level Distribution:[/bold]")
            # Group into buckets
            buckets = {}
            for level, count in levels.items():
                bucket = f"{(level // 10) * 10}-{(level // 10) * 10 + 9}"
                buckets[bucket] = buckets.get(bucket, 0) + count

            for bucket, count in sorted(buckets.items()):
                bar = "█" * min(count // 10, 30)
                console.print(f"  L{bucket}: {bar} {count}")

    finally:
        fight_db.close()


@scrape.command("queue")
@click.argument("fight_ids", nargs=-1, type=int)
@click.option("--db", type=str, default="data/fights_meta.db", help="Database path")
@click.option("--source", "-s", type=str, default="manual", help="Source tag")
@click.option("--priority", "-p", type=int, default=100, help="Queue priority")
@click.pass_context
def queue_fights(ctx: click.Context, fight_ids: tuple, db: str, source: str, priority: int) -> None:
    """Manually queue fight IDs for download.

    Examples:
        leek scrape queue 51200838 51200839 51200840
        leek scrape queue 51200838 --priority 200
    """
    if not fight_ids:
        error("No fight IDs provided")
        raise SystemExit(1)

    fight_db = FightDB(db)

    try:
        queued = 0
        for fight_id in fight_ids:
            if not fight_db.has_fight(fight_id):
                fight_db.queue_fight(fight_id, source=source, priority=priority)
                queued += 1

        if ctx.obj.get("json"):
            output_json({"queued": queued, "total": len(fight_ids)})
        else:
            success(f"Queued {queued}/{len(fight_ids)} fights")

    finally:
        fight_db.close()
