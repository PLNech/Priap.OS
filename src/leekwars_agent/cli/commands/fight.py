"""Fight commands - run fights and view status."""

import click
import time
from ..output import output_json, output_kv, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api


@click.group()
def fight():
    """Fight operations - run fights and view status."""
    pass


@fight.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show current fight status (fights remaining, talent, etc)."""
    api = login_api()
    try:
        garden = api.get_garden().get("garden", {})
        leek = api.get_leek(LEEK_ID).get("leek", {})

        data = {
            "fights_available": garden.get("fights", 0),
            "fights_max": garden.get("max_fights", 100),
            "leek_name": leek.get("name"),
            "leek_level": leek.get("level"),
            "talent": leek.get("talent"),
        }

        if ctx.obj.get("json"):
            output_json(data)
        else:
            console.print("[bold]Fight Status[/bold]")
            console.print(f"  Fights: [green]{data['fights_available']}[/green] / {data['fights_max']}")
            console.print(f"  Leek: {data['leek_name']} (L{data['leek_level']})")
            console.print(f"  Talent: {data['talent']}")
    finally:
        api.close()


@fight.command("run")
@click.option("--count", "-n", type=int, default=1, help="Number of fights to run")
@click.option("--dry-run", is_flag=True, help="Show what would happen without fighting")
@click.pass_context
def run(ctx: click.Context, count: int, dry_run: bool) -> None:
    """Run solo fights.

    Finds opponents and fights them. Results are printed as W/L/D.
    """
    api = login_api()
    try:
        garden = api.get_garden().get("garden", {})
        available = garden.get("fights", 0)

        if available < count:
            error(f"Only {available} fights available, requested {count}")
            raise SystemExit(1)

        if dry_run:
            success(f"Would run {count} fights (dry run)")
            if ctx.obj.get("json"):
                output_json({"dry_run": True, "count": count, "available": available})
            return

        wins, losses, draws = 0, 0, 0
        results = []

        for i in range(count):
            console.print(f"  [{i+1}/{count}] Finding opponent...", end=" ")

            opponents = api.get_leek_opponents(LEEK_ID).get("opponents", [])
            if not opponents:
                console.print("[yellow]No opponents[/yellow]")
                break

            target = opponents[0]
            result = api.start_solo_fight(LEEK_ID, target["id"])

            if "fight" not in result:
                console.print(f"[red]Failed: {result}[/red]")
                continue

            fight_id = result["fight"]
            time.sleep(3)  # Wait for fight to complete

            fight_data = api.get_fight(fight_id).get("fight", {})
            winner = fight_data.get("winner", 0)

            if winner == 1:  # We're always team 1 when attacking
                wins += 1
                status_str = "[green]W[/green]"
            elif winner == 0:
                draws += 1
                status_str = "[yellow]D[/yellow]"
            else:
                losses += 1
                status_str = "[red]L[/red]"

            console.print(f"{status_str} vs {target.get('name', '?')}")

            results.append({
                "fight_id": fight_id,
                "opponent": target.get("name"),
                "winner": winner,
                "result": "W" if winner == 1 else ("D" if winner == 0 else "L"),
            })

            time.sleep(0.5)  # Rate limit

        # Summary
        total = wins + losses + draws
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        if ctx.obj.get("json"):
            output_json({
                "fights": results,
                "summary": {
                    "total": total,
                    "wins": wins,
                    "losses": losses,
                    "draws": draws,
                    "win_rate": win_rate,
                }
            })
        else:
            console.print(f"\n[bold]Results:[/bold] {wins}W-{losses}L-{draws}D ({win_rate:.1f}% WR)")

    finally:
        api.close()


@fight.command("history")
@click.option("--limit", "-n", type=int, default=10, help="Number of fights to show")
@click.pass_context
def history(ctx: click.Context, limit: int) -> None:
    """Show recent fight history."""
    api = login_api()
    try:
        data = api.get_leek_history(LEEK_ID, page=0, count=limit)
        fights = data.get("fights", [])

        if ctx.obj.get("json"):
            output_json(fights)
            return

        console.print(f"[bold]Recent Fights[/bold] (last {len(fights)})\n")

        for f in fights:
            winner = f.get("winner", 0)
            if winner == 1:
                status = "[green]W[/green]"
            elif winner == 0:
                status = "[yellow]D[/yellow]"
            else:
                status = "[red]L[/red]"

            fight_id = f.get("id", "?")
            console.print(f"  {status} #{fight_id}")

    finally:
        api.close()
