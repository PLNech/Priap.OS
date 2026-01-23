"""Fight commands - run fights and view status."""

import json
import click
import time
from pathlib import Path
from ..output import output_json, output_kv, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api
from leekwars_agent.fight_parser import parse_fight


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
        garden_data = api.get_garden()
        garden = garden_data.get("garden", garden_data)
        leek_data = api.get_leek(LEEK_ID)
        leek = leek_data.get("leek", leek_data)

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


@fight.command("get")
@click.argument("fight_id", type=int)
@click.option("--save/--no-save", default=False, help="Save fight data to data/fights/")
@click.option("--analyze", is_flag=True, help="Show fight analysis")
@click.pass_context
def get_fight(ctx: click.Context, fight_id: int, save: bool, analyze: bool) -> None:
    """Fetch and display fight details by ID.

    Examples:
        leek fight get 50863105
        leek fight get 50863105 --save --analyze
    """
    api = login_api()
    try:
        fight_data = api.get_fight(fight_id)
        fight = fight_data.get("fight", fight_data)

        if save:
            output_dir = Path("data/fights")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"fight_{fight_id}.json"
            output_file.write_text(json.dumps(fight_data, indent=2))
            success(f"Saved to {output_file}")

        if ctx.obj.get("json"):
            output_json(fight_data)
            return

        # Basic display
        winner = fight.get("winner", 0)
        winner_str = "Team 1" if winner == 1 else ("Draw" if winner == 0 else "Team 2")

        console.print(f"[bold]Fight #{fight_id}[/bold]")
        console.print(f"  Winner: {winner_str}")

        # Show teams
        leeks = fight.get("leeks1", []) + fight.get("leeks2", [])
        if leeks:
            console.print(f"  Participants: {', '.join(l.get('name', '?') for l in leeks)}")

        if analyze:
            console.print("\n[bold]Analysis:[/bold]")
            parsed = parse_fight(fight_data)
            summary = parsed.get("summary", {})

            turns = summary.get("turns", 0)
            console.print(f"  Turns: {turns}")

            damage = summary.get("damage_dealt", {})
            for entity_id, dmg in damage.items():
                console.print(f"  Entity {entity_id}: {dmg} damage dealt")

            weapon_uses = summary.get("weapon_uses", 0)
            console.print(f"  Total weapon uses: {weapon_uses}")

    finally:
        api.close()
