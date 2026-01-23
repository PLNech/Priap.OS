"""Build commands - manage leek stats and capital."""

import json
import click
from ..output import output_json, success, error, console
from ..constants import LEEK_ID
from leekwars_agent.auth import login_api


@click.group()
def build():
    """Build management - view and spend capital on stats."""
    pass


@build.command("show")
@click.pass_context
def show_build(ctx: click.Context) -> None:
    """Show current leek build (stats allocation)."""
    api = login_api()
    try:
        data = api.get_leek(LEEK_ID)
        leek = data.get("leek", data)

        stats = {
            "strength": leek.get("strength", 0),
            "agility": leek.get("agility", 0),
            "frequency": leek.get("frequency", 100),
            "wisdom": leek.get("wisdom", 0),
            "resistance": leek.get("resistance", 0),
            "science": leek.get("science", 0),
            "magic": leek.get("magic", 0),
        }
        base = {
            "life": leek.get("life", 0),
            "tp": leek.get("tp", 10),
            "mp": leek.get("mp", 3),
        }
        capital = leek.get("capital", 0)
        level = leek.get("level", 1)

        if ctx.obj.get("json"):
            output_json({
                "stats": stats,
                "base": base,
                "capital": capital,
                "level": level,
            })
            return

        console.print(f"[bold]Build[/bold] (L{level}, {capital} capital unspent)\n")

        console.print("[cyan]Combat Stats[/cyan]")
        console.print(f"  STR: [bold]{stats['strength']:4d}[/bold]  (damage)")
        console.print(f"  AGI: [bold]{stats['agility']:4d}[/bold]  (dodge/crit)")
        console.print(f"  FRQ: [bold]{stats['frequency']:4d}[/bold]  (turn order)")

        console.print("\n[cyan]Support Stats[/cyan]")
        console.print(f"  WIS: [bold]{stats['wisdom']:4d}[/bold]  (chip power)")
        console.print(f"  RES: [bold]{stats['resistance']:4d}[/bold]  (damage reduction)")
        console.print(f"  SCI: [bold]{stats['science']:4d}[/bold]  (buff duration)")
        console.print(f"  MAG: [bold]{stats['magic']:4d}[/bold]  (chip effects)")

        console.print("\n[cyan]Base Stats[/cyan]")
        console.print(f"  HP:  [bold]{base['life']:4d}[/bold]")
        console.print(f"  TP:  [bold]{base['tp']:4d}[/bold]  (actions/turn)")
        console.print(f"  MP:  [bold]{base['mp']:4d}[/bold]  (movement/turn)")

        if capital > 0:
            console.print(f"\n[yellow]⚠ {capital} capital unspent![/yellow]")

    finally:
        api.close()


@build.command("spend")
@click.argument("stat", type=click.Choice([
    "strength", "str",
    "agility", "agi",
    "frequency", "frq",
    "wisdom", "wis",
    "resistance", "res",
    "science", "sci",
    "magic", "mag",
]))
@click.argument("points", type=int)
@click.option("--dry-run", is_flag=True, help="Show what would happen without spending")
@click.pass_context
def spend_capital(ctx: click.Context, stat: str, points: int, dry_run: bool) -> None:
    """Spend capital points on a stat.

    STAT is which stat to increase (strength/str, agility/agi, etc).
    POINTS is how many points to spend.

    Examples:
        leek build spend str 50      # Add 50 strength
        leek build spend agi 10      # Add 10 agility
        leek build spend str 76 --dry-run  # Preview spending all capital
    """
    # Normalize stat names
    stat_map = {
        "str": "strength", "strength": "strength",
        "agi": "agility", "agility": "agility",
        "frq": "frequency", "frequency": "frequency",
        "wis": "wisdom", "wisdom": "wisdom",
        "res": "resistance", "resistance": "resistance",
        "sci": "science", "science": "science",
        "mag": "magic", "magic": "magic",
    }
    stat_name = stat_map[stat]

    api = login_api()
    try:
        # Check available capital
        data = api.get_leek(LEEK_ID)
        leek = data.get("leek", data)
        available = leek.get("capital", 0)
        current = leek.get(stat_name, 0)

        if points > available:
            error(f"Not enough capital: need {points}, have {available}")
            raise SystemExit(1)

        if points <= 0:
            error("Points must be positive")
            raise SystemExit(1)

        if dry_run:
            console.print(f"[yellow]Would spend {points} capital on {stat_name}[/yellow]")
            console.print(f"  {stat_name}: {current} → {current + points}")
            console.print(f"  Capital: {available} → {available - points}")
            return

        # Spend via API
        # API expects: {"characteristics": json.dumps({stat: points})}
        result = api._client.post(
            "/leek/spend-capital",
            headers=api._headers(),
            data={"leek_id": LEEK_ID, "characteristics": json.dumps({stat_name: points})},
        )
        result.raise_for_status()

        success(f"Spent {points} capital on {stat_name}!")
        console.print(f"  {stat_name}: {current} → {current + points}")
        console.print(f"  Capital: {available} → {available - points}")

        if ctx.obj.get("json"):
            output_json({
                "stat": stat_name,
                "points": points,
                "new_value": current + points,
                "capital_remaining": available - points,
            })

    finally:
        api.close()


@build.command("recommend")
@click.pass_context
def recommend_build(ctx: click.Context) -> None:
    """Recommend how to spend unspent capital.

    Based on current build archetype (STR-focused, balanced, etc).
    """
    api = login_api()
    try:
        data = api.get_leek(LEEK_ID)
        leek = data.get("leek", data)

        capital = leek.get("capital", 0)
        strength = leek.get("strength", 0)
        agility = leek.get("agility", 0)

        if capital == 0:
            console.print("[green]No unspent capital - you're maxed out![/green]")
            return

        if ctx.obj.get("json"):
            # Determine archetype
            if strength > agility * 5:
                archetype = "str_glass_cannon"
                recommendation = {"strength": capital}
            elif agility > strength:
                archetype = "agi_dodge"
                recommendation = {"agility": capital}
            else:
                archetype = "balanced"
                recommendation = {"strength": capital}

            output_json({
                "capital": capital,
                "archetype": archetype,
                "recommendation": recommendation,
            })
            return

        console.print(f"[bold]Build Recommendation[/bold] ({capital} capital)\n")

        # Analyze current build
        if strength > agility * 5:
            console.print("[cyan]Archetype:[/cyan] STR Glass Cannon 🔥")
            console.print("  You're all-in on damage. Keep stacking STR!")
            console.print(f"\n[green]Recommendation:[/green] leek build spend str {capital}")
        elif agility > strength:
            console.print("[cyan]Archetype:[/cyan] AGI Dodge Tank")
            console.print("  You're built for survivability. Keep stacking AGI!")
            console.print(f"\n[green]Recommendation:[/green] leek build spend agi {capital}")
        else:
            console.print("[cyan]Archetype:[/cyan] Balanced")
            console.print("  For burst damage, STR is usually better.")
            console.print(f"\n[green]Recommendation:[/green] leek build spend str {capital}")

    finally:
        api.close()
