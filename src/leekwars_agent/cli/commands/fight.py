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

            fight_resp = api.get_fight(fight_id)
            # API returns fight data directly OR nested in "fight" key
            fight_data = fight_resp.get("fight", fight_resp) if isinstance(fight_resp, dict) else fight_resp
            winner = fight_data.get("winner", 0)

            # Determine which team we're on (don't assume team 1!)
            my_team = 1
            for leek in fight_data.get("leeks2", []):
                if leek.get("id") == LEEK_ID:
                    my_team = 2
                    break

            if winner == 0:
                draws += 1
                status_str = "[yellow]D[/yellow]"
            elif winner == my_team:
                wins += 1
                status_str = "[green]W[/green]"
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
        data = api.get_leek_history(LEEK_ID)
        fights = data.get("fights", [])[:limit]

        if ctx.obj.get("json"):
            output_json(fights)
            return

        console.print(f"[bold]Recent Fights[/bold] (last {len(fights)})\n")

        for f in fights:
            winner = f.get("winner", 0)

            # Determine which team we're on
            my_team = 1
            for leek in f.get("leeks2", []):
                if leek.get("id") == LEEK_ID:
                    my_team = 2
                    break

            # Get opponent name
            if my_team == 1:
                opp = f.get("leeks2", [{}])[0] if f.get("leeks2") else {}
            else:
                opp = f.get("leeks1", [{}])[0] if f.get("leeks1") else {}
            opp_name = opp.get("name", "?")

            if winner == 0:
                status = "[yellow]D[/yellow]"
            elif winner == my_team:
                status = "[green]W[/green]"
            else:
                status = "[red]L[/red]"

            fight_id = f.get("id", "?")
            console.print(f"  {status} vs {opp_name:20} #{fight_id}")

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


@fight.command("analyze")
@click.option("--limit", "-n", type=int, default=40, help="Number of fights to analyze")
@click.pass_context
def analyze_fights(ctx: click.Context, limit: int) -> None:
    """Analyze recent fight history with win/loss breakdown.

    Shows overall stats, win rate by level difference, and fight duration patterns.
    """
    api = login_api()
    try:
        console.print(f"[bold]Analyzing last {limit} fights...[/bold]\n")

        # Get fight IDs from history
        data = api.get_leek_history(LEEK_ID)
        fight_ids = [f["id"] for f in data.get("fights", [])[:limit]]

        results = {"W": 0, "L": 0, "D": 0}
        by_level_diff = {}
        turn_counts = []

        for i, fid in enumerate(fight_ids):
            # Fetch full fight data
            resp = api._client.get(f"/fight/get/{fid}", headers=api._headers())
            if resp.status_code != 200:
                continue

            f = resp.json()
            winner = f.get("winner", 0)
            l1 = f.get("leeks1", [{}])[0] if f.get("leeks1") else {}
            l2 = f.get("leeks2", [{}])[0] if f.get("leeks2") else {}

            # Determine which team we're on
            my_team = 1 if l1.get("id") == LEEK_ID else 2
            my_leek = l1 if my_team == 1 else l2
            opp = l2 if my_team == 1 else l1

            my_level = my_leek.get("level", 0)
            opp_level = opp.get("level", 0)
            level_diff = my_level - opp_level

            # Get fight duration
            duration = f.get("data", {}).get("duration", 0) if f.get("data") else 0
            if duration:
                turn_counts.append(duration)

            # Determine result
            if winner == 0:
                result = "D"
            elif winner == my_team:
                result = "W"
            else:
                result = "L"
            results[result] += 1

            # Track by level diff
            key = f"{level_diff:+d}"
            if key not in by_level_diff:
                by_level_diff[key] = {"W": 0, "L": 0, "D": 0}
            by_level_diff[key][result] += 1

            # Progress indicator
            if (i + 1) % 10 == 0:
                console.print(f"  Processed {i + 1}/{len(fight_ids)}...")

            time.sleep(0.05)  # Light rate limit

        # Output results
        total = sum(results.values())
        win_rate = results["W"] / (results["W"] + results["L"]) * 100 if (results["W"] + results["L"]) > 0 else 0
        draw_rate = results["D"] / total * 100 if total > 0 else 0

        if ctx.obj.get("json"):
            output_json({
                "total": total,
                "wins": results["W"],
                "losses": results["L"],
                "draws": results["D"],
                "win_rate": win_rate,
                "draw_rate": draw_rate,
                "by_level_diff": by_level_diff,
                "avg_turns": sum(turn_counts) / len(turn_counts) if turn_counts else 0,
            })
            return

        console.print(f"\n[bold]Results: {results['W']}W-{results['L']}L-{results['D']}D[/bold]")
        console.print(f"  Win rate: [green]{win_rate:.1f}%[/green]")
        console.print(f"  Draw rate: [yellow]{draw_rate:.1f}%[/yellow]")

        if by_level_diff:
            console.print("\n[bold]By Level Difference:[/bold]")
            for diff in sorted(by_level_diff.keys(), key=lambda x: int(x)):
                d = by_level_diff[diff]
                diff_total = d["W"] + d["L"] + d["D"]
                diff_wr = d["W"] / (d["W"] + d["L"]) * 100 if (d["W"] + d["L"]) > 0 else 0
                console.print(f"  {diff}: {d['W']}W-{d['L']}L-{d['D']}D ({diff_wr:.0f}% WR)")

        if turn_counts:
            console.print("\n[bold]Fight Duration:[/bold]")
            console.print(f"  Average: {sum(turn_counts) / len(turn_counts):.1f} turns")
            console.print(f"  Short (<10): {len([t for t in turn_counts if t < 10])}")
            console.print(f"  Long (>30): {len([t for t in turn_counts if t >= 30])}")
            console.print(f"  Timeouts (64): {len([t for t in turn_counts if t >= 64])}")

    finally:
        api.close()
